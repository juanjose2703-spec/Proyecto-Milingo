from flask import Blueprint, jsonify, request

from servidor.errores import ErrorAPI
from servidor.seguridad import rol_requerido
from servidor.servicios import admin_contenido as ac

admin_contenido_bp = Blueprint("admin_contenido", __name__, url_prefix="/api/v1/admin")

TIPO_POR_COLECCION = {
    "courses": "curso", "units": "unidad", "lessons": "leccion", "questions": "pregunta",
}
COLECCIONES = "<any(courses,units,lessons,questions):coleccion>"


def _ok(datos, estado=200):
    return jsonify({"ok": True, "datos": datos}), estado


def _cuerpo():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ErrorAPI(400, "json_invalido", "El cuerpo debe ser JSON.")
    return datos


@admin_contenido_bp.get("/content")
@rol_requerido("admin")
def ver_contenido():
    return _ok({"cursos": ac.arbol()})


@admin_contenido_bp.post("/courses")
@rol_requerido("admin")
def crear_curso():
    return _ok({"curso": ac.crear_curso(_cuerpo())}, 201)


@admin_contenido_bp.post("/courses/<int:curso_id>/units")
@rol_requerido("admin")
def crear_unidad(curso_id):
    return _ok({"unidad": ac.crear_unidad(curso_id, _cuerpo())}, 201)


@admin_contenido_bp.post("/units/<int:unidad_id>/lessons")
@rol_requerido("admin")
def crear_leccion(unidad_id):
    return _ok({"leccion": ac.crear_leccion(unidad_id, _cuerpo())}, 201)


@admin_contenido_bp.get("/lessons/<int:leccion_id>/questions")
@rol_requerido("admin")
def listar_preguntas(leccion_id):
    return _ok(ac.listar_preguntas(leccion_id))


@admin_contenido_bp.post("/lessons/<int:leccion_id>/questions")
@rol_requerido("admin")
def crear_pregunta(leccion_id):
    return _ok({"pregunta": ac.crear_pregunta(leccion_id, _cuerpo())}, 201)


@admin_contenido_bp.patch(f"/{COLECCIONES}/<int:id_>")
@rol_requerido("admin")
def editar(coleccion, id_):
    tipo = TIPO_POR_COLECCION[coleccion]
    return _ok({tipo: ac.editar(tipo, id_, _cuerpo())})


@admin_contenido_bp.delete(f"/{COLECCIONES}/<int:id_>")
@rol_requerido("admin")
def borrar(coleccion, id_):
    ac.borrar(TIPO_POR_COLECCION[coleccion], id_)
    return _ok({})


@admin_contenido_bp.post(f"/{COLECCIONES}/<int:id_>/move")
@rol_requerido("admin")
def mover(coleccion, id_):
    movido = ac.mover(TIPO_POR_COLECCION[coleccion], id_, _cuerpo().get("direccion"))
    return _ok({"movido": movido})