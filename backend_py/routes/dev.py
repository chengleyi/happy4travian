"""开发辅助接口

提供数据灌入与数据库迁移的触发接口，用于在服务器上快速初始化环境。
"""
from flask import Blueprint
import time
import json
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

@bp.route("/api/v1/dev/e2e-run", methods=["POST"])
def dev_e2e_run():
    """在服务器侧使用 requests 远端调用自身 API，执行 E2E 并返回汇总"""
    use_requests = True
    try:
        import requests
    except Exception:
        use_requests = False
    base = "http://127.0.0.1:8080/api/v1"
    ts = time.strftime("%Y%m%d%H%M%S", time.gmtime())
    results = {}
    if use_requests:
        def _post(path, payload):
            r = requests.post(base + path, json=payload)
            try:
                return r.status_code, r.json()
            except Exception:
                return r.status_code, {"raw": r.text}
        def _get(path):
            r = requests.get(base + path)
            try:
                return r.status_code, r.json()
            except Exception:
                return r.status_code, {"raw": r.text}
    else:
        import urllib.request
        def _post(path, payload):
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
            try:
                with urllib.request.urlopen(req) as resp:
                    sc = resp.getcode()
                    txt = resp.read().decode("utf-8", errors="replace")
                    try:
                        return sc, json.loads(txt)
                    except Exception:
                        return sc, {"raw": txt}
            except Exception as e:
                return 500, {"error": str(e)}
        def _get(path):
            req = urllib.request.Request(base + path, method="GET")
            try:
                with urllib.request.urlopen(req) as resp:
                    sc = resp.getcode()
                    txt = resp.read().decode("utf-8", errors="replace")
                    try:
                        return sc, json.loads(txt)
                    except Exception:
                        return sc, {"raw": txt}
            except Exception as e:
                return 500, {"error": str(e)}
    # users
    sc, u = _post("/users", {"nickname": "PyReqUser-" + ts})
    results["users"] = {"status": sc, "resp": u}
    uid = u.get("data", {}).get("id")
    # servers
    sc, s = _post("/servers", {"code": "com-pyreq-" + ts, "region": "CN", "speed": "x1", "startDate": "2025-11-20"})
    results["servers"] = {"status": sc, "resp": s}
    sid = s.get("data", {}).get("id")
    # tribes
    sc, t = _post("/tribes", {"code": "PYROM-" + ts, "name": "罗马部落"})
    results["tribes"] = {"status": sc, "resp": t}
    tid = t.get("data", {}).get("id")
    # accounts
    sc, a = _post("/accounts", {"userId": uid, "serverId": sid, "tribeId": tid, "inGameName": "账号-" + ts})
    results["accounts"] = {"status": sc, "resp": a}
    aid = a.get("data", {}).get("id")
    # villages
    sc, v = _post("/villages", {"serverId": sid, "gameAccountId": aid, "name": "村庄-" + ts, "x": 110, "y": -50})
    results["villages"] = {"status": sc, "resp": v}
    # alliances
    sc, al = _post("/alliances", {"serverId": sid, "name": "联盟-" + ts, "tag": "联", "description": "中文演示", "createdBy": uid})
    results["alliances"] = {"status": sc, "resp": al}
    alid = al.get("data", {}).get("id")
    if alid:
        scg, alget = _get("/alliances/" + str(alid))
        results["alliances_get"] = {"status": scg, "resp": alget}
    # troops params
    sc, tp = _get("/troops/params?version=1.46&speed=3x")
    results["troops_params"] = {"status": sc, "resp": tp}
    # negative
    sc, bad = _get("/alliances?serverId=abc")
    results["alliances_bad"] = {"status": sc, "resp": bad}
    return ok(results)

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
