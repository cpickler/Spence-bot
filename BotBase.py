# Series of functions to handle postgres database

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import sessionmaker
import sqlalchemy
import json
from guildwars2api.v1 import GuildWars2API as GW1

Api = GW1()
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


class Users(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    api_key = Column(String)


engine = sqlalchemy.create_engine(sql_url)
Session = sessionmaker(bind=engine)
session = Session()


def get_world(wid):
    query = session.query(World.name).filter(World.id == wid).one()
    return query[0]


def add_key(uid, key):
    existing = session.query(Users).filter(Users.id == uid).one_or_none()
    if existing is None:
        user = Users(id=uid, api_key=key)
        session.add(user)
    else:
        existing.api_key = key
    session.commit()
    return "You're API key was added!"


if __name__ == "__main__":
    def worldset():
        for world in Api.world_names.get():
            try:
                w = World(id=int(world['id']), name=world['name'])
                session.add(w)
            except:
                print('Couldnt add' + w)

    session.commit()
    session.close()