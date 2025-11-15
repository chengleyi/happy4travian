import re
from flask import Blueprint, jsonify, request
import pkgutil
from db import SessionLocal
from models import TroopCount, TroopType, Village, GameAccount
import os
import json
import urllib.request

bp = Blueprint("troops", __name__)

@bp.post("/api/v1/troops/upload")
def upload_troops():
    data = request.get_json(force=True)
    villageId = int(data.get("villageId"))
    counts = data.get("counts", {})
    with SessionLocal() as db:
        for k, v in counts.items():
            k_int = int(k)
            v_int = int(v)
            existing = db.query(TroopCount).filter(TroopCount.village_id == villageId, TroopCount.troop_type_id == k_int).first()
            if existing:
                existing.count = v_int
            else:
                db.add(TroopCount(village_id=villageId, troop_type_id=k_int, count=v_int))
        db.commit()
    return "ok"

@bp.get("/api/v1/troops/aggregate")
def troops_aggregate():
    villageId = request.args.get("villageId", type=int)
    with SessionLocal() as db:
        rows = db.query(TroopCount).filter(TroopCount.village_id == villageId).all()
        return jsonify({int(r.troop_type_id): int(r.count) for r in rows})

@bp.get("/api/v1/troop-types")
def list_troop_types():
    tribeId = request.args.get("tribeId", type=int)
    with SessionLocal() as db:
        q = db.query(TroopType)
        if tribeId is not None:
            q = q.filter(TroopType.tribe_id == tribeId)
        rows = q.all()
        return jsonify([
            {"id": r.id, "tribeId": r.tribe_id, "code": r.code, "name": r.name}
            for r in rows
        ])

@bp.post("/api/v1/troop-types")
def create_troop_type():
    data = request.get_json(force=True)
    tribeId = data.get("tribeId")
    code = data.get("code")
    name = data.get("name")
    if not tribeId or not code or not name:
        return jsonify({"error":"bad_request"}), 400
    with SessionLocal() as db:
        tt = TroopType(tribe_id=int(tribeId), code=str(code), name=str(name))
        db.add(tt)
        db.commit()
        db.refresh(tt)
        return jsonify({"id": tt.id, "tribeId": tt.tribe_id, "code": tt.code, "name": tt.name})

def _parse_travian_html_to_counts(html: str, tribe_types: list):
    text = re.sub(r"<[^>]+>", " ", html)
    nums = [int(x) for x in re.findall(r"\b\d+\b", text)]
    counts = {}
    for i, t in enumerate(tribe_types):
        if i < len(nums):
            counts[int(t.id)] = int(nums[i])
    return counts

@bp.post("/api/v1/troops/parse-upload")
def parse_upload_troops():
    data = request.get_json(force=True)
    villageId = int(data.get("villageId"))
    html = data.get("html") or ""
    with SessionLocal() as db:
        v = db.query(Village).filter(Village.id == villageId).first()
        if not v:
            return jsonify({"error":"bad_request","message":"village_not_found"}), 400
        acc = db.query(GameAccount).filter(GameAccount.id == v.game_account_id).first()
        if not acc:
            return jsonify({"error":"bad_request","message":"account_not_found"}), 400
        types = db.query(TroopType).filter(TroopType.tribe_id == acc.tribe_id).order_by(TroopType.id.asc()).all()
        parsed = _parse_travian_html_to_counts(html, types)
        for tid, cnt in parsed.items():
            existing = db.query(TroopCount).filter(TroopCount.village_id == villageId, TroopCount.troop_type_id == int(tid)).first()
            if existing:
                existing.count = int(cnt)
            else:
                db.add(TroopCount(village_id=villageId, troop_type_id=int(tid), count=int(cnt)))
        db.commit()
        return jsonify({"parsed": parsed, "written": True})

@bp.get("/api/v1/troops/params")
def troops_params():
    env_path = os.getenv("TROOPS_PARAMS_PATH")
    if env_path and os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
        except Exception:
            pass
    # Try package resource first
    try:
        data_bytes = pkgutil.get_data('backend_py', 'data/troops_t4.6_1x.json')
        if data_bytes:
            return jsonify(json.loads(data_bytes.decode('utf-8')))
    except Exception:
        pass
    candidates = []
    base = os.path.dirname(os.path.dirname(__file__))
    candidates.append(os.path.abspath(os.path.join(base, "data", "troops_t4.6_1x.json")))
    candidates.append(os.path.abspath(os.path.join(os.getcwd(), "backend_py", "data", "troops_t4.6_1x.json")))
    candidates.append(os.path.abspath(os.path.join(os.getcwd(), "data", "troops_t4.6_1x.json")))
    candidates.append("/opt/happy4travian/backend_py/data/troops_t4.6_1x.json")
    candidates.append("/opt/happy4travian/backend_py/backend_py/data/troops_t4.6_1x.json")
    for p in candidates:
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return jsonify(data)
        except Exception:
            continue
    if request.args.get("debug") == "1":
        info = {
            "cwd": os.getcwd(),
            "file": __file__,
            "env_path": env_path,
            "exists": {p: os.path.exists(p) for p in candidates}
        }
        return jsonify(info), 404
    try:
        url = os.getenv("TROOPS_PARAMS_URL") or "https://raw.githubusercontent.com/chengleyi/happy4travian/main/backend_py/data/troops_t4.6_1x.json"
        with urllib.request.urlopen(url, timeout=10) as r:
            txt = r.read().decode("utf-8")
            data = json.loads(txt)
            return jsonify(data)
    except Exception:
        pass
    return jsonify({"error": "not_found"}), 404