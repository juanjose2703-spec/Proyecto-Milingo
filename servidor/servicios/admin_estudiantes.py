"""Administración del progreso de los estudiantes (solo administrador).

Ninguna acción de aquí otorga XP, racha ni logros por sí misma: son correcciones
manuales. Las que tocan estadísticas bloquean la fila del estudiante.
"""
from datetime import timedelta

from servidor.errores import ErrorAPI
from servidor.extensiones import bd
from servidor.modelos import (
    ActividadDiaria, EstadisticaUsuario, IntentoLeccion, Leccion, Logro, LogroUsuario,
    ProgresoLeccionUsuario, RespuestaIntento, Usuario,
)
from servidor.servicios import desbloqueo, estadisticas
from servidor.servicios.ejercicios import es_entero
from servidor.servicios.fechas import hoy_local
from servidor.servicios.reglas import (
    CORAZONES_INICIALES, CORAZONES_MAXIMOS, ESTADO_ABANDONADO, ESTADO_EN_CURSO,
    LECCION_COMPLETADA, ROL_ESTUDIANTE,
)

MAX_XP = 1_000_000
DIAS_ACTIVIDAD = 14


def _malo(mensaje):
    return ErrorAPI(400, "datos_invalidos", mensaje)


def _estudiante(usuario_id):
    u = bd.session.get(Usuario, usuario_id)
    if u is None or u.rol != ROL_ESTUDIANTE:
        raise ErrorAPI(404, "no_encontrado", "Estudiante no encontrado.")
    return u


def _datos_estudiante(u):
    return {
        "id": u.id, "nombre_usuario": u.nombre_usuario, "nombre_mostrar": u.nombre_mostrar,
        "correo": u.correo, "activo": u.activo,
    }


def _completadas_por_usuario():
    filas = bd.session.execute(
        bd.select(ProgresoLeccionUsuario.usuario_id, bd.func.count())
        .where(ProgresoLeccionUsuario.estado == LECCION_COMPLETADA)
        .group_by(ProgresoLeccionUsuario.usuario_id)
    ).all()
    return {uid: n for uid, n in filas}


def listar():
    alumnos = bd.session.execute(
        bd.select(Usuario).where(Usuario.rol == ROL_ESTUDIANTE).order_by(Usuario.id)
    ).scalars().all()
    completadas = _completadas_por_usuario()
    total = len(desbloqueo.lecciones_ordenadas())
    salida = []
    for u in alumnos:
        est = estadisticas.obtener(u.id)
        s = estadisticas.a_dict(est)
        fila = _datos_estudiante(u)
        fila.update(
            xp_total=s["xp_total"], nivel=s["nivel"], racha_actual=s["racha_actual"],
            corazones=s["corazones"],
            lecciones_completadas=completadas.get(u.id, 0), total_lecciones=total,
            ultima_actividad=(
                est.ultima_fecha_actividad.isoformat() if est.ultima_fecha_actividad else None
            ),
        )
        salida.append(fila)
    return salida


def detalle(usuario_id):
    u = _estudiante(usuario_id)
    est = estadisticas.obtener(u.id)

    lecciones = desbloqueo.lecciones_ordenadas()
    estados = desbloqueo.estados_por_leccion(u.id, lecciones)
    progresos = {
        p.leccion_id: p for p in bd.session.execute(
            bd.select(ProgresoLeccionUsuario).where(ProgresoLeccionUsuario.usuario_id == u.id)
        ).scalars()
    }
    lista = []
    for l in lecciones:
        p = progresos.get(l.id)
        lista.append({
            "id": l.id, "titulo": l.titulo, "unidad_titulo": l.unidad.titulo,
            "unidad_orden": l.unidad.orden, "orden": l.orden, "estado": estados[l.id],
            "mejor_precision": p.mejor_precision if p else 0,
            "veces_completada": p.veces_completada if p else 0,
        })

    hoy = hoy_local()
    desde = hoy - timedelta(days=DIAS_ACTIVIDAD - 1)
    por_fecha = {
        a.fecha: a for a in bd.session.execute(
            bd.select(ActividadDiaria).where(
                ActividadDiaria.usuario_id == u.id, ActividadDiaria.fecha >= desde
            )
        ).scalars()
    }
    actividad = []
    for i in range(DIAS_ACTIVIDAD):
        dia = desde + timedelta(days=i)
        fila = por_fecha.get(dia)
        actividad.append({
            "fecha": dia.isoformat(), "activo": fila is not None,
            "xp": fila.xp_ganado if fila else 0,
            "lecciones": fila.lecciones_completadas if fila else 0,
        })

    fechas = {
        lu.logro_id: lu.desbloqueado_en for lu in bd.session.execute(
            bd.select(LogroUsuario).where(LogroUsuario.usuario_id == u.id)
        ).scalars()
    }
    logros = [
        {
            "codigo": lg.codigo, "nombre": lg.nombre,
            "desbloqueado": lg.id in fechas,
            "desbloqueado_en": fechas[lg.id].isoformat() if lg.id in fechas else None,
        }
        for lg in bd.session.execute(bd.select(Logro).order_by(Logro.id)).scalars()
    ]

    intentos = [
        {
            "id": i.id, "leccion_titulo": titulo, "estado": i.estado,
            "aciertos": i.aciertos, "errores": i.errores, "xp_ganado": i.xp_ganado,
            "iniciado_en": i.iniciado_en.isoformat() if i.iniciado_en else None,
        }
        for i, titulo in bd.session.execute(
            bd.select(IntentoLeccion, Leccion.titulo)
            .join(Leccion, Leccion.id == IntentoLeccion.leccion_id)
            .where(IntentoLeccion.usuario_id == u.id)
            .order_by(IntentoLeccion.id.desc()).limit(10)
        ).all()
    ]

    return {
        "estudiante": _datos_estudiante(u),
        "estadisticas": estadisticas.a_dict(est),
        "lecciones": lista,
        "actividad": actividad,
        "logros": logros,
        "intentos": intentos,
    }


