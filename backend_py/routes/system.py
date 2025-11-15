from flask import Blueprint, jsonify
from db import engine

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