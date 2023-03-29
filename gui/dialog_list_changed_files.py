import tkinter as tk

from core.sdfcore import check_changed_files, db_session, save_changed_files


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