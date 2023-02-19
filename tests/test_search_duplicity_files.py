import os
import sys

sys.path.append('../')
import search_duplicity_files as sdf
import db

# constants for testing
ROOT_FOLDER = os.path.abspath("test_files") + "/"


def test_load_files_number_of_files_is_17():
    assert len(sdf.load_files(ROOT_FOLDER)) == 17


def test_load_files_list_contents_file_rqhhrl_jpeg():
    existing_file = ROOT_FOLDER + "rqhHrL.jpeg"
    assert existing_file in sdf.load_files(ROOT_FOLDER)


def test_load_files_all_files_exists_on_drive():
    for files in sdf.load_files(ROOT_FOLDER):
        assert os.path.exists(files)


def test_get_hash_hash_exists_for_file():
    file = ROOT_FOLDER + "rqhHrL.jpeg"
    hash_for_file = "619b4755d6ea5f404224c3ea7ca8bb6b"
    assert sdf.get_hash(file) == hash_for_file


def create_basic_database():
    import config
    database_file = config.CONNECTION_STRING.split('/')[-1]
    if os.path.isfile(database_file):
        os.remove(database_file)
    engine = db.load_engine()
    db.create_db_structure(engine)
    session = db.create_session(engine)
    return session


def test_new_files_number_of_new_files_is_17():
    session = create_basic_database()
    loading_files = sdf.load_files('test_files')
    assert len(sdf.new_files(session, loading_files)) == 17


def test_new_files_number_added_files_from_folder_test_new_files_is_1():
    session = create_basic_database()
    loading_files = sdf.load_files('test_new_files')
    assert len(sdf.new_files(session, loading_files)) == 1

