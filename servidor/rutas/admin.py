from flask import Blueprint, jsonify

from servidor.seguridad import rol_requerido

admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


@admin_bp.get("/ping")
@rol_requerido("admin")
def ping():
    return jsonify({"ok": True, "datos": {"mensaje": "Acceso de administrador"}})