def fijar_estadisticas(usuario_id, datos):
    _estudiante(usuario_id)
    est = estadisticas.obtener_bloqueada(usuario_id)
    cambio = False
    if "xp_total" in datos:
        xp = datos["xp_total"]
        if not es_entero(xp) or not 0 <= xp <= MAX_XP:
            raise _malo(f"«xp_total» debe ser un número entre 0 y {MAX_XP}.")
        est.xp_total = xp
        cambio = True
    if "corazones" in datos:
        c = datos["corazones"]
        if not es_entero(c) or not 0 <= c <= CORAZONES_MAXIMOS:
            raise _malo(f"«corazones» debe ser un número entre 0 y {CORAZONES_MAXIMOS}.")
        est.corazones = c
        est.fecha_corazones = hoy_local()  # que no se restauren hasta mañana
        cambio = True
    if not cambio:
        raise _malo("Indica «xp_total» y/o «corazones».")
    bd.session.commit()
    return estadisticas.a_dict(est)


def completar_hasta(usuario_id, leccion_id):
    """Marca como completadas esa lección y todas las anteriores. No da XP ni logros."""
    _estudiante(usuario_id)
    lecciones = desbloqueo.lecciones_ordenadas()
    ids = [l.id for l in lecciones]
    if leccion_id not in ids:
        raise ErrorAPI(404, "no_encontrado", "Lección no encontrada o no publicada.")

    existentes = {
        p.leccion_id: p for p in bd.session.execute(
            bd.select(ProgresoLeccionUsuario).where(ProgresoLeccionUsuario.usuario_id == usuario_id)
        ).scalars()
    }
    for l in lecciones[: ids.index(leccion_id) + 1]:
        p = existentes.get(l.id)
        if p is None:
            bd.session.add(ProgresoLeccionUsuario(
                usuario_id=usuario_id, leccion_id=l.id, estado=LECCION_COMPLETADA,
                mejor_precision=0, veces_completada=1, completada_en=bd.func.now(),
            ))
        elif p.estado != LECCION_COMPLETADA:
            p.estado = LECCION_COMPLETADA
            p.veces_completada = max(1, p.veces_completada)
            p.completada_en = p.completada_en or bd.func.now()
    bd.session.flush()
    n = bd.session.execute(
        bd.select(bd.func.count()).select_from(ProgresoLeccionUsuario).where(
            ProgresoLeccionUsuario.usuario_id == usuario_id,
            ProgresoLeccionUsuario.estado == LECCION_COMPLETADA,
        )
    ).scalar_one()
    bd.session.commit()
    return {"lecciones_completadas": n}


def reiniciar_leccion(usuario_id, leccion_id):
    """Borra el progreso de una lección y abandona sus intentos en curso."""
    _estudiante(usuario_id)
    if bd.session.get(Leccion, leccion_id) is None:
        raise ErrorAPI(404, "no_encontrado", "Lección no encontrada.")
    bd.session.execute(
        bd.delete(ProgresoLeccionUsuario).where(
            ProgresoLeccionUsuario.usuario_id == usuario_id,
            ProgresoLeccionUsuario.leccion_id == leccion_id,
        )
    )
    bd.session.execute(
        bd.update(IntentoLeccion).where(
            IntentoLeccion.usuario_id == usuario_id,
            IntentoLeccion.leccion_id == leccion_id,
            IntentoLeccion.estado == ESTADO_EN_CURSO,
        ).values(estado=ESTADO_ABANDONADO, finalizado_en=bd.func.now())
    )
    bd.session.commit()
    return {}


def reiniciar_todo(usuario_id, datos):
    """Borra progreso, intentos, actividad y logros, y deja las estadísticas en cero."""
    _estudiante(usuario_id)
    if datos.get("confirmar") is not True:
        raise _malo("Para reiniciar todo envía «confirmar»: true.")
    est = estadisticas.obtener_bloqueada(usuario_id)

    intentos = bd.select(IntentoLeccion.id).where(IntentoLeccion.usuario_id == usuario_id)
    bd.session.execute(
        bd.delete(RespuestaIntento).where(RespuestaIntento.intento_id.in_(intentos))
    )
    for modelo in (IntentoLeccion, ProgresoLeccionUsuario, ActividadDiaria, LogroUsuario):
        bd.session.execute(bd.delete(modelo).where(modelo.usuario_id == usuario_id))

    est.xp_total = 0
    est.racha_actual = 0
    est.mejor_racha = 0
    est.ultima_fecha_actividad = None
    est.corazones = CORAZONES_INICIALES
    est.fecha_corazones = hoy_local()
    bd.session.commit()
    return estadisticas.a_dict(est)