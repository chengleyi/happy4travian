"""部落相关接口

提供部落列表与创建能力。
"""
from flask import Blueprint, request
from utils.resp import ok, error
from db import SessionLocal
from models import Tribe

bp = Blueprint("tribes", __name__)

@bp.get("/api/v1/tribes")
def list_tribes():
    """列出所有部落"""
    with SessionLocal() as db:
        rows = db.query(Tribe).all()
        return ok([{ "id": r.id, "code": r.code, "name": r.name } for r in rows])

@bp.post("/api/v1/tribes")
def create_tribe():
    """创建部落"""
    data = request.get_json(force=True)
    code = data.get("code")
    name = data.get("name")
    if not code or not name:
        return error("bad_request", message="code_and_name_required", status=400)
    t = Tribe(code=code, name=name)
    with SessionLocal() as db:
        db.add(t)
        db.commit()
        db.refresh(t)
        return ok({"id": t.id, "code": t.code, "name": t.name})