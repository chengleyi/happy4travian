"""统一响应封装

提供 `ok` 与 `error` 两个辅助方法，返回 JSON 响应；
自动处理 `count` 字段（当 data 为列表时）。
"""
import json
from flask import Response

def _make(payload, status=200):
    """生成 Flask Response 对象（JSON），并附带状态码"""
    return Response(json.dumps(payload, ensure_ascii=False, indent=2), mimetype="application/json"), status

def ok(data=None, count=None, message=None):
    """成功响应

    - data: 成功数据
    - count: 总数（可选，若 data 为列表则自动推断）
    - message: 文本消息（可选）
    """
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
    """错误响应

    - code: 错误码
    - message: 错误描述（可选）
    - status: HTTP 状态码（默认 500）
    """
    payload = {"success": False, "error": code}
    if message is not None:
        payload["message"] = message
    return _make(payload, status)