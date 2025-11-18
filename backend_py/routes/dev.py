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
        def _put(path, payload):
            r = requests.put(base + path, json=payload)
            try:
                return r.status_code, r.json()
            except Exception:
                return r.status_code, {"raw": r.text}
        def _delete(path):
            r = requests.delete(base + path)
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
        def _put(path, payload):
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json; charset=utf-8"}, method="PUT")
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
        def _delete(path):
            req = urllib.request.Request(base + path, method="DELETE")
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
    results["health"] = {"status": _get("/health")[0]}
    results["healthz"] = {"status": _get("/healthz")[0]}
    results["db_ping"] = {"status": _get("/db/ping")[0]}
    # servers
    sc, s = _post("/servers", {"code": "com-pyreq-" + ts, "region": "CN", "speed": "x1", "startDate": "2025-11-20"})
    results["servers"] = {"status": sc, "resp": s}
    sid = s.get("data", {}).get("id")
    # tribes
    short = ts[-8:]
    sc, t = _post("/tribes", {"code": "PRM" + short, "name": "罗马部落"})
    results["tribes"] = {"status": sc, "resp": t}
    tid = t.get("data", {}).get("id")
    # accounts
    sc, a = _post("/accounts", {"userId": uid, "serverId": sid, "tribeId": tid, "inGameName": "账号-" + ts})
    results["accounts"] = {"status": sc, "resp": a}
    aid = a.get("data", {}).get("id")
    # villages
    sc, v = _post("/villages", {"serverId": sid, "gameAccountId": aid, "name": "村庄-" + ts, "x": 110, "y": -50})
    results["villages"] = {"status": sc, "resp": v}
    vid = v.get("data", {}).get("id")
    # troop types
    sc, tt1 = _post("/troop-types", {"tribeId": tid, "code": "T1-" + ts, "name": "步兵-" + ts})
    sc, tt2 = _post("/troop-types", {"tribeId": tid, "code": "T2-" + ts, "name": "骑兵-" + ts})
    results["troop_types"] = {"status": 201, "resp": [tt1, tt2]}
    sc, tlist = _get("/troop-types?tribeId=" + str(tid))
    results["troop_types_list"] = {"status": sc, "resp": tlist}
    try:
        ids = [x.get("id") for x in tlist.get("data", []) if x.get("code") in ["T1-" + ts, "T2-" + ts]]
    except Exception:
        ids = []
    if len(ids) >= 2 and vid:
        counts = {str(ids[0]): 200, str(ids[1]): 150}
        sc, up = _post("/troops/upload", {"villageId": vid, "counts": counts})
        results["troops_upload"] = {"status": sc, "resp": up}
        sc, ag = _get("/troops/aggregate?villageId=" + str(vid))
        results["troops_aggregate"] = {"status": sc, "resp": ag}
        sc, pu = _post("/troops/parse-upload", {"villageId": vid, "html": "<span>100 200</span>"})
        results["troops_parse"] = {"status": sc, "resp": pu}
    # alliances
    sc, al = _post("/alliances", {"serverId": sid, "name": "联盟-" + ts, "tag": "联", "description": "中文演示", "createdBy": uid})
    results["alliances"] = {"status": sc, "resp": al}
    alid = al.get("data", {}).get("id")
    if alid:
        scg, alget = _get("/alliances/" + str(alid))
        results["alliances_get"] = {"status": scg, "resp": alget}
        sc, mem_add = _post("/alliances/" + str(alid) + "/members", {"gameAccountId": aid, "role": "member"})
        results["alliances_member_add"] = {"status": sc, "resp": mem_add}
        sc, mem_list = _get("/alliances/" + str(alid) + "/members")
        results["alliances_member_list"] = {"status": sc, "resp": mem_list}
        try:
            mid = mem_add.get("data", {}).get("id")
        except Exception:
            mid = None
        if mid:
            sc, mem_up = _put("/alliances/" + str(alid) + "/members/" + str(mid), {"role": "leader", "joinStatus": "active"})
            results["alliances_member_update"] = {"status": sc, "resp": mem_up}
            sc, mem_del = _delete("/alliances/" + str(alid) + "/members/" + str(mid))
            results["alliances_member_delete"] = {"status": sc, "resp": mem_del}
    # troops params
    sc, tp = _get("/troops/params?version=1.46&speed=3x")
    results["troops_params"] = {"status": sc, "resp": tp}
    # negative
    sc, bad = _get("/alliances?serverId=abc")
    results["alliances_bad"] = {"status": sc, "resp": bad}
    sc, inv = _get("/alliances/999999")
    results["alliances_not_found"] = {"status": sc, "resp": inv}
    sc, tp_bad = _get("/troops/params?version=0&speed=3x")
    results["troops_params_bad"] = {"status": sc, "resp": tp_bad}
    sc, srv_bad = _post("/servers", {})
    results["servers_bad"] = {"status": sc, "resp": srv_bad}
    sc, al_bad = _post("/alliances", {"serverId": sid})
    results["alliances_bad_post"] = {"status": sc, "resp": al_bad}
    sc, sl = _get("/servers")
    results["servers_list"] = {"status": sc, "resp": sl}
    sc, ul = _get("/users")
    results["users_list"] = {"status": sc, "resp": ul}
    sc, tl = _get("/tribes")
    results["tribes_list"] = {"status": sc, "resp": tl}
    sc, vl = _get("/villages?serverId=" + str(sid))
    results["villages_list"] = {"status": sc, "resp": vl}
    sc, alql = _get("/alliances?serverId=" + str(sid))
    results["alliances_query_list"] = {"status": sc, "resp": alql}
    sc, acl = _get("/accounts?serverId=" + str(sid))
    results["accounts_list"] = {"status": sc, "resp": acl}
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
