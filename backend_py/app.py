import os
import re
import logging
from datetime import date
from typing import Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Date
from sqlalchemy.orm import declarative_base, sessionmaker

app = Flask(__name__)
CORS(app, origins=["https://happy4travian.com", "https://www.happy4travian.com"], methods=["GET","POST","PUT","DELETE","OPTIONS"], allow_headers=["*"])
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

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

@app.before_request
def _log_before():
    pass

@app.after_request
def _log_after(response):
    try:
        logging.info("api %s %s status=%s", request.method, request.full_path, response.status_code)
    except Exception:
        pass
    return response

@app.get("/api/v1/health")
def health():
    return "ok"

@app.get("/api/v1/healthz")
def healthz():
    return "ok"

@app.get("/api/v1/db/ping")
def db_ping():
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return "ok"
    except Exception:
        return "error"

@app.get("/api/v1/servers")
def list_servers():
    with SessionLocal() as db:
        rows = db.query(Server).all()
        return jsonify([
            {
                "id": r.id,
                "code": r.code,
                "region": r.region,
                "speed": r.speed,
                "startDate": r.start_date.isoformat() if r.start_date else None,
                "status": r.status,
            }
            for r in rows
        ])

@app.post("/api/v1/servers")
def create_server():
    data = request.get_json(force=True)
    code = data.get("code")
    region = data.get("region")
    speed = data.get("speed")
    startDate = data.get("startDate")
    if not code:
        return jsonify({"error":"bad_request"}), 400
    s = Server()
    s.code = code
    s.region = region
    s.speed = speed
    s.start_date = date.fromisoformat(startDate) if startDate else None
    s.status = "active"
    with SessionLocal() as db:
        db.add(s)
        db.commit()
        db.refresh(s)
        return jsonify({
            "id": s.id,
            "code": s.code,
            "region": s.region,
            "speed": s.speed,
            "startDate": s.start_date.isoformat() if s.start_date else None,
            "status": s.status,
        })

@app.get("/api/v1/tribes")
def list_tribes():
    with SessionLocal() as db:
        rows = db.query(Tribe).all()
        return jsonify([{"id": r.id, "code": r.code, "name": r.name} for r in rows])

@app.post("/api/v1/tribes")
def create_tribe():
    data = request.get_json(force=True)
    code = data.get("code")
    name = data.get("name")
    if not code or not name:
        return jsonify({"error":"bad_request"}), 400
    t = Tribe(code=code, name=name)
    with SessionLocal() as db:
        db.add(t)
        db.commit()
        db.refresh(t)
        return jsonify({"id": t.id, "code": t.code, "name": t.name})

@app.get("/api/v1/accounts")
def list_accounts():
    userId = request.args.get("userId", type=int)
    serverId = request.args.get("serverId", type=int)
    with SessionLocal() as db:
        q = db.query(GameAccount)
        if userId is not None:
            q = q.filter(GameAccount.user_id == userId)
        if serverId is not None:
            q = q.filter(GameAccount.server_id == serverId)
        rows = q.all()
        return jsonify([
            {
                "id": r.id,
                "userId": r.user_id,
                "serverId": r.server_id,
                "tribeId": r.tribe_id,
                "inGameName": r.in_game_name,
            }
            for r in rows
        ])

@app.post("/api/v1/accounts")
def create_account():
    data = request.get_json(force=True)
    a = GameAccount(user_id=int(data.get("userId")), server_id=int(data.get("serverId")), tribe_id=int(data.get("tribeId")), in_game_name=str(data.get("inGameName")))
    with SessionLocal() as db:
        db.add(a)
        db.commit()
        db.refresh(a)
        return jsonify({"id": a.id, "userId": a.user_id, "serverId": a.server_id, "tribeId": a.tribe_id, "inGameName": a.in_game_name})

@app.get("/api/v1/villages")
def list_villages():
    serverId = request.args.get("serverId", type=int)
    gameAccountId = request.args.get("gameAccountId", type=int)
    with SessionLocal() as db:
        q = db.query(Village)
        if serverId is not None:
            q = q.filter(Village.server_id == serverId)
        if gameAccountId is not None:
            q = q.filter(Village.game_account_id == gameAccountId)
        rows = q.all()
        return jsonify([
            {
                "id": r.id,
                "serverId": r.server_id,
                "gameAccountId": r.game_account_id,
                "name": r.name,
                "x": r.x,
                "y": r.y,
            }
            for r in rows
        ])

@app.post("/api/v1/villages")
def create_village():
    data = request.get_json(force=True)
    v = Village(server_id=int(data.get("serverId")), game_account_id=int(data.get("gameAccountId")), name=str(data.get("name")), x=int(data.get("x")), y=int(data.get("y")))
    with SessionLocal() as db:
        db.add(v)
        db.commit()
        db.refresh(v)
        return jsonify({"id": v.id, "serverId": v.server_id, "gameAccountId": v.game_account_id, "name": v.name, "x": v.x, "y": v.y})

@app.post("/api/v1/troops/upload")
def upload_troops():
    data = request.get_json(force=True)
    villageId = int(data.get("villageId"))
    counts = data.get("counts", {})
    with SessionLocal() as db:
        for k, v in counts.items():
            tc = TroopCount(village_id=villageId, troop_type_id=int(k), count=int(v))
            db.add(tc)
        db.commit()
    return "ok"

@app.get("/api/v1/troops/aggregate")
def troops_aggregate():
    villageId = request.args.get("villageId", type=int)
    with SessionLocal() as db:
        rows = db.query(TroopCount).filter(TroopCount.village_id == villageId).all()
        return jsonify({int(r.troop_type_id): int(r.count) for r in rows})