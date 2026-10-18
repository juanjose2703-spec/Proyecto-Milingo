from flask import Blueprint, jsonify, request

from servidor.errores import ErrorAPI
from servidor.seguridad import rol_requerido
from servidor.servicios import admin_estudiantes as ae

admin_estudiantes_bp = Blueprint(
    "admin_estudiantes", __name__, url_prefix="/api/v1/admin/students"
)


def _ok(datos):
    return jsonify({"ok": True, "datos": datos})


def _cuerpo():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ErrorAPI(400, "json_invalido", "El cuerpo debe ser JSON.")
    return datos


@admin_estudiantes_bp.get("")
@rol_requerido("admin")
def listar():
    return _ok({"estudiantes": ae.listar()})


@admin_estudiantes_bp.get("/<int:usuario_id>")
@rol_requerido("admin")
def detalle(usuario_id):
    return _ok(ae.detalle(usuario_id))


@admin_estudiantes_bp.patch("/<int:usuario_id>/stats")
@rol_requerido("admin")
def fijar_estadisticas(usuario_id):
    return _ok({"estadisticas": ae.fijar_estadisticas(usuario_id, _cuerpo())})


@admin_estudiantes_bp.post("/<int:usuario_id>/lessons/<int:leccion_id>/complete-until")
@rol_requerido("admin")
def completar_hasta(usuario_id, leccion_id):
    return _ok(ae.completar_hasta(usuario_id, leccion_id))


@admin_estudiantes_bp.post("/<int:usuario_id>/lessons/<int:leccion_id>/reset")
@rol_requerido("admin")
def reiniciar_leccion(usuario_id, leccion_id):
    return _ok(ae.reiniciar_leccion(usuario_id, leccion_id))


@admin_estudiantes_bp.post("/<int:usuario_id>/reset")
@rol_requerido("admin")
def reiniciar_todo(usuario_id):
    return _ok({"estadisticas": ae.reiniciar_todo(usuario_id, _cuerpo())})