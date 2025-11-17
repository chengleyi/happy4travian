"""开发辅助接口

提供数据灌入与数据库迁移的触发接口，用于在服务器上快速初始化环境。
"""
from flask import Blueprint
from utils.resp import ok, error
from tools.migrations import migrate_missing_columns
from tools.seed_basic_data import ensure_tables, seed_tribes, seed_server, seed_users_accounts_villages, seed_alliance, seed_troop_types_from_json
from db import SessionLocal

bp = Blueprint("dev", __name__)

@bp.route("/api/v1/dev/seed", methods=["POST"])
def dev_seed():
    """在目标环境灌入基础数据"""
    try:
        ensure_tables()
        with SessionLocal() as db:
            seed_tribes(db); seed_server(db); seed_users_accounts_villages(db); seed_alliance(db); seed_troop_types_from_json(db); db.commit()
        return ok({"message":"seed_done"})
    except Exception as e:
        return error("server_error", message=str(e))

@bp.route("/api/v1/dev/migrate", methods=["POST"])
def dev_migrate():
    """触发列迁移（幂等）"""
    try:
        changes = migrate_missing_columns()
        return ok({"message":"migrate_done","changes":changes})
    except Exception as e:
        return error("server_error", message=str(e))
