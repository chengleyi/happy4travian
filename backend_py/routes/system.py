from flask import Blueprint, jsonify, request, send_file
import pkgutil
from db import engine
import os, json, urllib.request

bp = Blueprint("system", __name__)

@bp.get("/api/v1/health")
def health():
    return "ok"

@bp.get("/api/v1/healthz")
def healthz():
    return "ok"

@bp.get("/api/v1/db/ping")
def db_ping():
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return "ok"
    except Exception:
        return "error"

@bp.get("/api/v1/troops_params")
def troops_params_alias():
    version = request.args.get("version", "1.46")
    speed_str = request.args.get("speed", "1x")
    m = re.match(r"^(\d+)x$", speed_str)
    speed = int(m.group(1)) if m else 1
    env_path = os.getenv("TROOPS_PARAMS_PATH")
    def load_base():
        if env_path and os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                return json.load(f)
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
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
        try:
            url = os.getenv("TROOPS_PARAMS_URL") or "https://raw.githubusercontent.com/chengleyi/happy4travian/main/backend_py/data/troops_t4.6_1x.json"
            with urllib.request.urlopen(url, timeout=10) as r:
                txt = r.read().decode("utf-8")
                return json.loads(txt)
        except Exception:
            return None
    base_data = load_base()
    if not base_data:
        if request.args.get("debug") == "1":
            info = {
                "cwd": os.getcwd(),
                "file": __file__,
                "env_path": env_path
            }
            return jsonify(info), 404
        return jsonify({"error": "not_found"}), 404
    if version != "1.46":
        return jsonify({"error": "not_found"}), 404
    if speed <= 1:
        return jsonify(base_data)
    def scale(d, k):
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
    return jsonify(scale(base_data, speed))