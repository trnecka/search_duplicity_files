# import configure constants
from typing import List

import config

from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column, relationship
from sqlalchemy import Column, Integer, String, create_engine, Engine, ForeignKey


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "file"
    id: Mapped[int] = mapped_column(primary_key=True, comment="ID of the file record")
    filehash: Mapped[str] = mapped_column(String(255), nullable=False, comment="Hash string of the file.")
    filename: Mapped[str] = mapped_column(String(1000), nullable=False, comment="Full path to the file.")
    parent_file_id: Mapped[int] = mapped_column(default=0, comment="ID of the parent file from this table. Zero is the first founded file.")
    root_folder_id: Mapped[int] = mapped_column(Integer, ForeignKey("root_folder.id", ondelete='CASCADE'), comment="Folder for searching duplicate files.")
    root_folder = relationship(
        "RootFolder",
        back_populates="files"
    )


class RootFolder(Base):
    __tablename__ = "root_folder"

    id: Mapped[int] = mapped_column(primary_key=True, comment="ID of the folder record")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="Custom name of the folder")
    path: Mapped[str] = mapped_column(String(1000), nullable=False, comment="Full path to the folder")
    files = relationship(
        "File",
        back_populates="root_folder",
        cascade="all, delete"
    )


def load_engine() -> Engine:
    """
    Loading the database engine

    :return: sqlalchemy.engine.base.Engine
    """
    return create_engine(config.CONNECTION_STRING, echo=config.DEVELOP_MODE)


def create_db_structure(engine: Engine) -> None:
    """
    Create tables in the database structure

    :param engine: sqlalchemy.engine.base.Engine
    """
    Base.metadata.create_all(bind=engine)


def create_session(engine: Engine):
    """
    Creating configurable Session factory

    :param engine: sqlalchemy.engine.base.Engine
    :return:
    """
    Session = sessionmaker(bind=engine)
    return Session()
