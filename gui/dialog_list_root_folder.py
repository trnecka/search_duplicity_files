import os
import tkinter as tk
from tkinter.filedialog import askdirectory
import tkinter.font as tkfont
from tkinter import messagebox

from core import db
from core.sdfcore import db_session, save_files


class DialogListRootFolders(tk.Toplevel):
    """
    The dialog window for the list mapped folders (called root folders)
    """
    def __init__(self, parent) -> None:
        """
        Extend class tkinter.Toplevel
        :param parent:
        """
        super().__init__(parent)
        self.title("List root folders")
        self.font = tkfont.Font()
        self.width = 300
        self.parent = parent

        self.frame_buttons = tk.Frame(self)
        self.frame_buttons.pack()

        self.button_add = tk.Button(self.frame_buttons)
        self.button_add["text"] = "Add"
        self.button_add["pady"] = 10
        self.button_add["width"] = 10
        self.button_add["command"] = lambda: self.add_directory()
        self.button_add.grid(row=0, column=0, padx=10, pady=10)

        self.button_delete = tk.Button(self.frame_buttons)
        self.button_delete["text"] = "Delete"
        self.button_delete["pady"] = 10
        self.button_delete["width"] = 10
        self.button_delete["command"] = lambda: self.delete_directory()
        self.button_delete.grid(row=0, column=1, padx=10, pady=10)

        self.button_cancel = tk.Button(self.frame_buttons)
        self.button_cancel["text"] = "Restore list files"
        self.button_cancel["pady"] = 10
        self.button_cancel["width"] = 10
        self.button_cancel["command"] = self.restore_list_files
        self.button_cancel.grid(row=0, column=2, padx=10, pady=10)

        self.label_list_root_folders = tk.Label(self)
        self.label_list_root_folders["text"] = "List root folders:"
        self.label_list_root_folders.pack(anchor="w", padx=5)

        self.frame_list_root_folders = tk.Frame(self)
        self.frame_list_root_folders.grid_rowconfigure(0, weight=1)
        self.frame_list_root_folders.grid_columnconfigure(0, weight=1)
        self.frame_list_root_folders.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

        # data for listbox root folders
        root_folders_data = db_session.query(db.RootFolder).all()

        # adding listbox for root folder
        self.listbox_root_folders = tk.Listbox(self.frame_list_root_folders)

        # primary keys for the root folders
        self.root_folders_pk = dict()

        # inserting data to root folder listbox
        index = 0
        for rfd in root_folders_data:
            self.listbox_root_folders.insert(
                tk.END,
                rfd.name
            )
            self.root_folders_pk[index] = rfd.id
            index += 1
        self.listbox_root_folders.grid(row=0, column=0, sticky=tk.NSEW)

        # creating vertical scrollbar
        self.scrollbar_list_folders_vertical = tk.Scrollbar(
            self.frame_list_root_folders,
            orient=tk.VERTICAL,
            command=self.listbox_root_folders.yview
        )
        self.scrollbar_list_folders_vertical.grid(row=0, column=1, sticky=tk.NS)

        # creating horizontal scrollbar
        self.scrollbar_list_folders_horizontal = tk.Scrollbar(
            self.frame_list_root_folders,
            orient=tk.HORIZONTAL,
            command=self.listbox_root_folders.xview
        )
        self.scrollbar_list_folders_horizontal.grid(row=1, column=0, sticky=tk.EW)

        # adding scrollbars to root folders (listbox)
        self.listbox_root_folders.configure(
            yscrollcommand=self.scrollbar_list_folders_vertical.set,
            xscrollcommand=self.scrollbar_list_folders_horizontal.set
        )

    def add_directory(self) -> None:
        """
        The path from the askdirectory form will add to the database
        and root folders listbox after the check existence folder.

        :return: None
        """
        folder_path = askdirectory(initialdir=os.getcwd(), parent=self)
        if folder_path != '':
            list_all_paths = db_session.query(db.RootFolder).all()
            folder_exist = False
            for lap in list_all_paths:
                if folder_path == lap.path:
                    # info about the existence of the folder (messagebox) and do not add new folder
                    messagebox.showinfo(
                        "Add a new root folder",
                        f"The folder\n{folder_path}\nalready exists and it will not add to the list root folders."
                    )
                    folder_exist = True
                    break
                elif lap.path in folder_path:
                    # info about the existence of the parent folder (messagebox) and do not add new folder
                    messagebox.showinfo(
                        "Add a new root folder",
                        f"The folder\n{folder_path}\nalready exists in the parent folder and it will not add to the list root folder."
                    )
                    folder_exist = True
                    break
                elif folder_path in lap.path:
                    # add new folder if the user confirms it and to delete the child folder
                    insert_folder = messagebox.askyesno(
                        "Add a new root folder",
                        f"This folder has the sub folder in root folders.\n"
                        f"Do you want to delete all sub folders and insert your root folder?"
                    )
                    if insert_folder:
                        origin_folders = db_session.query(db.RootFolder).filter(db.RootFolder.path.like(folder_path+"%")).all()
                        for of in origin_folders:
                            origin_folder = db_session.query(db.RootFolder).filter(db.RootFolder.path == of.path).one()
                            db_session.delete(origin_folder)
                            db_session.commit()

                        # refresh listbox for list root folders
                        # delete listbox data
                        self.listbox_root_folders.delete(0, tk.END)
                        # get data for listbox from database
                        list_root_folders = db_session.query(db.RootFolder).all()
                        # delete primary keys for listbox
                        self.root_folders_pk = dict()
                        # generate new listbox for root folders and primary keys
                        index = 0
                        for lrf in list_root_folders:
                            self.listbox_root_folders.insert(
                                index,
                                lrf.name
                            )
                            self.root_folders_pk[index] = lrf.id
                            index += 1

                        folder_exist = False
                    else:
                        folder_exist = True
                    break
                else:
                    folder_exist = False

            # adding a new root folder if not exists
            if not folder_exist:
                db_session.add(db.RootFolder(
                    name=folder_path,
                    path=folder_path
                ))
                db_session.commit()
                self.listbox_root_folders.insert(tk.END, folder_path)

                # update primary keys for listbox
                self.root_folders_pk_update()

    def delete_directory(self) -> None:
        """
        Delete directory from the list box folders

        :return: None
        """
        if listbox_item := self.listbox_root_folders.curselection():
            listbox_index = listbox_item[0]
            self.listbox_root_folders.delete(listbox_index)
            pk = self.root_folders_pk.get(listbox_index)

            # delete item from database
            item = db_session.query(db.RootFolder).filter(db.RootFolder.id == pk).one()
            db_session.delete(item)
            db_session.commit()

            # delete item from listbox
            self.root_folders_pk.pop(listbox_index)

            # update primary keys for listbox
            self.root_folders_pk_update()

    def root_folders_pk_update(self) -> None:
        """
        Update attribute root_folders_pk.

        :return: None
        """
        # data for listbox root folders
        root_folders_data = db_session.query(db.RootFolder).all()

        # restart primary keys for the root folders
        self.root_folders_pk = dict()

        # inserting data to root_folders_pk attribute
        index = 0
        for rfd in root_folders_data:
            self.root_folders_pk[index] = rfd.id
            index += 1

    def restore_list_files(self) -> None:
        """
        Restoring searched files.

        :return: None
        """
        list_folders = db_session.query(db.RootFolder).all()
        for lf in list_folders:
            save_files(db_session, lf.path)
        self.parent.update_list_duplicate_files()
        self.destroy()
