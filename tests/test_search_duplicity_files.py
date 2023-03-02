import os
import sys

sys.path.append('../')
import search_duplicity_files as sdf
import db

# constants for testing
ROOT_FOLDER = os.path.abspath("test_files") + "/"

# dataset for test
LIST_DUPLICATE_FILES = [
    [
        'test_files/African_Elephant_(188286877).jpeg',
        'test_files/animals/African_Elephant_(188286877).jpeg'
    ],
    [
        'test_files/dog-gfb6b9f480_1280.jpg',
        'test_files/animals/dog-gfb6b9f480_1280.jpg',
        'test_files/pes-duplicity.jpg'
    ],
    [
        'test_files/pes-seznamka-1.jpg',
        'test_files/animals/pes-seznamka-1.jpg'
    ],
    [
        'test_files/rqhHrL.jpeg',
        'test_files/lavicka-duplicity.jpeg'
    ]
]


def test_load_files_number_of_files_is_17():
    root_folder, files = sdf.load_files(ROOT_FOLDER)
    assert len(files) == 17


def test_load_files_list_contents_file_rqhhrl_jpeg():
    existing_file = ROOT_FOLDER + "rqhHrL.jpeg"
    root_folder, files = sdf.load_files(ROOT_FOLDER)
    assert existing_file in files


def test_load_files_all_files_exists_on_drive():
    root_folder, files = sdf.load_files(ROOT_FOLDER)
    for files in files:
        assert os.path.exists(files)


def test_get_hash_hash_exists_for_file():
    file = ROOT_FOLDER + "rqhHrL.jpeg"
    hash_for_file = "619b4755d6ea5f404224c3ea7ca8bb6b"
    assert sdf.get_hash(file) == hash_for_file


def basic_database_create():
    import config
    database_file = config.CONNECTION_STRING.split('/')[-1]
    if os.path.isfile(database_file):
        os.remove(database_file)
    engine = db.load_engine()
    db.create_db_structure(engine)
    session = db.create_session(engine)
    return session


def test_save_files_number_of_changed_files_after_first_saving_files_to_database_is_0():
    session = basic_database_create()
    root_folder, files = sdf.load_files(ROOT_FOLDER)
    list_changed_files = sdf.save_files(session, files, root_folder)
    assert len(list_changed_files) == 0


def test_save_files_number_of_changed_file_after_change_file_content_is_1():
    """
    The test of the change file in the course of the test
    The scenario of the test:
        -1. Creating the file
        -2. Saving the file to the database
        -3. Changing of the file
        -4. Saving changed file to the database
        -5. Saving the return value from the function save_files() to the variable
        -6. Deleting the file which created this test
    """
    # initialize to the database and create full path to the new file
    session = basic_database_create()
    new_file = ROOT_FOLDER + '/test_file.txt'

    # creating a file
    with open(new_file, 'w') as f:
        import random
        import string
        f.write(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(100)))

    # saving created file to database
    root_folder, files = sdf.load_files(ROOT_FOLDER)
    sdf.save_files(session, files, root_folder)

    # changing created file content
    with open(new_file, 'a') as f:
        f.write('Append text')

    # saving changed file to the database
    root_folder, edited_file = sdf.load_files(ROOT_FOLDER)
    changed_files = sdf.save_files(session, edited_file, root_folder)

    # delete testing file
    if os.path.isfile(new_file):
        os.remove(new_file)

    assert len(changed_files) == 1


def test_load_duplicate_files_loaded_files_are_in_the_list():

    # creating the database
    session = basic_database_create()

    # saving the data to the database
    root_folder, files = sdf.load_files(ROOT_FOLDER)
    sdf.save_files(session, files, root_folder)

    # loading data from database
    loaded_files = sdf.load_duplicate_files(session)

    # prepare of the dataset
    loaded_files_joined = list()
    for file in LIST_DUPLICATE_FILES:
        loaded_files_joined.extend([os.path.abspath(f) for f in file])

    # test
    for lf in loaded_files:
        assert lf.get('file_original').filename in loaded_files_joined
        for f in lf.get('file_copy'):
            assert f.filename in loaded_files_joined


def test_get_duplicates_for_file_file_rqhHrL_jpeg_has_min_one_duplicate():
    session = basic_database_create()
    root_folder, files = sdf.load_files(ROOT_FOLDER)
    sdf.save_files(session, files, root_folder)
    test_file = os.path.abspath('test_files/rqhHrL.jpeg')

    assert len(sdf.get_duplicates_for_file(session, test_file)) > 1


def test_get_duplicates_for_file_file_PUmFFwcN_html_does_not_have_duplicate():
    session = basic_database_create()
    root_folder, files = sdf.load_files(ROOT_FOLDER)
    sdf.save_files(session, files, root_folder)
    test_file = os.path.abspath('test_files/PUmFFwcN.html')

    assert len(sdf.get_duplicates_for_file(session, test_file)) == 1


def test_get_duplicates_for_file_file_testovaci_txt_does_not_exists():
    session = basic_database_create()
    root_folder, files = sdf.load_files(ROOT_FOLDER)
    sdf.save_files(session, files, root_folder)
    test_file = os.path.abspath('test_files/testovaci.txt')

    assert len(sdf.get_duplicates_for_file(session, test_file)) == 0
