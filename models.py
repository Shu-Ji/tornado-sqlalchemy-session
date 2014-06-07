# coding: u8

from sqlalchemy import Column, Text, DateTime, String, Integer
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session


engine = create_engine('sqlite:///meta.db')
db = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()


class TornadoSqlaSession(Base):
    __tablename__ = 'tornado_sqla_session'

    sid = Column(String(32), primary_key=True)
    last_access = Column(DateTime)
    data = Column(Text)


if __name__ == '__main__':
    Base.metadata.create_all(engine)
