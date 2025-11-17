import logging
import json
from flask import Flask, request, Response
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
import models  # ensure models are loaded

def create_app():
    app = Flask(__name__)
    CORS(app, origins=["https://happy4travian.com", "https://www.happy4travian.com"], methods=["GET","POST","PUT","DELETE","OPTIONS"], allow_headers=["*"])
    logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    @app.before_request
    def _log_before():
        pass

    @app.after_request
    def _log_after(response):
        try:
            logging.info("api %s %s status=%s", request.method, request.full_path, response.status_code)
        except Exception:
            pass
        return response

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
        body = {"success": False, "error": "not_found", "message": "route_not_found"}
        return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json"), 404

    @app.errorhandler(400)
    def handle_400(e):
        body = {"success": False, "error": "bad_request", "message": getattr(e, "description", "bad_request")}
        return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json"), 400

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            code = e.code
            name = getattr(e, "name", "http_error")
            msg = getattr(e, "description", str(e))
            body = {"success": False, "error": name.replace(" ", "_"), "message": msg}
            return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json"), code
        body = {"success": False, "error": "server_error", "message": str(e)}
        return Response(json.dumps(body, ensure_ascii=False, indent=2), mimetype="application/json"), 500

    try:
        Base.metadata.create_all(engine)
    except Exception:
        pass

    try:
        if migrate_missing_columns:
            migrate_missing_columns()
    except Exception:
        pass

    return app