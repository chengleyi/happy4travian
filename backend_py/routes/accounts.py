"""游戏账号相关接口

提供账号列表与创建能力，支持按用户或服务器筛选。
"""
from flask import Blueprint, request
from utils.req import get_json
from utils.resp import ok, error
from db import SessionLocal
from models import GameAccount

bp = Blueprint("accounts", __name__)

@bp.get("/api/v1/accounts")
def list_accounts():
    """列出游戏账号（可筛选）"""
    userId_raw = request.args.get("userId")
    serverId_raw = request.args.get("serverId")
    userId = None
    serverId = None
    if userId_raw is not None:
        try:
            userId = int(userId_raw)
        except Exception:
            return error("bad_request", message="userId_invalid", status=400)
    if serverId_raw is not None:
        try:
            serverId = int(serverId_raw)
        except Exception:
            return error("bad_request", message="serverId_invalid", status=400)
    with SessionLocal() as db:
        q = db.query(GameAccount)
        if userId is not None:
            q = q.filter(GameAccount.user_id == userId)
        if serverId is not None:
            q = q.filter(GameAccount.server_id == serverId)
        rows = q.all()
        return ok([
            {
                "id": r.id,
                "userId": r.user_id,
                "serverId": r.server_id,
                "tribeId": r.tribe_id,
                "inGameName": r.in_game_name,
            }
            for r in rows
        ])

@bp.post("/api/v1/accounts")
def create_account():
    data = get_json()
    a = GameAccount(user_id=int(data.get("userId")), server_id=int(data.get("serverId")), tribe_id=int(data.get("tribeId")), in_game_name=str(data.get("inGameName")))
    with SessionLocal() as db:
        db.add(a)
        db.commit()
        db.refresh(a)
        return ok({"id": a.id, "userId": a.user_id, "serverId": a.server_id, "tribeId": a.tribe_id, "inGameName": a.in_game_name})