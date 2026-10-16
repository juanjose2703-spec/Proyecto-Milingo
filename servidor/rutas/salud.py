from flask import Blueprint, jsonify
from sqlalchemy import text

from servidor.extensiones import bd

salud_bp = Blueprint("salud", __name__, url_prefix="/api/v1")


@salud_bp.get("/salud")
def salud():
    """Comprueba que el servidor y la base de datos responden."""
    try:
        bd.session.execute(text("SELECT 1"))
        estado_bd = "ok"
    except Exception:
        estado_bd = "error"

    codigo = 200 if estado_bd == "ok" else 503
    return jsonify({"servidor": "ok", "base_datos": estado_bd}), codigo