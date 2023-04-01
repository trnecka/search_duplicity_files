# import configure constants
import config

from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, create_engine, Engine, ForeignKey
from sqlalchemy.orm import Session


class Base(DeclarativeBase):
    """
    Base class for declarative class definition.
    """
    pass


class File(Base):
    """
    Class represents the list of the mapped files in the database.
    """

    __tablename__ = "file"

    id: Mapped[int] = mapped_column(primary_key=True, comment="ID of the file record")
    """ ID of the record in the database table """

    filehash: Mapped[str] = mapped_column(String(255), nullable=False, comment="Hash string of the file.")
    """ The hash of the file """

    filename: Mapped[str] = mapped_column(String(1000), nullable=False, comment="Full path to the file.")
    """ The name of the file """

    root_folder_id: Mapped[int] = mapped_column(Integer, ForeignKey("root_folder.id", ondelete='CASCADE'), comment="Folder for searching duplicate files.")
    """ ID mapped folder """

    root_folder = relationship(
        "RootFolder",
        back_populates="files"
    )


class RootFolder(Base):
    """
    Class represents mapped folder. This so-called root folder can contain another sub-folders.
    """

    __tablename__ = "root_folder"

    id: Mapped[int] = mapped_column(primary_key=True, comment="ID of the folder record")
    """ ID of the record in the database table """

    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="Custom name of the folder")
    """ Custom name for the folder """

    path: Mapped[str] = mapped_column(String(1000), nullable=False, comment="Full path to the folder")
    """ The full path to the folder """

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


def create_session(engine: Engine) -> Session:
    """
    Creating configurable Session factory

    :param engine: sqlalchemy.engine.base.Engine
    :return: Database session of sessionmaker() function
    """
    Session = sessionmaker(bind=engine)
    return Session()
