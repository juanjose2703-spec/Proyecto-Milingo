from datetime import timedelta

from flask import Blueprint, jsonify

from servidor.extensiones import bd
from servidor.modelos import ActividadDiaria, Logro, LogroUsuario
from servidor.seguridad import rol_requerido, usuario_actual
from servidor.servicios import desbloqueo, estadisticas
from servidor.servicios.fechas import hoy_local
from servidor.servicios.reglas import LECCION_COMPLETADA

progreso_bp = Blueprint("progreso", __name__, url_prefix="/api/v1")

DIAS_ACTIVIDAD = 7


def _ok(datos):
    return jsonify({"ok": True, "datos": datos})


def _logro_dict(logro, fecha):
    return {
        "codigo": logro.codigo,
        "nombre": logro.nombre,
        "descripcion": logro.descripcion,
        "icono": logro.icono,
        "desbloqueado": fecha is not None,
        "desbloqueado_en": fecha.isoformat() if fecha else None,
    }


@progreso_bp.get("/stats")
@rol_requerido("estudiante")
def estadisticas_usuario():
    est = estadisticas.obtener(usuario_actual().id)
    return _ok(estadisticas.a_dict(est))


@progreso_bp.get("/progress")
@rol_requerido("estudiante")
def resumen_progreso():
    lecciones = desbloqueo.lecciones_ordenadas()
    estados = desbloqueo.estados_por_leccion(usuario_actual().id, lecciones)
    total = len(lecciones)
    completadas = sum(1 for e in estados.values() if e == LECCION_COMPLETADA)
    siguiente = desbloqueo.siguiente_leccion(lecciones, estados)
    return _ok({
        "total_lecciones": total,
        "lecciones_completadas": completadas,
        "porcentaje": round(100 * completadas / total) if total else 0,
        "siguiente": None if siguiente is None else {
            "id": siguiente.id,
            "titulo": siguiente.titulo,
            "descripcion": siguiente.descripcion,
            "unidad_titulo": siguiente.unidad.titulo,
            "estado": estados[siguiente.id],
        },
    })


@progreso_bp.get("/activity")
@rol_requerido("estudiante")
def actividad():
    hoy = hoy_local()
    desde = hoy - timedelta(days=DIAS_ACTIVIDAD - 1)
    filas = bd.session.execute(
        bd.select(ActividadDiaria).where(
            ActividadDiaria.usuario_id == usuario_actual().id,
            ActividadDiaria.fecha >= desde,
        )
    ).scalars()
    por_fecha = {f.fecha: f for f in filas}

    dias = []
    for i in range(DIAS_ACTIVIDAD):
        dia = desde + timedelta(days=i)
        fila = por_fecha.get(dia)
        dias.append({
            "fecha": dia.isoformat(),
            "activo": fila is not None,
            "xp": fila.xp_ganado if fila else 0,
            "lecciones": fila.lecciones_completadas if fila else 0,
        })
    return _ok({"dias": dias})


@progreso_bp.get("/achievements")
@rol_requerido("estudiante")
def listar_logros():
    todos = bd.session.execute(bd.select(Logro).order_by(Logro.id)).scalars().all()
    fechas = {
        lu.logro_id: lu.desbloqueado_en
        for lu in bd.session.execute(
            bd.select(LogroUsuario).where(LogroUsuario.usuario_id == usuario_actual().id)
        ).scalars()
    }
    return _ok({"logros": [_logro_dict(l, fechas.get(l.id)) for l in todos]})


@progreso_bp.get("/achievements/unlocked")
@rol_requerido("estudiante")
def listar_logros_desbloqueados():
    filas = bd.session.execute(
        bd.select(Logro, LogroUsuario.desbloqueado_en)
        .join(LogroUsuario, LogroUsuario.logro_id == Logro.id)
        .where(LogroUsuario.usuario_id == usuario_actual().id)
        .order_by(LogroUsuario.desbloqueado_en.desc(), Logro.id.desc())
    ).all()
    return _ok({"logros": [_logro_dict(logro, fecha) for logro, fecha in filas]})