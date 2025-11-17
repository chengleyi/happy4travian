from flask import Blueprint, request
from utils.resp import ok
from db import SessionLocal
from models import GameAccount

bp = Blueprint("accounts", __name__)

@bp.get("/api/v1/accounts")
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
    data = request.get_json(force=True)
    a = GameAccount(user_id=int(data.get("userId")), server_id=int(data.get("serverId")), tribe_id=int(data.get("tribeId")), in_game_name=str(data.get("inGameName")))
    with SessionLocal() as db:
        db.add(a)
        db.commit()
        db.refresh(a)
        return ok({"id": a.id, "userId": a.user_id, "serverId": a.server_id, "tribeId": a.tribe_id, "inGameName": a.in_game_name})