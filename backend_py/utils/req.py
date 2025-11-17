import json
from flask import request

def get_json():
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