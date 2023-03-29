from core import db
from hashlib import md5
import typing as t
import os
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import and_, or_

# create database session
global db_session
engine = db.load_engine()
db.create_db_structure(engine)
db_session = db.create_session(engine)


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


def load_duplicate_files(session: Session) -> t.List[t.List[db.File]]:
    """
    Load only duplicates of the files. The first file is always the file which it founded as the first.
    The column of the first file parent_file_id contents 0.

    :param session: The function create_session() from the file db.py
    :return: The list of the list of the db.File object
    """
    # variable contents all items if it is not only one on the database (parent_file_id > 0)
    db_file_dupl = session.query(db.File).filter(db.File.parent_file_id > 0).group_by(db.File.parent_file_id).all()

    # id of the files if they have some duplicates
    db_file_orig_ids = [dfd.parent_file_id for dfd in db_file_dupl]

    duplicate_files = list()
    for db_file_orig_id in db_file_orig_ids:
        duplicate_files.append(session.query(db.File).
                               filter(or_(db.File.id == db_file_orig_id, db.File.parent_file_id == db_file_orig_id)).
                               order_by(db.File.id).
                               all())

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
