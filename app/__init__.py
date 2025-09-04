from flask import Flask
from flask_cors import CORS
from .config import get_config

def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(get_config())

    # CORS for frontend hosting (Vercel/Netlify)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    # Register blueprints
    from .routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    # Health
    @app.get("/healthz")
    def health():
        return {"status": "ok"}, 200

    # Home (simple demo UI)
    @app.get("/")
    def home():
        from flask import render_template
        return render_template("index.html")

    # Logging basic
    app.logger.setLevel(app.config["LOG_LEVEL"])
    app.logger.info("HireSense AI booted.")
    return app
