"""应用工厂

负责创建并配置 Flask 应用：
- 注册各业务蓝图（系统、服务器、部落、账号、村庄、兵种、联盟、用户、开发）
- 设置 CORS 允许的来源和方法
- 配置统一的异常处理与访问日志
- 初始化数据库模型并执行缺失列的迁移
"""
import logging
import json
from flask import Flask, request, Response
import os, sys, platform, shutil
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
from routes.system import bp as system_bp
from routes.servers import bp as servers_bp
from routes.tribes import bp as tribes_bp
from routes.accounts import bp as accounts_bp
from routes.villages import bp as villages_bp
from routes.troops import bp as troops_bp
from routes.alliances import bp as alliances_bp
from routes.users import bp as users_bp
from routes.dev import bp as dev_bp
from db import Base, engine
try:
    from tools.migrations import migrate_missing_columns
except Exception:
    migrate_missing_columns = None
import models  

def create_app():
    """创建并返回 Flask 应用实例"""
    app = Flask(__name__)
    # 配置跨域：允许正式域名来源访问 API
    CORS(app, origins=[
        "https://happy4travian.com",
        "https://www.happy4travian.com",
        "http://happy4travian.com",
        "http://www.happy4travian.com",
        "http://47.243.146.179",
        "https://47.243.146.179"
    ], methods=["GET","POST","PUT","DELETE","OPTIONS"], allow_headers=["*"])
    # 简单文件日志（位于 /opt/happy4travian/app.log 或当前目录）
    logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    try:
        logging.info("boot python_executable=%s python_version=%s platform=%s", sys.executable, sys.version.replace("\n"," "), platform.platform())
        logging.info("boot cwd=%s", os.getcwd())
        tp = os.getenv("TROOPS_PARAMS_PATH")
        logging.info("boot env TROOPS_PARAMS_PATH=%s", tp or "")
        tpath = shutil.which("tesseract")
        logging.info("boot which tesseract=%s", tpath or "")
        try:
            import PIL
            logging.info("boot dep PIL=%s", getattr(PIL, "__version__", ""))
        except Exception as e:
            logging.info("boot dep PIL_missing=%s", str(e))
        try:
            import pytesseract
            logging.info("boot dep pytesseract=%s", getattr(pytesseract, "__version__", ""))
        except Exception as e:
            logging.info("boot dep pytesseract_missing=%s", str(e))
        try:
            import imagehash
            logging.info("boot dep imagehash=%s", getattr(imagehash, "__version__", ""))
        except Exception as e:
            logging.info("boot dep imagehash_missing=%s", str(e))
        try:
            import numpy as np
            logging.info("boot dep numpy=%s", getattr(np, "__version__", ""))
        except Exception as e:
            logging.info("boot dep numpy_missing=%s", str(e))
    except Exception:
        pass

    @app.before_request
    def _log_before():
        # 可插入请求开始前的审计或鉴权逻辑，目前为空
        pass

    @app.after_request
    def _log_after(response):
        # 简单记录请求方法、完整路径与响应状态码
        try:
            logging.info("api %s %s status=%s", request.method, request.full_path, response.status_code)
        except Exception:
            pass
        return response

    # 注册所有路由蓝图
    app.register_blueprint(system_bp)
    app.register_blueprint(servers_bp)
    app.register_blueprint(tribes_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(villages_bp)
    app.register_blueprint(troops_bp)
    app.register_blueprint(alliances_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(dev_bp)

    @app.errorhandler(404)
    def handle_404(e):
        # 未匹配的路由统一返回 JSON
        body = {"success": False, "error": "not_found", "message": "route_not_found"}
        return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json"), 404

    @app.errorhandler(400)
    def handle_400(e):
        # 请求错误（参数缺失等）统一返回 JSON
        body = {"success": False, "error": "bad_request", "message": getattr(e, "description", "bad_request")}
        return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json"), 400

    @app.errorhandler(Exception)
    def handle_exception(e):
        # 统一异常处理：HTTPException 按其状态码返回，其他视为服务器错误
        if isinstance(e, HTTPException):
            code = e.code
            name = getattr(e, "name", "http_error")
            msg = getattr(e, "description", str(e))
            body = {"success": False, "error": name.replace(" ", "_"), "message": msg}
            return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json"), code
        body = {"success": False, "error": "server_error", "message": str(e)}
        return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json"), 500

    try:
        # 应用启动时尝试创建缺失的表结构（幂等）
        Base.metadata.create_all(engine)
    except Exception:
        pass

    try:
        # 运行简单的列迁移（如果工具可用）
        if migrate_missing_columns:
            migrate_missing_columns()
    except Exception:
        pass

    return app