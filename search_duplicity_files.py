import os

import core.sdfcore
from core import db

from core.sdfcore import load_duplicate_files, get_duplicates_for_file, save_files, load_files
from gui.search_duplicity_files_gui import SearchDuplicityFilesGUI


def search_duplicity_files():
    engine = db.load_engine()
    db.create_db_structure(engine)
    session = db.create_session(engine)
    root_folder, files = load_files("tests/test_files")
    # print the list of the changed files
    print(save_files(session, root_folder))
    print(f"Root folder: {root_folder}")

    # this line is only for testing
    # get data from strucutre
    # the item with parent_file_id = 0 is always the first in the sub-list
    for set_duplicate_files in load_duplicate_files(session):
        print(f"> {set_duplicate_files.pop(0).filename}")
        for file in set_duplicate_files:
            print(f"\t {file.filename}")

    # write all duplicate files of one concrete file
    # example output
    print(f'Duplicates for file "{os.path.abspath("tests/test_files/pes-seznamka-1.jpg")}"')
    for gdff in get_duplicates_for_file(session, os.path.abspath("tests/test_files/pes-seznamka-1.jpg")):
        print(gdff.filename)


if __name__ == '__main__':
    # search_duplicity_files()

    window = SearchDuplicityFilesGUI()
    window.mainloop()
