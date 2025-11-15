import os
import re
from datetime import date
from typing import Dict, List, Optional

from fastapi import FastAPI, Depends, Query, Body
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session

app = FastAPI()

jdbc = os.getenv("SPRING_DATASOURCE_URL", "")
user = os.getenv("SPRING_DATASOURCE_USERNAME", "")
password = os.getenv("SPRING_DATASOURCE_PASSWORD", "")
m = re.match(r"jdbc:mysql://([^/:]+)(?::(\d+))?/([^?]+)", jdbc)
host = m.group(1) if m else "localhost"
port = int(m.group(2)) if m and m.group(2) else 3306
dbname = m.group(3) if m else "happy4travian"
url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}?charset=utf8mb4"
engine = create_engine(url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

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

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CreateServerRequest(BaseModel):
    code: str
    region: Optional[str] = None
    speed: Optional[str] = None
    startDate: Optional[str] = None

class CreateTribeRequest(BaseModel):
    code: str
    name: str

class CreateGameAccountRequest(BaseModel):
    userId: int
    serverId: int
    tribeId: int
    inGameName: str

class CreateVillageRequest(BaseModel):
    serverId: int
    gameAccountId: int
    name: str
    x: int
    y: int

class UploadTroopsRequest(BaseModel):
    villageId: int
    counts: Dict[int, int]

@app.get("/api/v1/health")
def health():
    return "ok"

@app.get("/api/v1/healthz")
def healthz():
    return "ok"

@app.get("/api/v1/db/ping")
def db_ping(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return "ok"
    except Exception:
        return "error"

@app.get("/api/v1/servers")
def list_servers(db: Session = Depends(get_db)):
    rows = db.query(Server).all()
    return [
        {
            "id": r.id,
            "code": r.code,
            "region": r.region,
            "speed": r.speed,
            "startDate": r.start_date.isoformat() if r.start_date else None,
            "status": r.status,
        }
        for r in rows
    ]

@app.post("/api/v1/servers")
def create_server(req: CreateServerRequest, db: Session = Depends(get_db)):
    if not req.code:
        return {"error": "bad_request"}
    s = Server()
    s.code = req.code
    s.region = req.region
    s.speed = req.speed
    s.start_date = date.fromisoformat(req.startDate) if req.startDate else None
    s.status = "active"
    db.add(s)
    db.commit()
    db.refresh(s)
    return {
        "id": s.id,
        "code": s.code,
        "region": s.region,
        "speed": s.speed,
        "startDate": s.start_date.isoformat() if s.start_date else None,
        "status": s.status,
    }

@app.get("/api/v1/tribes")
def list_tribes(db: Session = Depends(get_db)):
    rows = db.query(Tribe).all()
    return [{"id": r.id, "code": r.code, "name": r.name} for r in rows]

@app.post("/api/v1/tribes")
def create_tribe(req: CreateTribeRequest, db: Session = Depends(get_db)):
    if not req.code or not req.name:
        return {"error": "bad_request"}
    t = Tribe(code=req.code, name=req.name)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "code": t.code, "name": t.name}

@app.get("/api/v1/accounts")
def list_accounts(userId: Optional[int] = Query(None), serverId: Optional[int] = Query(None), db: Session = Depends(get_db)):
    q = db.query(GameAccount)
    if userId is not None:
        q = q.filter(GameAccount.user_id == userId)
    if serverId is not None:
        q = q.filter(GameAccount.server_id == serverId)
    rows = q.all()
    return [
        {
            "id": r.id,
            "userId": r.user_id,
            "serverId": r.server_id,
            "tribeId": r.tribe_id,
            "inGameName": r.in_game_name,
        }
        for r in rows
    ]

@app.post("/api/v1/accounts")
def create_account(req: CreateGameAccountRequest, db: Session = Depends(get_db)):
    a = GameAccount(user_id=req.userId, server_id=req.serverId, tribe_id=req.tribeId, in_game_name=req.inGameName)
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"id": a.id, "userId": a.user_id, "serverId": a.server_id, "tribeId": a.tribe_id, "inGameName": a.in_game_name}

@app.get("/api/v1/villages")
def list_villages(serverId: Optional[int] = Query(None), gameAccountId: Optional[int] = Query(None), db: Session = Depends(get_db)):
    q = db.query(Village)
    if serverId is not None:
        q = q.filter(Village.server_id == serverId)
    if gameAccountId is not None:
        q = q.filter(Village.game_account_id == gameAccountId)
    rows = q.all()
    return [
        {
            "id": r.id,
            "serverId": r.server_id,
            "gameAccountId": r.game_account_id,
            "name": r.name,
            "x": r.x,
            "y": r.y,
        }
        for r in rows
    ]

@app.post("/api/v1/villages")
def create_village(req: CreateVillageRequest, db: Session = Depends(get_db)):
    v = Village(server_id=req.serverId, game_account_id=req.gameAccountId, name=req.name, x=req.x, y=req.y)
    db.add(v)
    db.commit()
    db.refresh(v)
    return {"id": v.id, "serverId": v.server_id, "gameAccountId": v.game_account_id, "name": v.name, "x": v.x, "y": v.y}

@app.post("/api/v1/troops/upload")
def upload_troops(req: UploadTroopsRequest, db: Session = Depends(get_db)):
    for k, v in req.counts.items():
        tc = TroopCount(village_id=req.villageId, troop_type_id=int(k), count=int(v))
        db.add(tc)
    db.commit()
    return "ok"

@app.get("/api/v1/troops/aggregate")
def troops_aggregate(villageId: int = Query(...), db: Session = Depends(get_db)):
    rows = db.query(TroopCount).filter(TroopCount.village_id == villageId).all()
    return {int(r.troop_type_id): int(r.count) for r in rows}