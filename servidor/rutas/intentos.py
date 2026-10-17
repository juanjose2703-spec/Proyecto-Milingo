from flask import Blueprint, jsonify, request

from servidor.errores import ErrorAPI
from servidor.seguridad import rol_requerido, usuario_actual
from servidor.servicios import intentos

intentos_bp = Blueprint("intentos", __name__, url_prefix="/api/v1")


def _ok(datos, estado=200):
    return jsonify({"ok": True, "datos": datos}), estado


def _cuerpo_json():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ErrorAPI(400, "json_invalido", "El cuerpo debe ser JSON.")
    return datos


@intentos_bp.post("/lessons/<int:leccion_id>/attempts")
@rol_requerido("estudiante")
def iniciar_intento(leccion_id):
    """Crea un intento, o reanuda el que está en curso."""
    datos = intentos.iniciar(usuario_actual().id, leccion_id)
    return _ok(datos, 200 if datos["reanudado"] else 201)


@intentos_bp.post("/attempts/<int:intento_id>/answers")
@rol_requerido("estudiante")
def responder_pregunta(intento_id):
    return _ok(intentos.responder(usuario_actual().id, intento_id, _cuerpo_json()))


@intentos_bp.post("/attempts/<int:intento_id>/complete")
@rol_requerido("estudiante")
def completar_intento(intento_id):
    return _ok(intentos.completar(usuario_actual().id, intento_id))


@intentos_bp.post("/attempts/<int:intento_id>/abandon")
@rol_requerido("estudiante")
def abandonar_intento(intento_id):
    return _ok(intentos.abandonar(usuario_actual().id, intento_id))