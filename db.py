# import configure constants
import config

from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import Column, Integer, String, create_engine, Engine


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "file"
    id = Column(Integer, primary_key=True)
    filehash = Column(String(255), nullable=False)
    filename = Column(String(1000), nullable=False)
    parent_file_id = Column(Integer, default=0)

    def __init__(self, filehash, filename, parent_file_id=0):
        self.filehash = filehash
        self.filename = filename
        self.parent_file_id = parent_file_id


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
