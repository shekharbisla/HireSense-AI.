from app import create_app
import os

# Create Flask app using factory
app = create_app()

if __name__ == "__main__":
    # PORT: Cloud hosting (Render/Railway/Replit) will inject this
    port = int(os.environ.get("PORT", 5000))
    # ENV: If not set, defaults to "dev" (see config.py)
    env = os.environ.get("ENV", "dev")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=(env == "dev")   # debug true only in dev
    )
