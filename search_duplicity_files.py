import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from tkinter.filedialog import askdirectory
from tkinter import messagebox
from hashlib import md5

from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import and_

import db
import typing as t


def load_files(root_folder: str) -> t.Tuple[str, t.List[str]]:
    """
    Loading list all files in root folder and subfolders.

    :param root_folder: Relative path to the folder.
    :return: Tuple where is first value root folder and second value is the list of the all files with absolute path.
    """
    list_files = list()
    for (path, _, files) in os.walk(root_folder):
        for file_name in files:
            list_files.append(os.path.abspath((os.path.join(path, file_name))))
    return os.path.abspath(root_folder), list_files


def get_hash(path_file: str) -> str:
    """
    Getting hash from file

    :param path_file: Full path to the file.
    :return: Hash from the file
    """
    if os.path.exists(path_file):
        with open(path_file, "rb") as file:
            hash_file = md5(file.read()).hexdigest()
    else:
        hash_file = None
    return hash_file


def get_parent_file_id(session: Session, file: str) -> int:
    """
    The function returns id of this file.

    :param session: The function create_session() from the file db.py
    :param file: Full path to the file.
    :return: Id of the existing hash file, if it does not exist, it will be returned 0.
    """
    existing_hash = session.query(db.File).filter(
        db.File.filehash == get_hash(file) and db.File.parent_file_id == 0
    ).first()
    if existing_hash:
        return existing_hash.id
    else:
        return 0


def file_exists(session: Session, file: str) -> bool:
    """
    Check if the file exists in database. File has to have the same hash and filename.

    :param session: The function create_session() from the file db.py
    :param file: Full path to the file.
    :return: It returns True or False
    """
    return bool(session.query(db.File).filter(
        and_(db.File.filename == file, db.File.filehash == get_hash(file))
    ).first())


def is_file_changed(session: Session, file: str) -> bool:
    """
    The function check if the file is the same as the file saved in the database.
    The file has the same path (like in the database) but it has different content.

    :param session: The function create_session() from the file db.py
    :param file: Full path to the file.
    :return: True if the file is different in the database else False.
    """
    input_file_hash = get_hash(file)
    database_file = session.query(db.File).filter(
        db.File.filename == file
    ).first()
    if database_file is not None:
        if input_file_hash != database_file.filehash:
            return True
    return False


def save_files(session: Session, root_folder: str) -> None:
    """
    Saving files to the database if the files do not exist in the database.
    Saving the root folder to the database if it does not exist.

    :param session: The function create_session() from the file db.py
    :param root_folder: Full path to the root folder.
    """
    saved_root_folder = session.query(db.RootFolder).filter(db.RootFolder.path == root_folder).first()
    if saved_root_folder is None:
        session.add(
            db.RootFolder(
                name=root_folder,
                path=root_folder
            )
        )
        session.commit()
        saved_root_folder = session.query(db.RootFolder).filter(db.RootFolder.path == root_folder).first()

    root_folder, files = load_files(root_folder)
    for file in files:
        if not file_exists(session, file):
            session.add(
                db.File(
                    filehash=get_hash(file),
                    filename=file,
                    parent_file_id=get_parent_file_id(session, file),
                    root_folder_id=saved_root_folder.id
                )
            )
            session.commit()


def check_changed_files(session: Session) -> t.List[str]:
    """
    The function checks if the files exist in the database and the file exists on the disk.
    The deleted files are detected as changed files.

    :param session: The function create_session() from the file db.py
    :return: List of the changed files
    """
    # load all files from the database
    files = session.query(db.File).all()
    changed_files = list()
    for file in files:
        if not get_hash(file.filename) == file.filehash:
            changed_files.append(file.filename)

    return changed_files


def save_changed_files(session: Session, list_files: t.List[str]) -> None:
    """
    Save changed files in filesystem. They are the deleted files and changed files.
    These changes are detected of the function check_changed_files()

    :param session: The function create_session() from the file db.py
    :param list_files: The list of the changed files.
    """
    for file in list_files:
        file_from_db = session.query(db.File).filter(db.File.filename == file).one()
        if not os.path.exists(file_from_db.filename):
            session.delete(file_from_db)
        else:
            session.query(db.File).filter(db.File.filename == file).update({'filehash': get_hash(file)})
        session.commit()


def load_duplicate_files(session: Session) -> t.List[t.Dict[db.File, t.List[db.File]]]:
    """
    Loading duplicate files. It finds original file and their copies.
    It returns only files which has some duplicate.

    :param session: The function create_session() from the file db.py
    :return: List of the dictionaries. Dicticrionary contents key 'file_original' and 'file_copy'.
    """
    db_file_id = session.query(db.File.parent_file_id).filter(db.File.parent_file_id > 0).\
        group_by(db.File.parent_file_id).all()
    original_file_id = [ld[0] for ld in db_file_id]
    duplicate_files = list()
    for ofi in original_file_id:
        files = {
            'file_original': session.query(db.File).filter(db.File.id == ofi).first(),
            'file_copy': session.query(db.File).filter(db.File.parent_file_id == ofi).all()
        }
        duplicate_files.append(files)
    return duplicate_files


