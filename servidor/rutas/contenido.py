from flask import Blueprint, jsonify

from servidor.errores import ErrorAPI
from servidor.extensiones import bd
from servidor.modelos import Curso, Unidad, Leccion, Pregunta
from servidor.seguridad import login_requerido, usuario_actual
from servidor.servicios import desbloqueo
from servidor.servicios.reglas import LECCION_BLOQUEADA

contenido_bp = Blueprint("contenido", __name__, url_prefix="/api/v1")


def _ok(datos):
    return jsonify({"ok": True, "datos": datos})


def _curso_publico(curso_id):
    curso = bd.session.get(Curso, curso_id)
    if curso is None or not curso.publicado:
        raise ErrorAPI(404, "no_encontrado", "Curso no encontrado.")
    return curso


def _unidad_publica(unidad_id):
    unidad = bd.session.get(Unidad, unidad_id)
    if unidad is None or not unidad.publicado or not unidad.curso.publicado:
        raise ErrorAPI(404, "no_encontrado", "Unidad no encontrada.")
    return unidad


def _leccion_publica(leccion_id):
    leccion = bd.session.get(Leccion, leccion_id)
    if (leccion is None or not leccion.publicada
            or not leccion.unidad.publicado or not leccion.unidad.curso.publicado):
        raise ErrorAPI(404, "no_encontrado", "Lección no encontrada.")
    return leccion


def _curso_dict(curso):
    return {
        "id": curso.id, "titulo": curso.titulo, "descripcion": curso.descripcion,
        "nivel": curso.nivel, "orden": curso.orden,
    }


def _leccion_dict(leccion, estados):
    return {
        "id": leccion.id, "unidad_id": leccion.unidad_id, "titulo": leccion.titulo,
        "descripcion": leccion.descripcion, "orden": leccion.orden,
        "estado": estados.get(leccion.id, LECCION_BLOQUEADA),
    }


def _lecciones_publicadas(unidad, estados):
    return [_leccion_dict(l, estados) for l in unidad.lecciones if l.publicada]


def _estados():
    return desbloqueo.estados_por_leccion(usuario_actual().id)


@contenido_bp.get("/courses")
@login_requerido
def listar_cursos():
    cursos = bd.session.execute(
        bd.select(Curso).where(Curso.publicado.is_(True)).order_by(Curso.orden)
    ).scalars().all()
    return _ok({"cursos": [_curso_dict(c) for c in cursos]})


@contenido_bp.get("/courses/<int:curso_id>")
@login_requerido
def ver_curso(curso_id):
    return _ok({"curso": _curso_dict(_curso_publico(curso_id))})


@contenido_bp.get("/courses/<int:curso_id>/units")
@login_requerido
def unidades_del_curso(curso_id):
    curso = _curso_publico(curso_id)
    estados = _estados()
    unidades = [
        {
            "id": u.id, "titulo": u.titulo, "descripcion": u.descripcion, "orden": u.orden,
            "lecciones": _lecciones_publicadas(u, estados),
        }
        for u in curso.unidades if u.publicado
    ]
    return _ok({"curso": _curso_dict(curso), "unidades": unidades})


@contenido_bp.get("/units/<int:unidad_id>/lessons")
@login_requerido
def lecciones_de_unidad(unidad_id):
    unidad = _unidad_publica(unidad_id)
    return _ok({
        "unidad": {"id": unidad.id, "titulo": unidad.titulo},
        "lecciones": _lecciones_publicadas(unidad, _estados()),
    })


@contenido_bp.get("/lessons/<int:leccion_id>")
@login_requerido
def ver_leccion(leccion_id):
    """Datos de la lección. No incluye preguntas ni respuestas."""
    leccion = _leccion_publica(leccion_id)
    total = bd.session.execute(
        bd.select(bd.func.count()).select_from(Pregunta).where(
            Pregunta.leccion_id == leccion.id, Pregunta.publicada.is_(True)
        )
    ).scalar_one()
    datos = _leccion_dict(leccion, _estados())
    datos.update(
        num_preguntas=total,
        xp_base=leccion.xp_base,
        unidad_titulo=leccion.unidad.titulo,
    )
    return _ok({"leccion": datos})