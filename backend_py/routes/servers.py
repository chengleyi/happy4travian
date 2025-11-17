"""服务器相关接口

提供服务器列表与创建能力。
"""
from datetime import date
from flask import Blueprint, request
from utils.resp import ok, error
from db import SessionLocal
from models import Server

bp = Blueprint("servers", __name__)

@bp.get("/api/v1/servers")
def list_servers():
    """列出服务器"""
    with SessionLocal() as db:
        rows = db.query(Server).all()
        return ok([
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

@bp.post("/api/v1/servers")
def create_server():
    """创建服务器"""
    data = request.get_json(force=True)
    code = data.get("code")
    region = data.get("region")
    speed = data.get("speed")
    startDate = data.get("startDate")
    if not code:
        return error("bad_request", message="code_required", status=400)
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
        return ok({
            "id": s.id,
            "code": s.code,
            "region": s.region,
            "speed": s.speed,
            "startDate": s.start_date.isoformat() if s.start_date else None,
            "status": s.status,
        })