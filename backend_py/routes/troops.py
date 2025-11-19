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
from utils.req import get_json
from utils.resp import ok, error
import pkgutil
from db import SessionLocal
from models import TroopCount, TroopType, Village, GameAccount
import os
import json
import urllib.request
import io
from PIL import Image, ImageOps
import pytesseract
import numpy as np
import imagehash

bp = Blueprint("troops", __name__)

@bp.post("/api/v1/troops/upload")
def upload_troops():
    """上传兵种数量

    请求体：`{ villageId: number, counts: { [troopTypeId]: number } }`
    将各兵种数量写入 `troop_counts` 表（存在则更新，否则插入）。
    """
    data = get_json()
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
    data = get_json()
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

@bp.post("/api/v1/troops/parse-image")
def parse_image_troops():
    file = request.files.get("file")
    if not file:
        return error("bad_request", message="file_missing", status=400)
    gameAccountId_raw = request.form.get("gameAccountId")
    tribeId_raw = request.form.get("tribeId")
    write_flag = str(request.form.get("write" or "0")).strip() in ("1", "true", "True")
    gameAccountId = None
    tribeId = None
    if gameAccountId_raw:
        try:
            gameAccountId = int(gameAccountId_raw)
        except Exception:
            return error("bad_request", message="gameAccountId_invalid", status=400)
    if tribeId_raw:
        try:
            tribeId = int(tribeId_raw)
        except Exception:
            return error("bad_request", message="tribeId_invalid", status=400)
    with SessionLocal() as db:
        acc = None
        if gameAccountId is not None:
            acc = db.query(GameAccount).filter(GameAccount.id == gameAccountId).first()
            if not acc:
                return error("bad_request", message="account_not_found", status=400)
            tribeId = acc.tribe_id
        # 若暂未确定部落，先不报错，后续根据表头图标猜测
        type_ids = []
        if tribeId is not None:
            types = db.query(TroopType).filter(TroopType.tribe_id == tribeId).order_by(TroopType.id.asc()).all()
            type_ids = [int(t.id) for t in types]
        villages_by_name = {}
        if acc:
            vlist = db.query(Village).filter(Village.game_account_id == acc.id).all()
            villages_by_name = {str(v.name).strip(): int(v.id) for v in vlist}
    b = file.read()
    img = Image.open(io.BytesIO(b)).convert("L")
    img = ImageOps.autocontrast(img)
    data = pytesseract.image_to_data(img, lang="chi_sim+eng", config="--psm 6", output_type=pytesseract.Output.DICT)
    rows = {}
    n = len(data.get("text", []))
    for i in range(n):
        txt = (data["text"][i] or "").strip()
        conf = data.get("conf", ["0"])[i]
        try:
            c = float(conf)
        except Exception:
            c = -1.0
        if not txt:
            continue
        if c < 0:
            continue
        ln = data.get("line_num", [0])[i]
        if ln not in rows:
            rows[ln] = []
        rows[ln].append({
            "txt": txt,
            "left": int(data.get("left", [0])[i] or 0),
            "top": int(data.get("top", [0])[i] or 0),
            "width": int(data.get("width", [0])[i] or 0),
            "height": int(data.get("height", [0])[i] or 0)
        })
    out_rows = []
    def is_num(s):
        return bool(re.match(r"^\d+$", s))
    for ln, tokens in sorted(rows.items(), key=lambda x: x[0]):
        joined = "".join([t["txt"] for t in tokens])
        if any(x in joined for x in ["總和", "总和", "總計", "总计"]):
            continue
        nums = [int(t["txt"]) for t in tokens if is_num(t["txt"])]
        if not nums:
            continue
        name_tokens = []
        for t in tokens:
            if not is_num(t["txt"]):
                name_tokens.append(t["txt"])
            else:
                break
        vname = "".join(name_tokens).strip()
        if not vname:
            vname = None
        # 记录本行的数字列中心位置与文本高度用于后续图标识别
        num_centers = []
        text_h = 0
        for t in tokens:
            if is_num(t["txt"]):
                cx = t["left"] + t["width"] // 2
                num_centers.append(cx)
                text_h = max(text_h, int(t["height"]))
        # 仅在 tribe 未明确时，尝试通过表头图标猜测
        tribe_guess_id = None
        tribe_guess_conf = None
        if tribeId is None:
            try:
                if tokens:
                    row_top = min([t["top"] for t in tokens])
                    band_h = int(text_h * 2)
                    header_y = max(0, row_top - band_h)
                    # 先尝试整条表头带的匹配（与 resource/*.png 比较）
                    min_x = min([t["left"] for t in tokens])
                    max_x = max([t["left"] + t["width"] for t in tokens])
                    margin = int(text_h * 2)
                    x0_band = max(0, min_x - margin)
                    y0_band = header_y
                    x1_band = min(img.width, max_x + margin)
                    y1_band = min(img.height, header_y + max(int(text_h * 1.8), 24))
                    header_band = None
                    if x1_band > x0_band and y1_band > y0_band:
                        header_band = img.crop((x0_band, y0_band, x1_band, y1_band))
                        tid_band, conf_band = _guess_tribe_by_sprite_band(header_band)
                    if tid_band is not None:
                        tribe_guess_id, tribe_guess_conf = tid_band, conf_band
                        tribeId = int(tribe_guess_id)
                        if not type_ids:
                            # 获取该部落兵种顺序
                            with SessionLocal() as db2:
                                types2 = db2.query(TroopType).filter(TroopType.tribe_id == tribeId).order_by(TroopType.id.asc()).all()
                                type_ids = [int(t.id) for t in types2]
                    # 若整带不确定，再尝试按列图标小块匹配
                    patches = []
                    icon_size = max(16, int(text_h * 1.4))
                    for cx in num_centers:
                        x0 = max(0, cx - icon_size // 2)
                        y0 = header_y
                        x1 = min(img.width, x0 + icon_size)
                        y1 = min(img.height, y0 + icon_size)
                        if x1 > x0 and y1 > y0:
                            patches.append(img.crop((x0, y0, x1, y1)))
                    tribe_guess_id, tribe_guess_conf = _guess_tribe_by_icons(patches)
                    if tribe_guess_id is not None:
                        tribeId = int(tribe_guess_id)
                        if not type_ids:
                            with SessionLocal() as db2:
                                types2 = db2.query(TroopType).filter(TroopType.tribe_id == tribeId).order_by(TroopType.id.asc()).all()
                                type_ids = [int(t.id) for t in types2]
            except Exception:
                pass
        counts_map = {}
        for idx, tid in enumerate(type_ids):
            if idx < len(nums):
                counts_map[int(tid)] = int(nums[idx])
            else:
                counts_map[int(tid)] = 0
        vid = None
        if vname and vname in villages_by_name:
            vid = villages_by_name[vname]
        out_rows.append({"villageId": vid, "villageName": vname, "counts": counts_map})
    if write_flag:
        with SessionLocal() as db:
            for r in out_rows:
                vid = r.get("villageId")
                if not vid:
                    continue
                for tid, cnt in r.get("counts", {}).items():
                    existing = db.query(TroopCount).filter(TroopCount.village_id == int(vid), TroopCount.troop_type_id == int(tid)).first()
                    if existing:
                        existing.count = int(cnt)
                    else:
                        db.add(TroopCount(village_id=int(vid), troop_type_id=int(tid), count=int(cnt)))
            db.commit()
    return ok({"rows": out_rows, "written": bool(write_flag), "tribeId": tribeId, "gameAccountId": gameAccountId})

def _guess_tribe_by_sprite_band(band_img):
    # 归一尺寸
    try:
        W, H = 256, 64
        band = band_img.resize((W, H))
        band_h = imagehash.phash(band)
    except Exception:
        return None, None
    # 资源目录候选
    candidates = {
        1: ["roman_small.png", "roman.png"],
        2: ["teuton_small.png", "teutons.png"],
        3: ["gaul_small.png", "gauls.png"],
        6: ["egyptian_small.png", "egyptians.png"],
        7: ["hun_small.png", "huns.png"],
        8: ["spartan_small.png", "spartan.png"]
    }
    base_dirs = []
    # repo 根的 resource
    base_dirs.append(os.path.abspath(os.path.join(os.getcwd(), "resource")))
    # 后端工作目录下的 resource（容器）
    base_dirs.append(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "resource")))
    base_dirs.append(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "resource")))
    scores = {}
    found_any = False
    for tid, names in candidates.items():
        best = None
        for bd in base_dirs:
            for nm in names:
                p = os.path.join(bd, nm)
                if os.path.exists(p):
                    try:
                        im = Image.open(p).convert("L").resize((W, H))
                        h = imagehash.phash(im)
                        d = band_h - h
                        best = d if (best is None or d < best) else best
                        found_any = True
                    except Exception:
                        continue
        if best is not None:
            scores[tid] = best
    if not found_any or not scores:
        return None, None
    best_tid = min(scores.keys(), key=lambda k: scores[k])
    return best_tid, scores[best_tid]

