"""联盟与成员接口

提供联盟的 CRUD 以及成员管理能力；部分返回自行组装 JSON 以控制格式。
"""
import json
from flask import Blueprint, request, Response
from utils.req import get_json
from utils.resp import ok, error
from db import SessionLocal, engine
from sqlalchemy import inspect
from models import Alliance, AllianceMember, GameAccount

bp = Blueprint("alliances", __name__)

@bp.get("/api/v1/alliances")
def list_alliances():
    """列出联盟（可按服务器与名称过滤）"""
    serverId_raw = request.args.get("serverId")
    name = request.args.get("name", type=str)
    serverId = None
    if serverId_raw is not None:
        try:
            serverId = int(serverId_raw)
        except Exception:
            return error("bad_request", message="serverId_invalid", status=400)
    try:
        if not inspect(engine).has_table("alliances"):
            return ok([])
        with SessionLocal() as db:
            q = db.query(Alliance)
            if serverId is not None:
                q = q.filter(Alliance.server_id == serverId)
            if name:
                q = q.filter(Alliance.name.like(f"%{name}%"))
            rows = q.all()
            data = [
                {
                    "id": r.id,
                    "serverId": r.server_id,
                    "name": r.name,
                    "tag": r.tag,
                    "description": r.description,
                    "createdBy": r.created_by,
                    "createdAt": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
            body = {"success": True, "count": len(data), "data": data}
            return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json")
    except Exception as e:
        err = {"success": False, "error": "server_error", "message": str(e)}
        return Response(json.dumps(err, ensure_ascii=False, indent=2), mimetype="application/json"), 500

@bp.get("/api/v1/alliances/<int:aid>")
def get_alliance(aid: int):
    """获取单个联盟详情"""
    try:
        if not inspect(engine).has_table("alliances"):
            body = {"success": False, "error": "not_found"}
            return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json"), 404
        with SessionLocal() as db:
            r = db.query(Alliance).filter(Alliance.id == aid).first()
            if not r:
                body = {"success": False, "error": "not_found"}
                return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json"), 404
            data = {
                "id": r.id,
                "serverId": r.server_id,
                "name": r.name,
                "tag": r.tag,
                "description": r.description,
                "createdBy": r.created_by,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
            }
            body = {"success": True, "data": data}
            return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json")
    except Exception as e:
        err = {"success": False, "error": "server_error", "message": str(e)}
        return Response(json.dumps(err, ensure_ascii=False, indent=2), mimetype="application/json"), 500

@bp.post("/api/v1/alliances")
def create_alliance():
    """创建联盟"""
    data = get_json()
    serverId = data.get("serverId")
    name = data.get("name")
    tag = data.get("tag")
    description = data.get("description")
    createdBy = data.get("createdBy")
    if not serverId or not name or not tag or not createdBy:
        body = {"success": False, "error": "bad_request", "message": "missing_fields"}
        return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json"), 400
    a = Alliance(server_id=int(serverId), name=str(name), tag=str(tag), description=str(description) if description else None, created_by=int(createdBy))
    with SessionLocal() as db:
        db.add(a)
        db.commit()
        db.refresh(a)
        body = {
            "success": True,
            "data": {
                "id": a.id,
                "serverId": a.server_id,
                "name": a.name,
                "tag": a.tag,
                "description": a.description,
                "createdBy": a.created_by,
                "createdAt": a.created_at.isoformat() if a.created_at else None,
            }
        }
        return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json")

@bp.put("/api/v1/alliances/<int:aid>")
def update_alliance(aid: int):
    """更新联盟基本信息"""
    data = get_json()
    with SessionLocal() as db:
        a = db.query(Alliance).filter(Alliance.id == aid).first()
        if not a:
            return error("not_found", status=404)
        if "name" in data and data["name"]:
            a.name = str(data["name"])
        if "tag" in data and data["tag"]:
            a.tag = str(data["tag"])
        if "description" in data:
            a.description = str(data["description"]) if data["description"] is not None else None
        db.commit()
        db.refresh(a)
        return ok({
            "id": a.id,
            "serverId": a.server_id,
            "name": a.name,
            "tag": a.tag,
            "description": a.description,
            "createdBy": a.created_by,
            "createdAt": a.created_at.isoformat() if a.created_at else None,
        })

@bp.delete("/api/v1/alliances/<int:aid>")
def delete_alliance(aid: int):
    """删除联盟"""
    with SessionLocal() as db:
        a = db.query(Alliance).filter(Alliance.id == aid).first()
        if not a:
            return error("not_found", status=404)
        db.delete(a)
        db.commit()
        return ok({"deleted": True})

@bp.get("/api/v1/alliances/<int:aid>/members")
def list_alliance_members(aid: int):
    """列出联盟成员"""
    try:
        with SessionLocal() as db:
            rows = db.query(AllianceMember).filter(AllianceMember.alliance_id == aid).all()
            data = [
                {
                    "id": r.id,
                    "allianceId": r.alliance_id,
                    "gameAccountId": r.game_account_id,
                    "serverId": r.server_id,
                    "role": r.role,
                    "joinStatus": r.join_status,
                    "joinedAt": r.joined_at.isoformat() if r.joined_at else None,
                }
                for r in rows
            ]
            body = {"success": True, "count": len(data), "data": data}
            return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json")
    except Exception as e:
        err = {"success": False, "error": "server_error", "message": str(e)}
        return Response(json.dumps(err, ensure_ascii=False, indent=2), mimetype="application/json"), 500

@bp.post("/api/v1/alliances/<int:aid>/members")
def add_alliance_member(aid: int):
    """添加联盟成员"""
    data = get_json()
    gameAccountId = data.get("gameAccountId")
    role = data.get("role") or "member"
    with SessionLocal() as db:
        acc = db.query(GameAccount).filter(GameAccount.id == int(gameAccountId)).first()
        if not acc:
            body = {"success": False, "error": "bad_request", "message": "account_not_found"}
            return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json"), 400
        m = AllianceMember(alliance_id=aid, game_account_id=acc.id, server_id=acc.server_id, role=str(role), join_status="active")
        db.add(m)
        db.commit()
        db.refresh(m)
        body = {"success": True, "data": {
            "id": m.id,
            "allianceId": m.alliance_id,
            "gameAccountId": m.game_account_id,
            "serverId": m.server_id,
            "role": m.role,
            "joinStatus": m.join_status,
            "joinedAt": m.joined_at.isoformat() if m.joined_at else None,
        }}
        return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json")

@bp.put("/api/v1/alliances/<int:aid>/members/<int:mid>")
def update_alliance_member(aid: int, mid: int):
    """更新联盟成员信息"""
    data = get_json()
    with SessionLocal() as db:
        m = db.query(AllianceMember).filter(AllianceMember.id == mid, AllianceMember.alliance_id == aid).first()
        if not m:
            return error("not_found", status=404)
        if "role" in data and data["role"]:
            m.role = str(data["role"])
        if "joinStatus" in data and data["joinStatus"]:
            m.join_status = str(data["joinStatus"])
        db.commit()
        db.refresh(m)
        return ok({
            "id": m.id,
            "allianceId": m.alliance_id,
            "gameAccountId": m.game_account_id,
            "serverId": m.server_id,
            "role": m.role,
            "joinStatus": m.join_status,
            "joinedAt": m.joined_at.isoformat() if m.joined_at else None,
        })

@bp.delete("/api/v1/alliances/<int:aid>/members/<int:mid>")
def delete_alliance_member(aid: int, mid: int):
    """删除联盟成员"""
    with SessionLocal() as db:
        m = db.query(AllianceMember).filter(AllianceMember.id == mid, AllianceMember.alliance_id == aid).first()
        if not m:
            return error("not_found", status=404)
        db.delete(m)
        db.commit()
        return ok({"deleted": True})