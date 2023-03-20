import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from tkinter.filedialog import askdirectory
from hashlib import md5

from sqlalchemy.sql.operators import and_

import db


def load_files(root_folder: str) -> list:
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
    with open(path_file, "rb") as file:
        hash_file = md5(file.read()).hexdigest()
    return hash_file


def get_parent_file_id(session, file: str) -> int:
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


def file_exists(session, file: str) -> bool:
    """
    Check if the file exists in database. File has to have the same hash and filename.

    :param session: The function create_session() from the file db.py
    :param file: Full path to the file.
    :return: It returns True or False
    """
    return bool(session.query(db.File).filter(
        and_(db.File.filename == file, db.File.filehash == get_hash(file))
    ).first())


def is_file_changed(session, file: str):
    """
    The function check if the file is the same as the file saved in the database.
    The file has the same path (like in the database) but it has different content.

    :param session: The function create_session() from the file db.py
    :param file: Full path to the file.
    :return: Full path to the file which it is different in the database.
    """
    input_file_hash = get_hash(file)
    database_file = session.query(db.File).filter(
        db.File.filename == file
    ).first()
    if database_file is not None:
        if input_file_hash != database_file.filehash:
            return database_file.filename
    return False


def save_files(session, files: list, root_folder: str) -> list:
    """
    Saving files to the database.
    Function checks the changes of the files in the database and returns these changes.

    :param session: The function create_session() from the file db.py
    :param root_folder: Full path to the root folder.
    :param files: The list of the file with full paths.
    :return: List of the changed files
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

    changed_file = list()
    for file in files:
        if not file_exists(session, file):
            if chf := is_file_changed(session, file):
                changed_file.append(chf)
            else:
                session.add(
                    db.File(
                        filehash=get_hash(file),
                        filename=file,
                        parent_file_id=get_parent_file_id(session, file),
                        root_folder_id=saved_root_folder.id
                    )
                )
                session.commit()
    return changed_file


def load_duplicate_files(session):
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


def get_duplicates_for_file(session, file: str) -> list:
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


class DialogListRootFolders(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("List root folders")
        self.font = tkfont.Font()
        self.width = 300

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
        self.button_cancel["text"] = "Cancel"
        self.button_cancel["pady"] = 10
        self.button_cancel["width"] = 10
        self.button_cancel["command"] = self.destroy
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

        if not bool(db_session.query(db.RootFolder).filter(db.RootFolder.path == folder_path).first()):
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


class SearchDuplicityFilesGUI(tk.Tk):
    def __init__(self):
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
        for df in load_duplicate_files(db_session):
            self.insert_line(df.get('file_original').filename, df.get('file_original').id)
            for f in df.get('file_copy'):
                self.insert_line(f.filename, f.id)
                self.treeview_list_duplicity_files.move(
                    f.id,
                    df.get("file_original").id,
                    f.id
                )

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

    def dialog_root_folder_show(self):
        dlg = DialogListRootFolders(self)
        dlg.grab_set()

    def insert_line(self, new_line, id):
        """
        The function inserts a new line to treeview and it customizes minwidth of the treeview

        :param new_line: Text of the item
        :param id: Id of the item
        :return: None
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


if __name__ == '__main__':
    # search_duplicity_files()

    # create database session
    global db_session
    engine = db.load_engine()
    db.create_db_structure(engine)
    db_session = db.create_session(engine)

    window = SearchDuplicityFilesGUI()
    window.mainloop()
