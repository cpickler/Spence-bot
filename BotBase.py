# Series of functions to handle postgres database

import os

import sqlalchemy
from guildwars2api.v1 import GuildWars2API as GW1
from guildwars2api.v2 import GuildWars2API as GW2
from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Api1 = GW1()
Api2 = GW2()

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
    default_character = Column(String)


class WorldRoles(Base):
    __tablename__ = 'world-roles'

    id = Column(BigInteger, primary_key=True)
    server = Column(BigInteger)
    world_id = Column(Integer)


class Servers(Base):
    __tablename__ = 'servers'

    id = Column(BigInteger, primary_key=True)
    name = Column(String)


class GuildRoles(Base):
    __tablename__ = 'guild-roles'

    id = Column(BigInteger, primary_key=True)
    guild_id = Column(String)
    server = Column(BigInteger)


class Guilds(Base):
    __tablename__ = 'guilds'

    id = Column(String, primary_key=True)
    name = Column(String)
    tag = Column(String)


class Agony(Base):
    __tablename__ = 'agony'

    id = Column(Integer, primary_key=True)
    agony = Column(Integer)


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
    existing = session.query(WorldRoles).filter(WorldRoles.id == rid).one_or_none()
    if existing is not None:
        existing.id = rid
        existing.server = sid
        existing.world_id = wid
    elif existing is None:
        role = WorldRoles(world_id=wid, id=rid, server=sid)
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
    existing = session.query(WorldRoles.id).filter(WorldRoles.server == sid and WorldRoles.world_id == wid).one_or_none()
    if existing is not None:
        return existing[0]
    else:
        return existing


def add_guild_role(gid, rid, sid):
    existing = session.query(GuildRoles).filter(GuildRoles.id == rid, GuildRoles.server == sid).one_or_none()
    if existing is None:
        guild = GuildRoles(id=rid, guild_id=gid, server=sid)
        session.add(guild)
        result = True
    else:
        existing.role = rid
        result = True
    session.commit()
    return result


def get_add_guild(gid):
    guild = session.query(Guilds).filter(Guilds.id == gid).one_or_none()
    if guild is None:
        details = Api1.guild_details.get(guild_id=gid)
        guild = Guilds(id=gid, tag=details['guild_name'], name=details['tag'])
        session.add(guild)
        session.commit()
    return {'id': guild.id, 'guild_name': guild.name, 'tag': guild.name}


def worldset():
    for world in Api1.world_names.get():
        existing = session.query(World).filter(World.id == world['id']).one_or_none()
        if existing is None:
            w = World(id=int(world['id']), name=world['name'])
            session.add(w)
    session.commit()


def get_guild_role(server, gid):
    existing = session.query(GuildRoles.id).filter(GuildRoles.guild_id == gid,
                                                   GuildRoles.server == int(server)).one_or_none()
    if existing is None:
        return None
    else:
        return existing[0]


def get_agony_resistance(id):
    existing = session.query(Agony.agony).filter(Agony.id==id).one_or_none()
    if existing is None:
        agony = 0
        item = Api2.items.get(id=id)
        for inf in item['details']['infix_upgrade']['attributes']:
            if inf['attribute'] == 'AgonyResistance':
                agony += inf['modifier']
        infusion = Agony(id=id, agony=agony)
        session.add(infusion)
        session.commit()
    else:
        agony = existing[0]
    return agony


def set_default_character(uid, cname):
    existing = session.query(Users).filter(Users.id == uid).one_or_none()
    if existing is None:
        return False
    else:
        existing.default_character = cname
        session.commit()
        return True

worldset()

if __name__ == "__main__":
    worldset()
    session.commit()
    session.close()
