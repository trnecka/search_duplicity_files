# import configure constants
from typing import List

import config

from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column, relationship
from sqlalchemy import Column, Integer, String, create_engine, Engine, ForeignKey


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "file"
    id: Mapped[int] = mapped_column(primary_key=True)
    filehash: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(1000), nullable=False)
    parent_file_id: Mapped[int] = mapped_column(default=0)
    root_folder_id: Mapped[int] = mapped_column(Integer, ForeignKey("root_folder.id", ondelete='CASCADE'))
    root_folder = relationship(
        "RootFolder",
        back_populates="files"
    )


class RootFolder(Base):
    __tablename__ = "root_folder"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    path: Mapped[str] = mapped_column(String(1000), nullable=False)
    files = relationship(
        "File",
        back_populates="root_folder",
        cascade="all, delete",
        passive_deletes=True
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