def _guess_tribe_by_icons(patches):
    base = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "icons"))
    candidates = {
        1: "roman",
        2: "teutons",
        3: "gauls",
        6: "egyptians",
        7: "huns"
    }
    # 加载模板哈希
    tpl = {}
    for tid, name in candidates.items():
        d = os.path.join(base, f"tribe_{tid}_{name}")
        arr = []
        if os.path.isdir(d):
            for fn in os.listdir(d):
                p = os.path.join(d, fn)
                try:
                    im = Image.open(p).convert("L")
                    arr.append(imagehash.phash(im))
                except Exception:
                    continue
        if arr:
            tpl[tid] = arr
    if not tpl:
        return None, None
    # 计算每个补丁与模板的最小距离并汇总
    scores = {}
    for tid, arr in tpl.items():
        dsum = 0
        cnt = 0
        for patch in patches:
            try:
                h = imagehash.phash(patch)
                dist = min([h - th for th in arr]) if arr else 64
            except Exception:
                dist = 64
            dsum += dist
            cnt += 1
        if cnt > 0:
            scores[tid] = dsum / float(cnt)
    if not scores:
        return None, None
    # 距离越小越匹配
    best_tid = min(scores.keys(), key=lambda k: scores[k])
    return best_tid, scores[best_tid]

@bp.post("/api/v1/troops/parse-upload")
def parse_upload_troops():
    """解析网页片段并写入兵种数量"""
    data = get_json()
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