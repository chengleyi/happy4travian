import re
from flask import Blueprint, jsonify, request
from db import SessionLocal
from models import TroopCount, TroopType, Village, GameAccount

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