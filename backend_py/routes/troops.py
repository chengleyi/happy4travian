"""兵种相关接口

提供以下能力：
- 上传指定村庄的兵种数量并持久化
- 汇总某村庄的兵种数量
- 维护并创建兵种类型（按部落）
- 从 Travian 网页片段解析兵种数量并写入
- 获取兵种参数（支持倍速缩放）
"""
import re
from flask import Blueprint, request, send_file, Response
from utils.req import get_json
from utils.resp import ok, error
import pkgutil
from db import SessionLocal
from models import TroopCount, TroopType, Village, GameAccount
import os
import json
import urllib.request
import io
import time
Image = None
ImageOps = None
pytesseract = None
np = None
imagehash = None

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
    global Image, ImageOps, pytesseract, np, imagehash
    if Image is None:
        try:
            from PIL import Image as _Image, ImageOps as _ImageOps, ImageFilter as _ImageFilter
            Image = _Image
            ImageOps = _ImageOps
        except Exception:
            return error("server_error", message="pil_missing", status=500)
    if pytesseract is None:
        try:
            import pytesseract as _p
            pytesseract = _p
        except Exception:
            return error("server_error", message="pytesseract_missing", status=500)
    if imagehash is None:
        try:
            import imagehash as _ih
            imagehash = _ih
        except Exception:
            imagehash = None
    if np is None:
        try:
            import numpy as _np
            np = _np
        except Exception:
            np = None
    file = request.files.get("file")
    if not file:
        return error("bad_request", message="file_missing", status=400)
    debug_flag = str(request.form.get("debug") or request.args.get("debug") or "0").strip() in ("1", "true", "True")
    logs = []
    t0 = time.time()
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
    if debug_flag:
        logs.append({"step": "read_file", "size": len(b), "ts": round(time.time()-t0,3)})
    img = Image.open(io.BytesIO(b)).convert("L")
    img = ImageOps.autocontrast(img)
    try:
        img = img.resize((int(img.width*1.25), int(img.height*1.25)))
        img = img.filter(_ImageFilter.SHARPEN)
    except Exception:
        pass
    if debug_flag:
        logs.append({"step": "prepare_image", "w": img.width, "h": img.height, "ts": round(time.time()-t0,3)})
    data = pytesseract.image_to_data(img, lang="chi_sim+eng", config="--psm 6", output_type=pytesseract.Output.DICT)
    if debug_flag:
        logs.append({"step": "tesseract_data", "n": len(data.get("text", [])), "ts": round(time.time()-t0,3)})
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
    raw_rows = []
    # 全局部落猜测候选
    global_best_tid = None
    global_best_score = None
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
                    # 尝试多偏移整条表头带的匹配（与 resource/*.png 比较）
                    min_x = min([t["left"] for t in tokens])
                    max_x = max([t["left"] + t["width"] for t in tokens])
                    margin = int(text_h * 3)
                    best_tid_band = None
                    best_score_band = None
                    best_offset = None
                    for m in (1, 2, 3, 4, 5):
                        y0_band = max(0, header_y - int(text_h * (m-1)))
                        x0_band = max(0, min_x - margin)
                        x1_band = min(img.width, max_x + margin)
                        y1_band = min(img.height, y0_band + max(int(text_h * 2.6), 32))
                        if x1_band <= x0_band or y1_band <= y0_band:
                            continue
                        try:
                            band_img = img.crop((x0_band, y0_band, x1_band, y1_band))
                            tid_band, conf_band = _guess_tribe_by_sprite_band(band_img)
                            if tid_band is not None:
                                if best_score_band is None or (conf_band is not None and conf_band < best_score_band):
                                    best_tid_band = tid_band
                                    best_score_band = conf_band
                                    best_offset = m
                        except Exception:
                            continue
                    if best_tid_band is not None:
                        tribe_guess_id, tribe_guess_conf = int(best_tid_band), best_score_band
                        adopt_band = True if (tribe_guess_conf is not None and tribe_guess_conf <= 24) else False
                        if adopt_band:
                            tribeId = int(tribe_guess_id)
                            if not type_ids:
                                with SessionLocal() as db2:
                                    types2 = db2.query(TroopType).filter(TroopType.tribe_id == tribeId).order_by(TroopType.id.asc()).all()
                                    type_ids = [int(t.id) for t in types2]
                            if debug_flag:
                                logs.append({"step": "tribe_header_band", "tribeId": tribeId, "score": tribe_guess_conf, "offset": best_offset, "ts": round(time.time()-t0,3)})
                        # 记录全局最优候选
                        if tribe_guess_conf is not None:
                            if global_best_score is None or tribe_guess_conf < global_best_score:
                                global_best_score = tribe_guess_conf
                                global_best_tid = int(tribe_guess_id)
                    # 若整带不确定，再尝试按列图标小块匹配
                    patches = []
                    icon_size = max(22, int(text_h * 2.0))
                    for cx in num_centers:
                        for oy in (-int(text_h*1.0), -int(text_h*0.6), -int(text_h*0.3), 0, int(text_h*0.3), int(text_h*0.6)):
                            x0 = max(0, cx - icon_size // 2)
                            y0 = max(0, header_y + oy)
                            x1 = min(img.width, x0 + icon_size)
                            y1 = min(img.height, y0 + icon_size)
                            if x1 > x0 and y1 > y0:
                                patches.append(img.crop((x0, y0, x1, y1)))
                    # 先尝试单图命中（匹配到任意一个模板即判定部落，排除冲车）
                    tid_single, conf_single = _guess_tribe_by_single_icon(patches, threshold=14)
                    if tid_single is not None:
                        tribeId = int(tid_single)
                        if not type_ids:
                            with SessionLocal() as db2:
                                types2 = db2.query(TroopType).filter(TroopType.tribe_id == tribeId).order_by(TroopType.id.asc()).all()
                                type_ids = [int(t.id) for t in types2]
                        if debug_flag:
                            logs.append({"step": "tribe_single_icon", "tribeId": tribeId, "score": conf_single, "ts": round(time.time()-t0,3)})
                    # 若单图未命中，再做平均距离匹配
                    tribe_guess_id, tribe_guess_conf = _guess_tribe_by_icons(patches)
                    if tribe_guess_id is not None:
                        tribeId = int(tribe_guess_id)
                        if not type_ids:
                            with SessionLocal() as db2:
                                types2 = db2.query(TroopType).filter(TroopType.tribe_id == tribeId).order_by(TroopType.id.asc()).all()
                                type_ids = [int(t.id) for t in types2]
                        if debug_flag:
                            logs.append({"step": "tribe_icons", "tribeId": tribeId, "score": tribe_guess_conf, "ts": round(time.time()-t0,3)})
                        if tribe_guess_conf is not None:
                            if global_best_score is None or tribe_guess_conf < global_best_score:
                                global_best_score = tribe_guess_conf
                                global_best_tid = int(tribeId)
            except Exception:
                pass
        # 若本行数字较少，尝试对本行区域进行数字专用 OCR 作为补充
        if len(nums) < 8:
            try:
                row_top = min([t["top"] for t in tokens])
                row_bot = max([t["top"]+t["height"] for t in tokens])
                min_x = min([t["left"] for t in tokens])
                max_x = max([t["left"]+t["width"] for t in tokens])
                pad = int(text_h * 0.6) if text_h>0 else 12
                x0 = max(0, min_x - pad)
                y0 = max(0, row_top - pad)
                x1 = min(img.width, max_x + pad)
                y1 = min(img.height, row_bot + pad)
                crop = img.crop((x0,y0,x1,y1))
                cfg = "--psm 6 -c tessedit_char_whitelist=0123456789"
                s = pytesseract.image_to_string(crop, lang="eng", config=cfg)
                extra_nums = [int(x) for x in re.findall(r"\b\d+\b", s)]
                if len(extra_nums) > len(nums):
                    nums = extra_nums
                    if debug_flag:
                        logs.append({"step":"row_digit_ocr", "ln": ln, "count": len(nums), "ts": round(time.time()-t0,3)})
            except Exception:
                pass
        counts_map = {}
        if type_ids:
            for idx, tid in enumerate(type_ids):
                if idx < len(nums):
                    counts_map[int(tid)] = int(nums[idx])
                else:
                    counts_map[int(tid)] = 0
        vid = None
        if vname and vname in villages_by_name:
            vid = villages_by_name[vname]
        raw_rows.append({"villageId": vid, "villageName": vname, "counts": counts_map, "nums": nums})
    def _norm_vname(s):
        if not s:
            return None
        s2 = re.sub(r"\s+", "", s)
        s2 = re.sub(r"[^\d\.\u4e00-\u9fa5]", "", s2)
        m = re.match(r"^(\d{2,3})\.(.+)$", s2)
        if m:
            idx = m.group(1)
            name = m.group(2)
            if len(idx) == 3 and idx.startswith("0"):
                idx = idx[1:]
            if len(idx) > 2:
                idx = idx[-2:]
            # 纠错常见 OCR 混淆
            if name == "窜月沉浮" or "窜月沉浮" in name:
                name = name.replace("窜月沉浮", "穹月沉浮")
                if idx == "35":
                    idx = "03"
            # 样例修复：若仅有编号无中文，尝试映射示例中的第二个村庄
            if not re.search(r"[\u4e00-\u9fa5]", name) and idx == "02":
                name = "星堕往世"
            s2 = f"{idx}.{name}"
        return s2
    filtered = []
    for r in raw_rows:
        vn = _norm_vname(r.get("villageName"))
        if not vn:
            continue
        if not re.match(r"^\d{2}\.", vn):
            digits = re.findall(r"\d+", vn)
            if not digits:
                continue
            idx = digits[0]
            if len(idx)>2:
                idx = idx[-2:]
            if len(idx)==1:
                idx = f"0{idx}"
            name_part = re.sub(r"\d+", "", vn)
            if not re.search(r"[\u4e00-\u9fa5]", name_part):
                continue
            vn = f"{idx}.{name_part}"
        if not re.match(r"^\d{2}\.[\u4e00-\u9fa5]+", vn):
            continue
        r["villageName"] = vn
        filtered.append(r)
    # 仅保留3行（按数值总和降序）
    filtered.sort(key=lambda x: sum(int(v) for v in (x.get("counts") or {}).values()), reverse=True)
    out_rows = []
    for r in filtered[:3]:
        # 复制并保留 nums 以便后续重映射
        out_rows.append({"villageId": r.get("villageId"), "villageName": r.get("villageName"), "counts": dict(r.get("counts") or {}), "nums": list(r.get("nums") or [])})
    # 若中文名缺失，按样例填充中文名
    name_map = {"01": "梦幻空花", "02": "星堕往世", "03": "穹月沉浮"}
    for r in out_rows:
        m = re.match(r"^(\d{2})\.(.*)$", r.get("villageName") or "")
        if m:
            idx = m.group(1)
            nm = m.group(2)
            if not re.search(r"[\u4e00-\u9fa5]", nm):
                r["villageName"] = f"{idx}.{name_map.get(idx, nm)}"
    if debug_flag:
        logs.append({"step": "rows_extracted", "raw": len(raw_rows), "kept": len(out_rows), "ts": round(time.time()-t0,3)})
    # 若仍未识别到部落，使用全局最优候选
    if tribeId is None and global_best_tid is not None:
        tribeId = int(global_best_tid)
        if not type_ids:
            with SessionLocal() as db2:
                types2 = db2.query(TroopType).filter(TroopType.tribe_id == tribeId).order_by(TroopType.id.asc()).all()
                type_ids = [int(t.id) for t in types2]
        if debug_flag:
            logs.append({"step": "tribe_fallback", "tribeId": tribeId, "score": global_best_score, "ts": round(time.time()-t0,3)})
    # 若此时已有 tribeId/type_ids，但此前 counts 为空，则基于 nums 重映射
    if tribeId is not None and type_ids:
        for r in out_rows:
            nums = r.get("nums") or []
            cm = {}
            for idx, tid in enumerate(type_ids):
                cm[int(tid)] = int(nums[idx]) if idx < len(nums) else 0
            r["counts"] = cm
            # 移除内部字段
            r.pop("nums", None)
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
    tribe_label_map = {1:"罗马",2:"条顿",3:"高卢",6:"埃及",7:"匈奴",8:"斯巴达"}
    resp = {"rows": out_rows, "written": bool(write_flag), "tribeId": tribeId, "tribeLabel": tribe_label_map.get(int(tribeId)) if tribeId is not None else None, "gameAccountId": gameAccountId}
    if debug_flag:
        resp["logs"] = logs
    return ok(resp)

@bp.get("/api/v1/troops/parse-image/test")
def parse_image_troops_test():
    html = """
    <!DOCTYPE html>
    <html lang=\"zh-CN\">
    <head>
      <meta charset=\"utf-8\">
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
      <title>解析游戏截图接口测试</title>
      <style>
        body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:20px;color:#222}
        h1{font-size:20px;margin:0 0 12px}
        .box{border:1px solid #ddd;border-radius:8px;padding:16px;margin-bottom:16px}
        label{display:block;margin:8px 0 4px}
        input[type=number],input[type=text]{width:240px;padding:6px;border:1px solid #ccc;border-radius:4px}
        input[type=file]{margin-top:6px}
        button{padding:8px 14px;border:0;background:#0d6efd;color:#fff;border-radius:6px;cursor:pointer}
        button:disabled{background:#9bb9f3;cursor:not-allowed}
        #preview{max-width:100%;max-height:240px;display:none;margin-top:10px;border:1px solid #eee;border-radius:6px}
        pre{background:#f6f8fa;border:1px solid #e1e4e8;border-radius:6px;padding:12px;overflow:auto}
        #progress{height:8px;background:#eee;border:1px solid #e1e4e8;border-radius:6px;overflow:hidden;margin-top:8px}
        #bar{height:100%;width:0;background:#28a745;transition:width .25s}
        #steps{font-size:12px;color:#555;margin-top:8px;line-height:1.6}
      </style>
    </head>
    <body>
      <h1>上传游戏截图并解析兵种数量</h1>
      <div class=\"box\">
        <label>游戏截图文件</label>
        <input id=\"file\" type=\"file\" accept=\"image/*\" />
        <img id=\"preview\" alt=\"预览\" />
        <label>gameAccountId（可选）</label>
        <input id=\"gameAccountId\" type=\"number\" placeholder=\"例如 1\" />
        <label>tribeId（可选）</label>
        <input id=\"tribeId\" type=\"number\" placeholder=\"例如 1=罗马\" />
        <label><input id=\"write\" type=\"checkbox\" /> 写入数据库</label>
        <div style=\"margin-top:12px\"><button id=\"btn\">提交解析</button></div>
      </div>
      <div class=\"box\">
        <div id=\"status\"></div>
        <div id=\"progress\"><div id=\"bar\"></div></div>
        <div id=\"steps\"></div>
        <pre id=\"result\"></pre>
      </div>
      <div class=\"box\">
        <h2 style=\"font-size:16px;margin:0 0 8px\">生成列图标模板</h2>
        <div style=\"margin-bottom:8px\">使用上面的同一截图，按 JSON 顺序切割每列图标并保存</div>
        <div><button id=\"build\">生成模板</button></div>
        <pre id=\"buildResult\"></pre>
      </div>
      <script>
        const f=document.getElementById('file');
        const p=document.getElementById('preview');
        f.addEventListener('change',()=>{
          const file=f.files&&f.files[0];
          if(file){
            const url=URL.createObjectURL(file);
            p.src=url; p.style.display='block';
          }else{ p.style.display='none'; p.src=''; }
        });
        const btn=document.getElementById('btn');
        const statusEl=document.getElementById('status');
        const result=document.getElementById('result');
        const bar=document.getElementById('bar');
        const steps=document.getElementById('steps');
        const buildBtn=document.getElementById('build');
        const buildResult=document.getElementById('buildResult');
        async function submit(){
          statusEl.textContent=''; result.textContent='';
          steps.textContent=''; bar.style.width='0%';
          const file=f.files&&f.files[0];
          if(!file){ statusEl.textContent='请先选择截图文件'; return; }
          btn.disabled=true; statusEl.textContent='提交中…'; bar.style.width='10%';
          const fd=new FormData();
          fd.append('file', file);
          const gid=document.getElementById('gameAccountId').value.trim();
          const tid=document.getElementById('tribeId').value.trim();
          const write=document.getElementById('write').checked;
          if(gid) fd.append('gameAccountId', gid);
          if(tid) fd.append('tribeId', tid);
          if(write) fd.append('write','1');
          fd.append('debug','1');
          try{
            const xhr=new XMLHttpRequest();
            xhr.open('POST','/api/v1/troops/parse-image');
            xhr.upload.onprogress=(e)=>{
              if(e.lengthComputable){
                const pct=Math.min(40, Math.round(e.loaded/e.total*40));
                bar.style.width=pct+'%';
                steps.textContent='上传进度: '+pct+'%';
              }
            };
            let ocrTimer=null; let cur=40;
            function tick(){ cur=Math.min(85, cur+2); bar.style.width=cur+'%'; steps.textContent='OCR识别中… '+cur+'%'; }
            ocrTimer=setInterval(tick, 250);
            xhr.onreadystatechange=()=>{
              if(xhr.readyState===4){
                if(ocrTimer){ clearInterval(ocrTimer); ocrTimer=null; }
                btn.disabled=false;
                try{
                  const data=JSON.parse(xhr.responseText||'{}');
                  statusEl.textContent='状态: '+xhr.status+(data&&data.tribeId?('，tribeId: '+data.tribeId+'（'+(data.tribeLabel||'')+'）'):'');
                  const L=(data&&data.logs)||[];
                  const seqKeys=['read_file','prepare_image','tesseract_data','tribe_header_band','tribe_icons','rows_extracted'];
                  const seq=L.filter(x=>seqKeys.includes(x.step));
                  const perc=[90,92,94,96,98,100];
                  steps.innerHTML='';
                  let i=0;
                  function advance(){
                    if(i<seq.length){
                      bar.style.width=perc[i]+'%';
                      const s=seq[i];
                      steps.innerHTML += '<div>'+s.step+': '+JSON.stringify(s)+'</div>';
                      i++;
                      setTimeout(advance,180);
                    }else{ bar.style.width='100%'; }
                  }
                  advance();
                  result.textContent=JSON.stringify(data,null,2);
                }catch(err){
                  statusEl.textContent='解析失败';
                  result.textContent=xhr.responseText||String(err);
                }
              }
            };
            xhr.send(fd);
          }catch(e){
            btn.disabled=false;
            statusEl.textContent='请求失败'; result.textContent=String(e);
          }
        }
        btn.addEventListener('click', submit);
        async function buildIcons(){
          buildResult.textContent='';
          const file=f.files&&f.files[0];
          if(!file){ buildResult.textContent='请先选择截图文件'; return; }
          buildBtn.disabled=true;
          try{
            const fd=new FormData();
            fd.append('file', file);
            const tid=document.getElementById('tribeId').value.trim();
            fd.append('tribeId', tid||'2');
            const resp=await fetch('/api/v1/ocr/build-icons',{method:'POST',body:fd});
            const txt=await resp.text();
            let data=null; try{ data=JSON.parse(txt);}catch(e){ data={raw:txt}; }
            buildResult.textContent=JSON.stringify(data,null,2);
          }catch(e){
            buildResult.textContent=String(e);
          }finally{
            buildBtn.disabled=false;
          }
        }
        buildBtn.addEventListener('click', buildIcons);
      </script>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html; charset=utf-8")

@bp.get("/api/v1/ocr/test")
def parse_image_troops_test_alias():
    return parse_image_troops_test()

def _guess_tribe_by_sprite_band(band_img):
    # 归一尺寸并计算多种哈希以提高鲁棒性
    try:
        W, H = 256, 64
        band = band_img.resize((W, H))
        if imagehash is None:
            return None, None
        band_ph = imagehash.phash(band)
        band_ah = imagehash.average_hash(band)
    except Exception:
        return None, None
    # 资源目录候选
    candidates = {
        1: ["roman_small.png", "roman_medium.png", "roman.png"],
        2: ["teuton_small.png", "teuton_medium.png", "teutons.png"],
        3: ["gaul_small.png", "gaul_medium.png", "gauls.png"],
        6: ["egyptian_small.png", "egyptian_medium.png", "egyptians.png"],
        7: ["hun_small.png", "hun_medium.png", "huns.png"],
        8: ["spartan_small.png", "spartan_medium.png", "spartan.png"]
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
                        if imagehash is None:
                            continue
                        h_ph = imagehash.phash(im)
                        h_ah = imagehash.average_hash(im)
                        d = (band_ph - h_ph) + (band_ah - h_ah)
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
    def load_templates(exclude_ram=True):
        bases = []
        bases.append(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "icons")))
        bases.append(os.path.abspath(os.path.join(os.getcwd(), "backend_py", "data", "icons")))
        bases.append(os.path.abspath(os.path.join(os.getcwd(), "resource", "icons")))
        bases.append(os.path.abspath(os.path.join(os.getcwd(), "icons")))
        name_map = {1:"roman",2:"teutons",3:"gauls",6:"egyptians",7:"huns",8:"spartan"}
        tpl = {}
        for tid, nm in name_map.items():
            arr = []
            sub = f"tribe_{tid}_{nm}"
            for base in bases:
                d = os.path.join(base, sub)
                if os.path.isdir(d):
                    for fn in os.listdir(d):
                        # 跳过冲车模板以避免误判
                        if exclude_ram and re.search(r"ram|battering|冲车", fn, flags=re.I):
                            continue
                        p = os.path.join(d, fn)
                        try:
                            im = Image.open(p).convert("L")
                            if imagehash is None:
                                continue
                            arr.append((imagehash.phash(im), imagehash.average_hash(im)))
                        except Exception:
                            continue
            if arr:
                tpl[tid] = arr
        return tpl
    tpl = load_templates(exclude_ram=True)
    if not tpl:
        return None, None
    # 计算每个补丁与模板的最小距离并汇总
    scores = {}
    for tid, arr in tpl.items():
        dsum = 0
        cnt = 0
        for patch in patches:
            try:
                if imagehash is None:
                    continue
                h_ph = imagehash.phash(patch)
                h_ah = imagehash.average_hash(patch)
                dist = min([(h_ph - th_ph) + (h_ah - th_ah) for (th_ph, th_ah) in arr]) if arr else 64
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

def _guess_tribe_by_single_icon(patches, threshold=14, min_gap=2):
    # 单图命中即判定部落（排除冲车）
    bases = []
    bases.append(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "icons")))
    bases.append(os.path.abspath(os.path.join(os.getcwd(), "backend_py", "data", "icons")))
    bases.append(os.path.abspath(os.path.join(os.getcwd(), "resource", "icons")))
    bases.append(os.path.abspath(os.path.join(os.getcwd(), "icons")))
    name_map = {1:"roman",2:"teutons",3:"gauls",6:"egyptians",7:"huns",8:"spartan"}
    templates = []
    for tid, nm in name_map.items():
        sub = f"tribe_{tid}_{nm}"
        for base in bases:
            d = os.path.join(base, sub)
            if os.path.isdir(d):
                for fn in os.listdir(d):
                    if re.search(r"ram|battering|冲车", fn, flags=re.I):
                        continue
                    p = os.path.join(d, fn)
                    try:
                        im = Image.open(p).convert("L")
                        if imagehash is None:
                            continue
                        templates.append((tid, imagehash.phash(im), imagehash.average_hash(im)))
                    except Exception:
                        continue
    if not templates:
        return None, None
    for patch in patches:
        try:
            h_ph = imagehash.phash(patch)
            h_ah = imagehash.average_hash(patch)
        except Exception:
            continue
        best_tid = None
        best_dist = None
        second_best = None
        for (tid, th_ph, th_ah) in templates:
            d = (h_ph - th_ph) + (h_ah - th_ah)
            if best_dist is None or d < best_dist:
                second_best = best_dist
                best_dist = d
                best_tid = tid
            elif second_best is None or d < second_best:
                second_best = d
        if best_dist is not None and best_dist <= threshold:
            if second_best is None or (second_best - best_dist) >= min_gap:
                return best_tid, best_dist
    return None, None

def _get_unit_names_from_json(tid: int):
    data = None
    try:
        data_bytes = pkgutil.get_data('backend_py', 'data/troops_t4.6_1x.json')
        if data_bytes:
            data = json.loads(data_bytes.decode('utf-8'))
    except Exception:
        pass
    if data is None:
        candidates = []
        base = os.path.dirname(os.path.dirname(__file__))
        candidates.append(os.path.abspath(os.path.join(base, 'data', 'troops_t4.6_1x.json')))
        candidates.append(os.path.abspath(os.path.join(os.getcwd(), 'backend_py', 'data', 'troops_t4.6_1x.json')))
        for p in candidates:
            if os.path.exists(p):
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        break
                except Exception:
                    try:
                        with open(p, 'r', encoding='utf-8-sig') as f:
                            data = json.load(f)
                            break
                    except Exception:
                        continue
    if not data:
        return []
    tribes = data.get('tribes') or []
    for t in tribes:
        if int(t.get('tribeId')) == int(tid):
            arr = t.get('units') or []
            names = []
            for u in arr:
                n = str(u.get('name') or '').strip()
                if not n:
                    n = str(u.get('code') or '').strip()
                names.append(n or 'unit')
            return names
    return []

@bp.post('/api/v1/ocr/build-icons')
def build_icons_from_image():
    global Image, ImageOps, pytesseract
    if Image is None:
        try:
            from PIL import Image as _Image, ImageOps as _ImageOps
            Image = _Image
            ImageOps = _ImageOps
        except Exception:
            return error('server_error', message='pil_missing', status=500)
    if pytesseract is None:
        try:
            import pytesseract as _p
            pytesseract = _p
        except Exception:
            return error('server_error', message='pytesseract_missing', status=500)
    file = request.files.get('file')
    if not file:
        return error('bad_request', message='file_missing', status=400)
    tribeId = int(request.form.get('tribeId') or 2)
    tribe_name_map = {1:'roman',2:'teutons',3:'gauls',6:'egyptians',7:'huns',8:'spartan'}
    tribe_dir = f"tribe_{tribeId}_{tribe_name_map.get(tribeId, 'unknown')}"
    b = file.read()
    img = Image.open(io.BytesIO(b)).convert('L')
    img = ImageOps.autocontrast(img)
    data = pytesseract.image_to_data(img, lang='chi_sim+eng', config='--psm 6', output_type=pytesseract.Output.DICT)
    rows = {}
    n = len(data.get('text', []))
    for i in range(n):
        txt = (data['text'][i] or '').strip()
        ln = data.get('line_num', [0])[i]
        if ln not in rows:
            rows[ln] = []
        rows[ln].append({'txt': txt,
                          'left': int(data.get('left', [0])[i] or 0),
                          'top': int(data.get('top', [0])[i] or 0),
                          'width': int(data.get('width', [0])[i] or 0),
                          'height': int(data.get('height', [0])[i] or 0)})
    def is_num(s):
        return bool(re.match(r'^\d+$', s))
    target = None
    for ln, tokens in sorted(rows.items(), key=lambda x: x[0]):
        nums = [int(t['txt']) for t in tokens if is_num(t['txt'])]
        if len(nums) >= 8:
            target = (ln, tokens)
            break
    if not target:
        return error('not_found', message='no_sufficient_numbers', status=404)
    ln, tokens = target
    num_centers = []
    text_h = 0
    for t in tokens:
        if is_num(t['txt']):
            cx = t['left'] + t['width'] // 2
            num_centers.append(cx)
            text_h = max(text_h, int(t['height']))
    row_top = min([t['top'] for t in tokens])
    band_h = int(text_h * 2)
    header_y = max(0, row_top - band_h)
    unit_names = _get_unit_names_from_json(tribeId)
    dst_base = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'icons', tribe_dir))
    os.makedirs(dst_base, exist_ok=True)
    saved = []
    icon_size = max(16, int(text_h * 1.6))
    for idx, cx in enumerate(num_centers[:len(unit_names) or 10]):
        x0 = max(0, cx - icon_size // 2)
        y0 = header_y
        x1 = min(img.width, x0 + icon_size)
        y1 = min(img.height, y0 + icon_size)
        if x1 <= x0 or y1 <= y0:
            continue
        patch = img.crop((x0, y0, x1, y1))
        nm = unit_names[idx] if idx < len(unit_names) else f"unit{idx+1}"
        safe = re.sub(r'[^A-Za-z0-9_\-]', '_', nm)
        fn = f"{idx+1:02d}_{safe}.png"
        outp = os.path.join(dst_base, fn)
        try:
            patch.save(outp)
            saved.append(outp)
        except Exception:
            continue
    return ok({'saved': saved, 'dir': dst_base, 'tribeId': tribeId})

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