def get_duplicates_for_file(session: Session, file: str) -> t.List[db.File]:
    """
    Function gets all duplicates by full path to file

    :param session: The function create_session() from the file db.py
    :param file: Full path to the file.
    :return: List of the object File sorted by 'parent_file_id'. If the file does not exist, this function returns empty list.
    """
    if not os.path.exists(file):
        return []

    hash_file = get_hash(file)
    duplicates = session.query(db.File).filter(db.File.filehash == hash_file).order_by(db.File.parent_file_id).all()
    return duplicates


def search_duplicity_files():
    engine = db.load_engine()
    db.create_db_structure(engine)
    session = db.create_session(engine)
    root_folder, files = load_files("tests/test_files")
    # print the list of the changed files
    print(save_files(session, files, root_folder))
    print(f"Root folder: {root_folder}")

    # write all duplicate name of the files with their original (first record in the database)
    # example output
    for df in load_duplicate_files(session):
        print(df.get('file_original').filename)
        for f in df.get('file_copy'):
            print(f"\t{f.filename}")

    # write all duplicate files of one concrete file
    # example output
    print(f'Duplicates for file "{os.path.abspath("tests/test_files/pes-seznamka-1.jpg")}"')
    for gdff in get_duplicates_for_file(session, os.path.abspath("tests/test_files/pes-seznamka-1.jpg")):
        print(gdff.filename)


class DialogListChangedFiles(tk.Toplevel):
    """
    The dialog window for the list changed files.
    """
    def __init__(self, parent) -> None:
        """
        Extend class tkinter.Toplevel
        :param parent:
        """
        super().__init__(parent)
        self.title("List changed files")
        self.parent = parent
        self.list_changed_files = check_changed_files(db_session)

        # frame buttons
        self.frame_buttons = tk.Frame(self)
        self.frame_buttons.pack()

        # buttons
        self.button_add_changed_files = tk.Button(self.frame_buttons)
        self.button_add_changed_files["text"] = "Add changed files"
        self.button_add_changed_files["padx"] = 10
        self.button_add_changed_files["pady"] = 10
        self.button_add_changed_files["command"] = lambda: self.add_changed_files()
        self.button_add_changed_files.grid(row=0, column=0, padx=10, pady=10)

        self.button_cancel = tk.Button(self.frame_buttons)
        self.button_cancel["text"] = "Cancel"
        self.button_cancel["padx"] = 10
        self.button_cancel["pady"] = 10
        self.button_cancel["command"] = self.destroy
        self.button_cancel.grid(row=0, column=1, padx=10, pady=10)

        # frame listbox
        self.frame_list_changed_files = tk.Frame(self)
        self.frame_list_changed_files.pack()

        # label for the list changed files
        self.label_list_changed_files = tk.Label(self)
        self.label_list_changed_files["text"] = "List changed files:"
        self.label_list_changed_files.pack(anchor="w", padx=5)

        # frame for the list changed files
        self.frame_list_changed_files = tk.Frame(self)
        self.frame_list_changed_files.grid_rowconfigure(0, weight=1)
        self.frame_list_changed_files.grid_columnconfigure(0, weight=1)
        self.frame_list_changed_files.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

        # listbox for the list changed files
        self.listbox_list_changed_files = tk.Listbox(self.frame_list_changed_files)
        for file in self.list_changed_files:
            self.listbox_list_changed_files.insert(
                tk.END,
                file
            )
        self.listbox_list_changed_files.grid(row=0, column=0, sticky=tk.NSEW)

        # creating vertical scrollbar
        self.scrollbar_list_changed_files_vertical = tk.Scrollbar(
            self.frame_list_changed_files,
            orient=tk.VERTICAL,
            command=self.listbox_list_changed_files.yview
        )
        self.scrollbar_list_changed_files_vertical.grid(row=0, column=1, sticky=tk.NS)

        # creating horizontal scrollbar
        self.scrollbar_list_changed_files_horizontal = tk.Scrollbar(
            self.frame_list_changed_files,
            orient=tk.HORIZONTAL,
            command=self.listbox_list_changed_files.xview
        )
        self.scrollbar_list_changed_files_horizontal.grid(row=1, column=0, sticky=tk.EW)

        # adding scrollbars to list changed files (listbox)
        self.listbox_list_changed_files.configure(
            yscrollcommand=self.scrollbar_list_changed_files_vertical.set,
            xscrollcommand=self.scrollbar_list_changed_files_horizontal.set
        )

    def add_changed_files(self) -> None:
        list_changed_file = check_changed_files(db_session)
        save_changed_files(db_session, list_changed_file)
        self.parent.update_list_duplicate_files()
        self.destroy()


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


