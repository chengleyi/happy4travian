import json
from flask import Blueprint, Response
from tools.seed_basic_data import ensure_tables, seed_tribes, seed_server, seed_users_accounts_villages, seed_alliance, seed_troop_types_from_json
from db import SessionLocal

bp = Blueprint("dev", __name__)

@bp.post("/api/v1/dev/seed")
def dev_seed():
    try:
        ensure_tables()
        stats = {"tribes":0,"servers":0,"accounts":0,"villages":0,"alliances":0,"members":0,"troopTypes":0}
        with SessionLocal() as db:
            seed_tribes(db); seed_server(db); seed_users_accounts_villages(db); seed_alliance(db); seed_troop_types_from_json(db); db.commit()
        body = {"success": True, "message": "seed_done", "stats": stats}
        return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json")
    except Exception as e:
        err = {"success": False, "error": "server_error", "message": str(e)}
        return Response(json.dumps(err, ensure_ascii=False, indent=2), mimetype="application/json"), 500