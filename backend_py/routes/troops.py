"""兵种相关接口

提供以下能力：
- 上传指定村庄的兵种数量并持久化
- 汇总某村庄的兵种数量
- 维护并创建兵种类型（按部落）
- 从 Travian 网页片段解析兵种数量并写入
- 获取兵种参数（支持倍速缩放）
"""
import re
from flask import Blueprint, request, send_file
from utils.resp import ok, error
import pkgutil
from db import SessionLocal
from models import TroopCount, TroopType, Village, GameAccount
import os
import json
import urllib.request

bp = Blueprint("troops", __name__)

@bp.post("/api/v1/troops/upload")
def upload_troops():
    """上传兵种数量

    请求体：`{ villageId: number, counts: { [troopTypeId]: number } }`
    将各兵种数量写入 `troop_counts` 表（存在则更新，否则插入）。
    """
    data = request.get_json(force=True)
    villageId = int(data.get("villageId"))
    counts = data.get("counts", {})
    with SessionLocal() as db:
        for k, v in counts.items():
            k_int = int(k)
            v_int = int(v)
            # 查找现有记录并更新数量
            existing = db.query(TroopCount).filter(TroopCount.village_id == villageId, TroopCount.troop_type_id == k_int).first()
            if existing:
                existing.count = v_int
            else:
                db.add(TroopCount(village_id=villageId, troop_type_id=k_int, count=v_int))
        db.commit()
    return ok({"written": True})

@bp.get("/api/v1/troops/aggregate")
def troops_aggregate():
    """汇总村庄兵种数量

    查询参数：`villageId`
    返回：`{ troopTypeId: count }`
    """
    villageId = request.args.get("villageId", type=int)
    with SessionLocal() as db:
        rows = db.query(TroopCount).filter(TroopCount.village_id == villageId).all()
        return ok({int(r.troop_type_id): int(r.count) for r in rows})

@bp.get("/api/v1/troop-types")
def list_troop_types():
    """列出兵种类型（可按部落过滤）"""
    tribeId = request.args.get("tribeId", type=int)
    with SessionLocal() as db:
        q = db.query(TroopType)
        if tribeId is not None:
            q = q.filter(TroopType.tribe_id == tribeId)
        rows = q.all()
        return ok([
            {"id": r.id, "tribeId": r.tribe_id, "code": r.code, "name": r.name}
            for r in rows
        ])

@bp.post("/api/v1/troop-types")
def create_troop_type():
    """创建兵种类型"""
    data = request.get_json(force=True)
    tribeId = data.get("tribeId")
    code = data.get("code")
    name = data.get("name")
    if not tribeId or not code or not name:
        return error("bad_request", message="missing_fields", status=400)
    with SessionLocal() as db:
        tt = TroopType(tribe_id=int(tribeId), code=str(code), name=str(name))
        db.add(tt)
        db.commit()
        db.refresh(tt)
        return ok({"id": tt.id, "tribeId": tt.tribe_id, "code": tt.code, "name": tt.name})

def _parse_travian_html_to_counts(html: str, tribe_types: list):
    """从网页片段解析兵种数量

    简化策略：
    - 去除所有 HTML 标签，仅保留文本
    - 抽取文本中的数字序列
    - 按 `tribe_types` 的顺序，将数字映射到对应 `troop_type_id`
    """
    text = re.sub(r"<[^>]+>", " ", html)
    nums = [int(x) for x in re.findall(r"\b\d+\b", text)]
    counts = {}
    for i, t in enumerate(tribe_types):
        if i < len(nums):
            counts[int(t.id)] = int(nums[i])
    return counts

