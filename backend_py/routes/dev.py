"""开发辅助接口

提供数据灌入与数据库迁移的触发接口，用于在服务器上快速初始化环境。
"""
from flask import Blueprint
from utils.resp import ok, error
from tools.migrations import migrate_missing_columns
from tools.seed_basic_data import ensure_tables, seed_tribes, seed_server, seed_users_accounts_villages, seed_alliance, seed_troop_types_from_json
from db import SessionLocal
from db import engine
from sqlalchemy import text

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

@bp.route("/api/v1/dev/charset", methods=["GET"])
def dev_charset():
    """返回关键表/列的字符集与排序规则，便于诊断中文显示问题"""
    try:
        q = text(
            """
            SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN (
              'alliances','alliance_members','users','servers','tribes','game_accounts','villages','troop_types','troop_counts'
            ) AND COLUMN_NAME IN ('name','tag','description')
            ORDER BY TABLE_NAME, COLUMN_NAME
            """
        )
        rows = []
        with engine.begin() as conn:
            for r in conn.execute(q).mappings():
                rows.append({
                    "table": r["TABLE_NAME"],
                    "column": r["COLUMN_NAME"],
                    "charset": r["CHARACTER_SET_NAME"],
                    "collation": r["COLLATION_NAME"],
                })
        return ok(rows)
    except Exception as e:
        return error("server_error", message=str(e))

@bp.route("/api/v1/dev/alliances/<int:aid>/fixdesc", methods=["POST"])
def dev_fix_alliance_desc(aid: int):
    """将指定联盟的描述直接设置为中文常量（用于验证数据库字符集生效）"""
    try:
        with SessionLocal() as db:
            db.execute(text("UPDATE alliances SET description=:d WHERE id=:id"), {"d": "中文演示", "id": aid})
            db.commit()
        return ok({"id": aid, "fixed": True})
    except Exception as e:
        return error("server_error", message=str(e))
