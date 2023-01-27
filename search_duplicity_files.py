import os
from hashlib import md5

import pytest
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import Session, sessionmaker, declarative_base


def load_files(root_folder: str) -> list:
    """
    Loading list all files in root folder and subfolders.

    :param root_folder: str
    :return: list
    """
    list_files = list()
    for (path, _, files) in os.walk(root_folder):
        for file_name in files:
            list_files.append(os.path.abspath((os.path.join(path, file_name))))
    return list_files


def db_init(connection_string: str) -> Session:
    """
    Initialize database structure.

    :param connection_string: str
    :return: Session
    """
    pass


def save_data(init_db_connection: Session) -> bool:
    """
    Saving files to the database. Return value is True if saving data was successful.

    :param init_db_connection: Session
    :return: bool
    """
    pass


def load_same_files(orig_file: str) -> list:
    """
    Loading the same files from database.

    :param orig_file: Path to original file.
    :return: list
    """
    pass


def get_hash(path_file: str) -> str:
    """
    Getting hash from file

    :param path_file: Path to file.
    :return: str
    """
    pass


def search_duplicity_files():
    pass


if __name__ == '__main__':
    search_duplicity_files()
