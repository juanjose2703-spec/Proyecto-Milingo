"""Desbloqueo secuencial: una lección se abre al completar la anterior.

El orden es curso -> unidad -> lección, solo con contenido publicado.
El estado lo calcula siempre el servidor.
"""
from servidor.extensiones import bd
from servidor.modelos import (
    Curso, Unidad, Leccion, IntentoLeccion, ProgresoLeccionUsuario,
)
from servidor.servicios.reglas import (
    ESTADO_EN_CURSO, LECCION_BLOQUEADA, LECCION_DISPONIBLE,
    LECCION_EN_PROGRESO, LECCION_COMPLETADA,
)


def lecciones_ordenadas():
    consulta = (
        bd.select(Leccion)
        .join(Unidad, Leccion.unidad_id == Unidad.id)
        .join(Curso, Unidad.curso_id == Curso.id)
        .where(
            Curso.publicado.is_(True),
            Unidad.publicado.is_(True),
            Leccion.publicada.is_(True),
        )
        .order_by(Curso.orden, Unidad.orden, Leccion.orden)
    )
    return bd.session.execute(consulta).scalars().all()


def estados_por_leccion(usuario_id, lecciones=None):
    """Devuelve {leccion_id: estado} para el usuario."""
    if lecciones is None:
        lecciones = lecciones_ordenadas()

    progresos = {
        p.leccion_id: p
        for p in bd.session.execute(
            bd.select(ProgresoLeccionUsuario).where(
                ProgresoLeccionUsuario.usuario_id == usuario_id
            )
        ).scalars()
    }
    en_curso = set(
        bd.session.execute(
            bd.select(IntentoLeccion.leccion_id).where(
                IntentoLeccion.usuario_id == usuario_id,
                IntentoLeccion.estado == ESTADO_EN_CURSO,
            )
        ).scalars()
    )

    estados = {}
    anterior_completada = True
    for leccion in lecciones:
        progreso = progresos.get(leccion.id)
        if progreso is not None and progreso.estado == LECCION_COMPLETADA:
            estado = LECCION_COMPLETADA
        elif not anterior_completada:
            estado = LECCION_BLOQUEADA
        elif progreso is not None or leccion.id in en_curso:
            estado = LECCION_EN_PROGRESO
        else:
            estado = LECCION_DISPONIBLE
        estados[leccion.id] = estado
        anterior_completada = estado == LECCION_COMPLETADA
    return estados


def siguiente_leccion(lecciones, estados):
    """Primera lección que el estudiante puede hacer ahora, o None."""
    for leccion in lecciones:
        if estados[leccion.id] in (LECCION_DISPONIBLE, LECCION_EN_PROGRESO):
            return leccion
    return None