# Series of functions to handle postgres database

import os

import sqlalchemy
from guildwars2api.v1 import GuildWars2API as GW1
from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Api = GW1()
Base = declarative_base()
sql_url = os.environ['DATABASE_URL']


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
    world_id = Column(Integer)


class Servers(Base):
    __tablename__ = 'servers'

    id = Column(BigInteger, primary_key=True)
    name = Column(String)

class Guilds(Base):
    __tablename__ = 'guilds'

    id = Column(String, primary_key=True)
    name = Column(String)
    tag = Column(String)
    role = Column(BigInteger)


engine = sqlalchemy.create_engine(sql_url)
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)


def get_world(wid):
    query = session.query(World.name).filter(World.id == wid).one()
    return query[0]


def get_world_id(name):
    query = session.query(World.id).filter(World.name == name).one_or_none()
    try:
        result = query[0]
    except TypeError:
        result = None
    return result


def add_key(uid, key):
    existing = existing_user(uid)
    if existing is None:
        user = Users(id=uid, api_key=key)
        session.add(user)
    else:
        existing.api_key = key
    session.commit()
    return "You're API key was added!"


def existing_user(uid):
    existing = session.query(Users).filter(Users.id == uid).one_or_none()
    return existing


def get_key(uid):
    try:
        key = session.query(Users.api_key).filter(Users.id == uid).one_or_none()[0]
    except TypeError:
        key = None
    return key


def delete_user(uid):
    existing = existing_user(uid)
    if existing is not None:
        session.delete(existing)
        return True
    else:
        return False


def add_world_role(sid, rid, wid):
    """
    Populates the Roles Table with a new row.
    :param sid: Discord Server ID
    :param rid: Discord Role ID
    :param wid: GW2 World ID
    :return: True:Success False:Error
    """
    existing = session.query(Roles).filter(Roles.id == rid).one_or_none()
    if existing is not None:
        existing.id = rid
        existing.server = sid
        existing.world_id = wid
    elif existing is None:
        role = Roles(world_id=wid, id=rid, server=sid)
        session.add(role)
    session.commit()
    return True


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


def get_world_role(sid, wid):
    """
    Get the Role ID for a world on a server
    :param sid: Server ID
    :param wid: World ID
    :return: Role ID or None if it doesn't exist
    """
    existing = session.query(Roles.id).filter(Roles.server == sid and Roles.world_id == wid).one_or_none()
    if existing is not None:
        return existing[0]
    else:
        return existing


def worldset():
    for world in Api.world_names.get():
        w = World(id=int(world['id']), name=world['name'])
        session.add(w)
    session.commit()


if __name__ == "__main__":
    worldset()
    session.commit()
    session.close()
