import os
import sys
import pytest

sys.path.append('../')
import core.sdfcore as sdf
from core import db

# constants for testing
# represents full path to subfolder folder (test_files)
ROOT_FOLDER = os.path.abspath("test_files") + "/"


def test_load_files_number_of_files_is_17():
    root_folder, files = sdf.load_files(ROOT_FOLDER)
    assert len(files) == 17


# list relative paths to files for test load files function
files_for_test = [
    'lavicka-duplicity.jpeg',
    'pes-seznamka-1.jpg',
    'rqhHrL.jpeg',
    'animals/pes-seznamka-1.jpg'
]

# list full paths to tested files
full_paths_of_tested_files = map(lambda file: ROOT_FOLDER + file, files_for_test)


@pytest.mark.parametrize('file', full_paths_of_tested_files, ids=files_for_test)
def test_load_files_list_contents_file(file):
    root_folder, files = sdf.load_files(ROOT_FOLDER)
    assert file in files


def test_load_files_all_files_exists_on_drive():
    root_folder, files = sdf.load_files(ROOT_FOLDER)
    for file in files:
        assert os.path.exists(file)


# relative paths of the files and their hash
file_hash = [
    ('pes-seznamka-1.jpg', '0dd0742271cf37bc9b18965fc10dc9e4'),
    ('animals/pes-seznamka-1.jpg', '0dd0742271cf37bc9b18965fc10dc9e4')
]

# the list of the files for ids in parametrize test
file_ids = [n[0] for n in file_hash]

# data for
file_hash_for_test = [(ROOT_FOLDER + file, hash) for file, hash in file_hash]


@pytest.mark.parametrize('file,hash', file_hash_for_test, ids=file_ids)
def test_get_hash_returns_correct_hash_for_file(file, hash):
    assert sdf.get_hash(file) == hash


# helped function
def basic_database_create():
    import config
    database_file = config.CONNECTION_STRING.split('/')[-1]
    if os.path.isfile(database_file):
        os.remove(database_file)
    engine = db.load_engine()
    db.create_db_structure(engine)
    session = db.create_session(engine)
    sdf.save_files(session, ROOT_FOLDER)
    return session


def test_load_duplicate_files_number_of_the_sublists_is_4():
    assert len(sdf.load_duplicate_files(basic_database_create())) == 4


def test_load_duplicate_files_all_files_are_in_output():
    # structure of the output
    expected_files = [
        [
            ROOT_FOLDER + "pes-seznamka-1.jpg",
            ROOT_FOLDER + "animals/pes-seznamka-1.jpg"
        ],
        [
            ROOT_FOLDER + "lavicka-duplicity.jpeg",
            ROOT_FOLDER + "rqhHrL.jpeg"
        ],
        [
            ROOT_FOLDER + "dog-gfb6b9f480_1280.jpg",
            ROOT_FOLDER + "pes-duplicity.jpg",
            ROOT_FOLDER + "animals/dog-gfb6b9f480_1280.jpg"
        ],
        [
            ROOT_FOLDER + "African_Elephant_(188286877).jpeg",
            ROOT_FOLDER + "animals/African_Elephant_(188286877).jpeg"
        ]
    ]

    # get data from database
    files_from_database = list()
    for set_files in sdf.load_duplicate_files(basic_database_create()):
        list_files = list()
        for file in set_files:
            list_files.append(file.filename)
        files_from_database.append(list_files)

    assert all([ffd == ef for ffd, ef in zip(files_from_database, expected_files)])



