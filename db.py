# import configure constants
import config

from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column
from sqlalchemy import Column, Integer, String, create_engine, Engine, ForeignKey


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "file"
    id: Mapped[int] = mapped_column(primary_key=True)
    filehash: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(1000), nullable=False)
    parent_file_id: Mapped[int] = mapped_column(default=0)


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