class SearchDuplicityFilesGUI(tk.Tk):
    """
    Main window of the application
    """
    def __init__(self) -> None:
        """
        Extend class tkinter.Tk
        """
        super().__init__()
        self.title("Search duplicity files")
        self.font = tkfont.Font()
        self.width = 700

        # creating buttons frame
        self.frame_buttons = tk.Frame(self)
        self.frame_buttons.pack(side=tk.TOP)

        # creating buttons
        self.button_search_duplicity = tk.Button(self.frame_buttons)
        self.button_search_duplicity["text"] = "Search duplicity files"
        self.button_search_duplicity["width"] = 17
        self.button_search_duplicity["pady"] = 10
        self.button_search_duplicity["command"] = lambda: self.update_list_duplicate_files()
        self.button_search_duplicity.grid(row=0, column=0, padx=10, pady=10)

        self.button_root_folder = tk.Button(self.frame_buttons)
        self.button_root_folder["text"] = "Root folders"
        self.button_root_folder["width"] = 17
        self.button_root_folder["pady"] = 10
        self.button_root_folder["command"] = lambda: self.dialog_root_folder_show()
        self.button_root_folder.grid(row=0, column=1, padx=10, pady=10)

        self.button_changed_files = tk.Button(self.frame_buttons)
        self.button_changed_files["text"] = "Changed files"
        self.button_changed_files["width"] = 17
        self.button_changed_files["pady"] = 10
        self.button_changed_files["command"] = lambda: self.dialog_changed_files_show()
        self.button_changed_files.grid(row=0, column=2, padx=10, pady=10)

        self.button_exit = tk.Button(self.frame_buttons)
        self.button_exit["text"] = "Exit"
        self.button_exit["width"] = 17
        self.button_exit["pady"] = 10
        self.button_exit["command"] = self.quit
        self.button_exit.grid(row=0, column=3, padx=10, pady=10)

        # create listbox frame
        self.frame_treeview = tk.Frame(self)
        self.frame_treeview.grid_columnconfigure(0, weight=1)
        self.frame_treeview.grid_rowconfigure(0, weight=1)
        self.frame_treeview.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # creating treeview for duplicity files
        self.treeview_list_duplicity_files = ttk.Treeview(self.frame_treeview)
        self.treeview_list_duplicity_files.heading("#0", text="List duplicity files")
        self.treeview_list_duplicity_files.column("#0", minwidth=self.width, width=self.width, stretch=True)
        self.update_list_duplicate_files()

        self.treeview_list_duplicity_files.grid(row=0, column=0, sticky=tk.NSEW)

        # creating vertical scrollbar
        self.scrollbar_list_duplicity_vertical = tk.Scrollbar(
            self.frame_treeview,
            orient=tk.VERTICAL,
            command=self.treeview_list_duplicity_files.yview
        )
        self.scrollbar_list_duplicity_vertical.grid(row=0, column=1, sticky=tk.NS)

        # creating horizontal scrollbar
        self.scrollbar_list_duplicity_horizontal = tk.Scrollbar(
            self.frame_treeview,
            orient=tk.HORIZONTAL,
            command=self.treeview_list_duplicity_files.xview
        )
        self.scrollbar_list_duplicity_horizontal.grid(row=1, column=0, sticky=tk.EW)

        # adding scrollbars to list duplicity files (treeview)
        self.treeview_list_duplicity_files.configure(
            yscrollcommand=self.scrollbar_list_duplicity_vertical.set,
            xscrollcommand=self.scrollbar_list_duplicity_horizontal.set
        )

    def dialog_root_folder_show(self) -> None:
        dlg = DialogListRootFolders(self)
        dlg.grab_set()

    def insert_line(self, new_line: str, id: int) -> None:
        """
        The function inserts a new line to treeview and it customizes min-width of the treeview

        :param new_line: Text of the item
        :param id: ID of the item
        """
        width = self.font.measure(new_line) + 40
        if width > self.width:
            self.treeview_list_duplicity_files.column("#0", minwidth=width)
            self.width = width
        self.treeview_list_duplicity_files.insert(
            '',
            tk.END,
            text=new_line,
            iid=id,
            open=False
        )

    def update_list_duplicate_files(self) -> None:
        """
        Updating the treeview of the list duplicate files
        """
        self.treeview_list_duplicity_files.delete(*self.treeview_list_duplicity_files.get_children())
        for df in load_duplicate_files(db_session):
            self.insert_line(df.get('file_original').filename, df.get('file_original').id)
            for f in df.get('file_copy'):
                self.insert_line(f.filename, f.id)
                self.treeview_list_duplicity_files.move(
                    f.id,
                    df.get("file_original").id,
                    f.id
                )

    def dialog_changed_files_show(self) -> None:
        """
        Show dialog changed files
        """
        dlg = DialogListChangedFiles(self)
        dlg.grab_set()


if __name__ == '__main__':
    # search_duplicity_files()

    # create database session
    global db_session
    engine = db.load_engine()
    db.create_db_structure(engine)
    db_session = db.create_session(engine)

    window = SearchDuplicityFilesGUI()
    window.mainloop()
