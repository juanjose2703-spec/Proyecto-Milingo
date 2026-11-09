import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def _formatear_db_url(nombre_variable: str) -> str | None:
    """Lee la URL de entorno y convierte el prefijo 'postgres://' a 'postgresql://'."""
    url = os.environ.get(nombre_variable)
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Configuracion:
    """Valores de configuración leídos del archivo .env."""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _formatear_db_url("DATABASE_URL")
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
    """Usa la base de datos de pruebas y desactiva el límite de intentos."""

    TESTING = True
    SECRET_KEY = "clave-solo-para-pruebas"
    SQLALCHEMY_DATABASE_URI = _formatear_db_url("TEST_DATABASE_URL")
    RATELIMIT_ENABLED = False