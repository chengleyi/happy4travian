from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime
from db import Base

class Server(Base):
    __tablename__ = "servers"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(32), nullable=False)
    region = Column(String(32))
    speed = Column(String(16))
    start_date = Column(Date)
    status = Column(String(16))

class Tribe(Base):
    __tablename__ = "tribes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(16), nullable=False)
    name = Column(String(32), nullable=False)

class GameAccount(Base):
    __tablename__ = "game_accounts"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    server_id = Column(BigInteger, nullable=False)
    tribe_id = Column(Integer, nullable=False)
    in_game_name = Column(String(64), nullable=False)

class Village(Base):
    __tablename__ = "villages"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    server_id = Column(BigInteger, nullable=False)
    game_account_id = Column(BigInteger, nullable=False)
    name = Column(String(64), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)

class TroopCount(Base):
    __tablename__ = "troop_counts"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    village_id = Column(BigInteger, nullable=False)
    troop_type_id = Column(Integer, nullable=False)
    count = Column(BigInteger, nullable=False)

class Alliance(Base):
    __tablename__ = "alliances"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    server_id = Column(BigInteger, nullable=False)
    name = Column(String(64), nullable=False)
    tag = Column(String(16), nullable=False)
    description = Column(String)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime)

class AllianceMember(Base):
    __tablename__ = "alliance_members"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    alliance_id = Column(BigInteger, nullable=False)
    game_account_id = Column(BigInteger, nullable=False)
    server_id = Column(BigInteger, nullable=False)
    role = Column(String(16), nullable=False)
    join_status = Column(String(16))
    joined_at = Column(DateTime)

class TroopType(Base):
    __tablename__ = "troop_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tribe_id = Column(Integer, nullable=False)
    code = Column(String(16), nullable=False)
    name = Column(String(32), nullable=False)