import logging
from flask import Flask, request
from flask_cors import CORS
from routes.system import bp as system_bp
from routes.servers import bp as servers_bp
from routes.tribes import bp as tribes_bp
from routes.accounts import bp as accounts_bp
from routes.villages import bp as villages_bp
from routes.troops import bp as troops_bp
from routes.alliances import bp as alliances_bp

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

    return app