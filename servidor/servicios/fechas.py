from datetime import datetime
from zoneinfo import ZoneInfo

from flask import current_app


def hoy_local():
    """Fecha de hoy en la zona horaria del proyecto (TIMEZONE en .env)."""
    return datetime.now(ZoneInfo(current_app.config["TIMEZONE"])).date()