@bp.post("/api/v1/troops/parse-upload")
def parse_upload_troops():
    """解析网页片段并写入兵种数量"""
    data = request.get_json(force=True)
    villageId = int(data.get("villageId"))
    html = data.get("html") or ""
    with SessionLocal() as db:
        # 校验村庄与其所属账号
        v = db.query(Village).filter(Village.id == villageId).first()
        if not v:
            return error("bad_request", message="village_not_found", status=400)
        acc = db.query(GameAccount).filter(GameAccount.id == v.game_account_id).first()
        if not acc:
            return error("bad_request", message="account_not_found", status=400)
        # 按账号部落获取兵种类型并解析数字
        types = db.query(TroopType).filter(TroopType.tribe_id == acc.tribe_id).order_by(TroopType.id.asc()).all()
        parsed = _parse_travian_html_to_counts(html, types)
        # 批量写入
        for tid, cnt in parsed.items():
            existing = db.query(TroopCount).filter(TroopCount.village_id == villageId, TroopCount.troop_type_id == int(tid)).first()
            if existing:
                existing.count = int(cnt)
            else:
                db.add(TroopCount(village_id=villageId, troop_type_id=int(tid), count=int(cnt)))
        db.commit()
        return ok({"parsed": parsed, "written": True})

@bp.get("/api/v1/troops/params")
def troops_params():
    """获取兵种参数（支持倍速缩放）

    - 读取本地/环境/远程数据源，获得基础 `1x` 数据
    - 若 `speed>1`，根据预设规则缩放 `speed/time/rs_time`
    """
    debug = request.args.get("debug") == "1"
    version = request.args.get("version", "1.46")
    speed_str = request.args.get("speed", "1x")
    m = re.match(r"^(\d+)x$", speed_str)
    speed = int(m.group(1)) if m else 1

    def load_base():
        """加载基础 1x 兵种数据（优先级：环境路径 → 包内资源 → 常见路径 → 远程 URL）"""
        env_path = os.getenv("TROOPS_PARAMS_PATH")
        if env_path and os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                try:
                    with open(env_path, "r", encoding="utf-8-sig") as f:
                        return json.load(f)
                except Exception:
                    pass
        try:
            data_bytes = pkgutil.get_data('backend_py', 'data/troops_t4.6_1x.json')
            if data_bytes:
                return json.loads(data_bytes.decode('utf-8'))
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
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    try:
                        with open(p, "r", encoding="utf-8-sig") as f:
                            return json.load(f)
                    except Exception:
                        continue
        try:
            url = os.getenv("TROOPS_PARAMS_URL") or "https://raw.githubusercontent.com/chengleyi/happy4travian/main/backend_py/data/troops_t4.6_1x.json"
            with urllib.request.urlopen(url, timeout=10) as r:
                txt = r.read().decode("utf-8")
                return json.loads(txt)
        except Exception:
            return None

    base_data = load_base()
    if not base_data:
        if debug:
            return error("not_found", message="base_data_none", status=404)
        return error("not_found", status=404)
    if version != "1.46":
        return error("not_found", status=404)
    if speed <= 1:
        return ok(base_data)

    def scale(d, k):
        """按倍速缩放单位属性（速度乘以系数、训练/研究时间按倍速除以 k）"""
        out = {"version": d.get("version"), "speed": f"{k}x", "tribes": []}
        spd_map = {1:1, 2:2, 3:2, 5:2, 10:4}
        spd_factor = spd_map.get(k, 1)
        for t in d.get("tribes", []):
            tribe_out = {"tribeId": t.get("tribeId"), "tribeLabel": t.get("tribeLabel"), "units": []}
            for u in t.get("units", []):
                u2 = dict(u)
                if isinstance(u2.get("speed"), (int, float)):
                    u2["speed"] = int(round(u2["speed"] * spd_factor))
                if isinstance(u2.get("time"), (int, float)):
                    u2["time"] = int(round(u2["time"] / k))
                if isinstance(u2.get("rs_time"), (int, float)):
                    u2["rs_time"] = int(round(u2["rs_time"] / k))
                tribe_out["units"].append(u2)
            out["tribes"].append(tribe_out)
        return out

    return ok(scale(base_data, speed))