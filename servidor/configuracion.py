import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Configuracion:
    """Valores de configuración leídos del archivo .env."""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TIMEZONE = os.environ.get("TIMEZONE", "America/Bogota")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    )
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_ENABLED = True


class ConfiguracionPruebas(Configuracion):
    """Usa la base milingo_pruebas y desactiva el límite de intentos."""

    TESTING = True
    SECRET_KEY = "clave-solo-para-pruebas"
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL")
    RATELIMIT_ENABLED = False