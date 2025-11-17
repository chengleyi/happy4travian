from flask import Blueprint, jsonify, request
from db import SessionLocal
from models import Village

bp = Blueprint("villages", __name__)

@bp.get("/api/v1/villages")
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

@bp.post("/api/v1/villages")
def create_village():
    data = request.get_json(force=True)
    v = Village(server_id=int(data.get("serverId")), game_account_id=int(data.get("gameAccountId")), name=str(data.get("name")), x=int(data.get("x")), y=int(data.get("y")))
    with SessionLocal() as db:
        db.add(v)
        db.commit()
        db.refresh(v)
        return jsonify({"id": v.id, "serverId": v.server_id, "gameAccountId": v.game_account_id, "name": v.name, "x": v.x, "y": v.y})