"""村庄相关接口

提供村庄列表与创建能力，支持按服务器或账号筛选。
"""
from flask import Blueprint, request
from utils.req import get_json
from utils.resp import ok, error
from db import SessionLocal
from models import Village

bp = Blueprint("villages", __name__)

@bp.get("/api/v1/villages")
def list_villages():
    """列出村庄（可筛选）

    参数（Query）：
    - `serverId`：按服务器筛选（可选）
    - `gameAccountId`：按账号筛选（可选）

    返回：
    - 成功：`{ success: true, data: Array<{id,serverId,gameAccountId,name,x,y}>, count }`
    - 失败：统一错误结构
    """
    serverId_raw = request.args.get("serverId")
    gameAccountId_raw = request.args.get("gameAccountId")
    serverId = None
    gameAccountId = None
    if serverId_raw is not None:
        try:
            serverId = int(serverId_raw)
        except Exception:
            return error("bad_request", message="serverId_invalid", status=400)
    if gameAccountId_raw is not None:
        try:
            gameAccountId = int(gameAccountId_raw)
        except Exception:
            return error("bad_request", message="gameAccountId_invalid", status=400)
    with SessionLocal() as db:
        q = db.query(Village)
        if serverId is not None:
            q = q.filter(Village.server_id == serverId)
        if gameAccountId is not None:
            q = q.filter(Village.game_account_id == gameAccountId)
        rows = q.all()
        return ok([
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
    """创建村庄

    参数（JSON）：
    - `serverId`：服务器 ID
    - `gameAccountId`：账号 ID
    - `name`：村庄名
    - `x`、`y`：坐标

    返回：新建村庄对象 `{ id, serverId, gameAccountId, name, x, y }`
    """
    data = get_json()
    v = Village(server_id=int(data.get("serverId")), game_account_id=int(data.get("gameAccountId")), name=str(data.get("name")), x=int(data.get("x")), y=int(data.get("y")))
    with SessionLocal() as db:
        db.add(v)
        db.commit()
        db.refresh(v)
        return ok({"id": v.id, "serverId": v.server_id, "gameAccountId": v.game_account_id, "name": v.name, "x": v.x, "y": v.y})