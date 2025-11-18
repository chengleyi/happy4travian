"""请求体读取工具

提供 `get_json()`：在不同类型的请求体（application/json、原始字节、表单）下，稳健地解析为字典。
"""
import json
from flask import request

def get_json():
    """稳健读取 JSON/表单请求并返回字典

    读取顺序：
    1. `request.get_json(silent=True)`（优先）
    2. 原始字节 → 尝试 `utf-8` / `utf-8-sig` 解码并 `json.loads`
    3. 若为表单：将 `request.form` 合并为 dict，并尝试解析字符串型 `counts`
    4. 无法解析则返回空字典

    返回：`dict`
    """
    data = None
    try:
        data = request.get_json(silent=True)
    except Exception:
        data = None
    if isinstance(data, dict):
        return data
    b = None
    try:
        b = request.get_data(cache=True, as_text=False)
    except Exception:
        b = None
    if not b:
        try:
            s2 = request.get_data(cache=True, as_text=True)
            if s2:
                try:
                    j2 = json.loads(s2)
                    if isinstance(j2, dict):
                        return j2
                except Exception:
                    pass
        except Exception:
            pass
        if request.form:
            d = {}
            for k in request.form.keys():
                v = request.form.getlist(k)
                d[k] = v[0] if len(v) == 1 else v
            try:
                if isinstance(d.get("counts"), str):
                    d["counts"] = json.loads(d["counts"])  
            except Exception:
                pass
            return d
        return {}
    for enc in ("utf-8", "utf-8-sig"):
        try:
            s = b.decode(enc)
            j = json.loads(s)
            if isinstance(j, dict):
                return j
        except Exception:
            continue
    return {}