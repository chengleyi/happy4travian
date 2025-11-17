import json
from flask import Response

def _make(payload, status=200):
    return Response(json.dumps(payload, ensure_ascii=False, indent=2), mimetype="application/json"), status

def ok(data=None, count=None, message=None):
    payload = {"success": True}
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
        if count is not None:
            payload["count"] = count
        elif isinstance(data, list):
            payload["count"] = len(data)
    else:
        if count is not None:
            payload["count"] = count
    return _make(payload)

def error(code="server_error", message=None, status=500):
    payload = {"success": False, "error": code}
    if message is not None:
        payload["message"] = message
    return _make(payload, status)