import os

class BaseConfig:
    APP_NAME = "HireSense AI"
    LOG_LEVEL = "INFO"
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    # Future: DB_URL, API_KEYS, etc.

class DevConfig(BaseConfig):
    DEBUG = True

class ProdConfig(BaseConfig):
    DEBUG = False
    LOG_LEVEL = "WARNING"

def get_config():
    env = os.environ.get("ENV", "dev").lower()
    return ProdConfig if env == "prod" else DevConfig
