import os
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


if __name__ == '__main__':
    search_duplicity_files()
