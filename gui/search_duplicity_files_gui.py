import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from core.sdfcore import load_duplicate_files, db_session
from gui.dialog_list_changed_files import DialogListChangedFiles
from gui.dialog_list_root_folder import DialogListRootFolders


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

        # create label for list duplicity files
        self.label_list_duplicity_files = tk.Label(self)
        self.label_list_duplicity_files["text"] = "List duplicity files:"
        self.label_list_duplicity_files.pack(anchor="w", padx=5)

        # create listbox frame
        self.frame_treeview = tk.Frame(self)
        self.frame_treeview.grid_columnconfigure(0, weight=1)
        self.frame_treeview.grid_rowconfigure(0, weight=1)
        self.frame_treeview.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # creating treeview for duplicity files
        self.treeview_list_duplicity_files = ttk.Treeview(self.frame_treeview, show="tree")
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

        # list all duplicate files
        list_duplicates = load_duplicate_files(db_session)

        # create parent item
        for duplicate_files in list_duplicates:
            # create parent item
            first_file = duplicate_files.pop(0)
            self.insert_line(first_file.filename, first_file.id)
            for file in duplicate_files:
                self.insert_line(file.filename, file.id)
                self.treeview_list_duplicity_files.move(file.id, first_file.id, file.id)

    def dialog_changed_files_show(self) -> None:
        """
        Show dialog changed files
        """
        dlg = DialogListChangedFiles(self)
        dlg.grab_set()
