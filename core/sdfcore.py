from sqlalchemy import func

from core import db
from hashlib import md5
import typing as t
import os
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import and_

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
    Load only duplicates of the files. The list of the list of the files is sorted by 'id' of the file.

    :param session: The function create_session() from the file db.py
    :return: The list of the list of the db.File object
    """
    duplicate_files = list()

    # get duplicate hash of files
    # query: select * from (select count(*) as file_number, filehash from file group by filehash) where file_number > 1;
    subquery = session.query(
        func.count(db.File.filehash).label("filenumber"),
        db.File.filehash.label("filehash")
    ).group_by(db.File.filehash).subquery("subquery")

    hashes = session.query(subquery.c.filehash).filter(subquery.c.filenumber > 1).all()
    for hash in hashes:
        duplicate_files.append(session.query(db.File).filter(db.File.filehash == hash[0]).all())

    return duplicate_files
