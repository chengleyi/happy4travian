from flask import Blueprint, jsonify
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
    env_path = os.getenv("TROOPS_PARAMS_PATH")
    if env_path and os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
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
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return jsonify(data)
        except Exception:
            continue
    try:
        url = os.getenv("TROOPS_PARAMS_URL") or "https://raw.githubusercontent.com/chengleyi/happy4travian/main/backend_py/data/troops_t4.6_1x.json"
        with urllib.request.urlopen(url, timeout=10) as r:
            txt = r.read().decode("utf-8")
            data = json.loads(txt)
            return jsonify(data)
    except Exception:
        pass
    return jsonify({"error": "not_found"}), 404