from contextlib import contextmanager

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
from tornado import options

from . import settings


Base = declarative_base()


class Murmur(Base):

    __tablename__ = 'murmur'

    id = Column(Integer, primary_key=True)
    sentence = Column(String(65536), nullable=False)


class Meme(Base):

    __tablename__ = 'meme'

    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, unique=True)
    url = Column(String(65536), nullable=False)


@contextmanager
def Session():
    session = _Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


engine = create_engine('sqlite:////tmp/tz.sqlite')
Base.metadata.create_all(engine)
_Session = sessionmaker(bind=engine)
