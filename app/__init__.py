# app/__init__.py
from flask import Flask
from flask_cors import CORS
from .config import get_config

def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(get_config())

    # CORS for frontend hosting (Vercel/Netlify)
    # allow origins configured in config (string or list)
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    # Register API blueprint
    try:
        from .routes.api import api_bp
        app.register_blueprint(api_bp, url_prefix="/api")
    except Exception as e:
        app.logger.warning(f"Could not register api blueprint: {e}")

    # Register main pages blueprint (index, terms, howto, about)
    try:
        from .routes.main import main as main_bp
        app.register_blueprint(main_bp)
    except Exception as e:
        app.logger.warning(f"Could not register main blueprint: {e}")

    # Health endpoint
    @app.get("/healthz")
    def health():
        return {"status": "ok"}, 200

    # Optional short demo route (kept for compatibility)
    # If main blueprint exists it will serve '/', otherwise fallback to index.html
    @app.get("/demo")
    def demo():
        from flask import render_template
        return render_template("index.html")

    # Template context processor: make 'year' available to all templates
    @app.context_processor
    def inject_year():
        from datetime import datetime
        return {"year": datetime.utcnow().year}

    # Logging
    # Ensure LOG_LEVEL exists in config; default to INFO if not.
    import logging
    level = app.config.get("LOG_LEVEL", "INFO")
    try:
        app.logger.setLevel(level)
    except Exception:
        app.logger.setLevel(logging.INFO)
    app.logger.info("HireSense AI booted.")

    return app
