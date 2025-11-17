from flask import Blueprint, request
from utils.resp import ok, error
from db import SessionLocal
from models import User

bp = Blueprint("users", __name__)

@bp.post("/api/v1/users")
def create_user():
    data = request.get_json(force=True) or {}
    nickname = data.get("nickname") or "user"
    with SessionLocal() as db:
        u = User(nickname=str(nickname), status="active")
        db.add(u)
        db.commit()
        db.refresh(u)
        return ok({"id": u.id, "nickname": u.nickname})

@bp.get("/api/v1/users")
def list_users():
    with SessionLocal() as db:
        rows = db.query(User).all()
        return ok([{"id": r.id, "nickname": r.nickname} for r in rows])