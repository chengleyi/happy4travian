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
    b = request.get_data(cache=False, as_text=False)
    if not b:
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