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


class Roles(Base):
    __tablename__ = 'roles'

    id = Column(BigInteger, primary_key=True)
    server = Column(BigInteger)
    name = Column(String)


class Servers(Base):
    __tablename__ = 'servers'

    id = Column(BigInteger, primary_key=True)
    name = Column(String)


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


def get_key(uid):
    try:
        key = session.query(Users.api_key).filter(Users.id == uid).one_or_none()[0]
    except TypeError:
        key = None
    return key


def delete(uid):
    existing = session.query(Users).filter(Users.id == uid).one_or_none()
    if existing is not None:
        session.delete(existing)
        return True
    else:
        return False


def add_server(sid, sname):
    """
    Adds a server to the database
    :param sid: Discord Server ID
    :param sname: Discord Server Name
    :return: True = Successfully added, False = Successfully updated, None = No change made
    """
    existing = session.query(Servers).filter(Servers.id == sid).one_or_none()
    if existing is None:
        server = Servers(id=sid, name=sname)
        session.add(server)
        result = True
    elif existing.name != sname:
        existing.name = sname
        result = False
    else:
        result = None
    session.commit()
    return result

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