from flask import Blueprint
from utils.resp import ok, error
from tools.migrations import migrate_missing_columns
from tools.seed_basic_data import ensure_tables, seed_tribes, seed_server, seed_users_accounts_villages, seed_alliance, seed_troop_types_from_json
from db import SessionLocal

bp = Blueprint("dev", __name__)

@bp.route("/api/v1/dev/seed", methods=["POST"])
def dev_seed():
    try:
        ensure_tables()
        with SessionLocal() as db:
            seed_tribes(db); seed_server(db); seed_users_accounts_villages(db); seed_alliance(db); seed_troop_types_from_json(db); db.commit()
        return ok({"message":"seed_done"})
    except Exception as e:
        return error("server_error", message=str(e))

@bp.route("/api/v1/dev/migrate", methods=["POST"])
def dev_migrate():
    try:
        changes = migrate_missing_columns()
        return ok({"message":"migrate_done","changes":changes})
    except Exception as e:
        return error("server_error", message=str(e))