import os
from hashlib import md5

from sqlalchemy.sql.operators import and_

import db


def load_files(root_folder: str) -> list:
    """
    Loading list all files in root folder and subfolders.

    :param root_folder: Relative path to the folder.
    :return: The list of the all files with absolute path.
    """
    list_files = list()
    for (path, _, files) in os.walk(root_folder):
        for file_name in files:
            list_files.append(os.path.abspath((os.path.join(path, file_name))))
    return list_files


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
    :return: Id of the existing hash file, if it does not exists, it will be returned 0.
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
        and_(db.File.filename == file, db.File.filename == get_hash(file))
    ).first())


def new_files(session, files: list) -> list:
    """
    Creating the list of the added files to original database.

    :param session: The function create_session() from the file db.py
    :param files: The list of the file with full paths.
    :return: List of the dictionaries with the keys 'filehash', 'filename', 'parent_file_id'
    """
    for file in files:

        if not file_exists(session, file):
            session.add(
                db.File(
                    filehash=get_hash(file),
                    filename=file,
                    parent_file_id=get_parent_file_id(session, file)
                )
            )
        session.commit()




def search_duplicity_files():
    engine = db.load_engine()
    db.create_db_structure(engine)
    session = db.create_session(engine)
    files = load_files("tests/test_files")

    new_files(session, files)
    # for file in new_files(session, files):
    #     f = db.File(
    #             filehash=file.get("filehash"),
    #             filename=file.get("filename"),
    #             parent_file_id=file.get("parent_file_id")
    #         )
    #     session.add(f)
    # session.commit()


if __name__ == '__main__':
    search_duplicity_files()
