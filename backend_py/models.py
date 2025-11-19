"""ORM 模型定义

定义系统核心实体表结构：用户、服务器、部落、游戏账号、村庄、兵种计数、联盟及成员、兵种类型。
"""
from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, Text
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nickname = Column(String(64))  # 昵称（或展示名）
    wechat_openid = Column(String(64))
    email = Column(String(128))
    password_hash = Column(String(128))
    lang = Column(String(8))
    status = Column(String(16))  # 状态：active/disabled 等
    created_at = Column(DateTime)

class Server(Base):
    __tablename__ = "servers"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(32), nullable=False)  # 服务器编码，如 eu1、cnX
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
    in_game_name = Column(String(64), nullable=False)  # 游戏内名称

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
    count = Column(BigInteger, nullable=False)  # 兵种数量

class Alliance(Base):
    __tablename__ = "alliances"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    server_id = Column(BigInteger, nullable=False)
    name = Column(String(64), nullable=False)
    tag = Column(String(16), nullable=False)
    description = Column(Text)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime)

class AllianceMember(Base):
    __tablename__ = "alliance_members"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    alliance_id = Column(BigInteger, nullable=False)
    game_account_id = Column(BigInteger, nullable=False)
    server_id = Column(BigInteger, nullable=False)
    role = Column(String(16), nullable=False)  # 角色：leader/member 等
    join_status = Column(String(16))  # 加入状态：active 等
    joined_at = Column(DateTime)

class TroopType(Base):
    __tablename__ = "troop_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tribe_id = Column(Integer, nullable=False)
    code = Column(String(16), nullable=False)
    name = Column(String(32), nullable=False)