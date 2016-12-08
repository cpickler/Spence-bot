# Series of functions to handle postgres database

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
import sqlalchemy
import json

Base = declarative_base()


def load_credentials():
    with open('credentials.json') as f:
        return json.load(f)

credentials = load_credentials()
sql_url = credentials['sql_url']

class World(Base):
    __tablename__ = 'world_names'

    id = Column(Integer, primary_key=True)
    name = Column(String)

engine = sqlalchemy.create_engine(sql_url)
Session = sessionmaker(bind=engine)

session = Session()
