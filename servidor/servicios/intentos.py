"""Intentos de lección: el servidor controla qué pregunta toca, evalúa las respuestas,
descuenta corazones y, al terminar, calcula XP, racha y logros en una transacción.

Reglas (ver también reglas.py):
  - Reanudar: si ya hay un intento en curso de esa lección, se continúa donde quedó.
  - Salir: el intento queda 'abandonado', sin XP. Los corazones perdidos no se devuelven.
  - Sin corazones: el intento termina ('sin_corazones') sin XP.
  - Repetir una respuesta o un cierre es idempotente: no duplica nada.
"""
from datetime import timedelta

from servidor.errores import ErrorAPI
from servidor.extensiones import bd
from servidor.modelos import (
    ActividadDiaria, IntentoLeccion, Leccion, Pregunta,
    ProgresoLeccionUsuario, RespuestaIntento,
)
from servidor.servicios import desbloqueo, ejercicios, estadisticas, logros
from servidor.servicios.fechas import hoy_local
from servidor.servicios.reglas import (
    CORAZONES_MAXIMOS, ESTADO_ABANDONADO, ESTADO_COMPLETADO, ESTADO_EN_CURSO,
    ESTADO_SIN_CORAZONES, FACTOR_REPETICION, LECCION_BLOQUEADA, LECCION_COMPLETADA,
    XP_POR_ACIERTO,
)


# ---------- Utilidades ----------

def _leccion_publicada(leccion_id):
    leccion = bd.session.get(Leccion, leccion_id)
    if (leccion is None or not leccion.publicada
            or not leccion.unidad.publicado or not leccion.unidad.curso.publicado):
        raise ErrorAPI(404, "no_encontrado", "Lección no encontrada.")
    return leccion


def _preguntas(leccion_id):
    return bd.session.execute(
        bd.select(Pregunta)
        .where(Pregunta.leccion_id == leccion_id, Pregunta.publicada.is_(True))
        .order_by(Pregunta.orden)
    ).scalars().all()


def _respondidas(intento_id):
    return {
        r.pregunta_id: r
        for r in bd.session.execute(
            bd.select(RespuestaIntento).where(RespuestaIntento.intento_id == intento_id)
        ).scalars()
    }


def _intento_del_usuario(usuario_id, intento_id):
    intento = bd.session.get(IntentoLeccion, intento_id)
    if intento is None or intento.usuario_id != usuario_id:
        raise ErrorAPI(404, "no_encontrado", "Intento no encontrado.")
    return intento


def _estado_intento(intento, est, preguntas, respondidas):
    pendientes = [p for p in preguntas if p.id not in respondidas]
    pregunta = None
    if intento.estado == ESTADO_EN_CURSO and pendientes:
        pregunta = ejercicios.presentar(intento.id, pendientes[0])
    return {
        "intento_id": intento.id,
        "leccion_id": intento.leccion_id,
        "estado": intento.estado,
        "total": len(respondidas) + len(pendientes),
        "respondidas": len(respondidas),
        "aciertos": intento.aciertos,
        "errores": intento.errores,
        "corazones": est.corazones,
        "corazones_maximos": CORAZONES_MAXIMOS,
        "pregunta": pregunta,
    }


# ---------- Iniciar o reanudar ----------

def iniciar(usuario_id, leccion_id):
    est = estadisticas.obtener_bloqueada(usuario_id)
    leccion = _leccion_publicada(leccion_id)

    estados = desbloqueo.estados_por_leccion(usuario_id)
    if estados.get(leccion.id, LECCION_BLOQUEADA) == LECCION_BLOQUEADA:
        raise ErrorAPI(403, "leccion_bloqueada", "Esta lección todavía está bloqueada.")

    preguntas = _preguntas(leccion.id)
    if not preguntas:
        raise ErrorAPI(409, "leccion_vacia", "Esta lección aún no tiene preguntas.")

    intento = bd.session.execute(
        bd.select(IntentoLeccion)
        .where(
            IntentoLeccion.usuario_id == usuario_id,
            IntentoLeccion.leccion_id == leccion.id,
            IntentoLeccion.estado == ESTADO_EN_CURSO,
        )
        .order_by(IntentoLeccion.id.desc())
    ).scalars().first()

    reanudado = intento is not None
    if intento is None:
        if est.corazones <= 0:
            raise ErrorAPI(
                409, "sin_corazones",
                "No te quedan corazones por hoy. Vuelven mañana.",
            )
        intento = IntentoLeccion(
            usuario_id=usuario_id, leccion_id=leccion.id, estado=ESTADO_EN_CURSO,
            aciertos=0, errores=0, xp_ganado=0,
        )
        bd.session.add(intento)
        bd.session.flush()

    datos = _estado_intento(intento, est, preguntas, _respondidas(intento.id))
    datos["reanudado"] = reanudado
    bd.session.commit()
    return datos


# ---------- Responder ----------

def _resultado_respuesta(intento, est, preguntas, respondidas, pregunta, correcta, repetida):
    pendientes = [p for p in preguntas if p.id not in respondidas]
    terminado = "sin_corazones" if intento.estado == ESTADO_SIN_CORAZONES else None
    siguiente = None
    if intento.estado == ESTADO_EN_CURSO and pendientes:
        siguiente = ejercicios.presentar(intento.id, pendientes[0])
    return {
        "correcta": bool(correcta),
        "respuesta_correcta": ejercicios.respuesta_correcta(pregunta),
        "explicacion": pregunta.explicacion,
        "corazones": est.corazones,
        "aciertos": intento.aciertos,
        "errores": intento.errores,
        "respondidas": len(respondidas),
        "total": len(respondidas) + len(pendientes),
        "terminado": terminado,
        "listo_para_completar": intento.estado == ESTADO_EN_CURSO and not pendientes,
        "siguiente_pregunta": siguiente,
        "repetida": repetida,
    }


def responder(usuario_id, intento_id, datos):
    est = estadisticas.obtener_bloqueada(usuario_id)
    intento = _intento_del_usuario(usuario_id, intento_id)
    preguntas = _preguntas(intento.leccion_id)
    respondidas = _respondidas(intento.id)

    pregunta_id = datos.get("pregunta_id")
    if not ejercicios.es_entero(pregunta_id):
        raise ErrorAPI(400, "datos_invalidos", "Falta indicar la pregunta.")

    # Petición repetida: se devuelve lo ya guardado, sin cambiar nada.
    previa = respondidas.get(pregunta_id)
    if previa is not None:
        pregunta = bd.session.get(Pregunta, pregunta_id)
        return _resultado_respuesta(
            intento, est, preguntas, respondidas, pregunta, previa.es_correcta, True
        )

    if intento.estado != ESTADO_EN_CURSO:
        raise ErrorAPI(409, "intento_cerrado", "Este intento ya terminó.")

    pendientes = [p for p in preguntas if p.id not in respondidas]
    if not pendientes:
        raise ErrorAPI(409, "intento_completo", "Ya respondiste todo. Termina la lección.")
    actual = pendientes[0]
    if pregunta_id != actual.id:
        raise ErrorAPI(409, "pregunta_incorrecta", "Esa no es la pregunta que toca ahora.")

    correcta, guardado = ejercicios.evaluar(actual, datos, intento.id)

    fila = RespuestaIntento(
        intento_id=intento.id, pregunta_id=actual.id,
        respuesta_usuario=guardado, es_correcta=correcta,
    )
    bd.session.add(fila)
    if correcta:
        intento.aciertos += 1
    else:
        intento.errores += 1
        est.corazones = max(0, est.corazones - 1)
        if est.corazones == 0:
            intento.estado = ESTADO_SIN_CORAZONES
            intento.finalizado_en = bd.func.now()
    bd.session.flush()

    respondidas[actual.id] = fila
    resultado = _resultado_respuesta(
        intento, est, preguntas, respondidas, actual, correcta, False
    )
    bd.session.commit()
    return resultado


# ---------- Completar ----------

def _resultado_final(intento, est, usuario_id, nuevos, repetido, repeticion):
    total = intento.aciertos + intento.errores
    precision = round(100 * intento.aciertos / total) if total else 0
    lecciones = desbloqueo.lecciones_ordenadas()
    estados = desbloqueo.estados_por_leccion(usuario_id, lecciones)
    siguiente = desbloqueo.siguiente_leccion(lecciones, estados)
    return {
        "intento_id": intento.id,
        "leccion_id": intento.leccion_id,
        "aciertos": intento.aciertos,
        "errores": intento.errores,
        "total": total,
        "precision": precision,
        "xp_ganado": intento.xp_ganado,
        "repeticion": repeticion,
        "repetido": repetido,
        "estadisticas": estadisticas.a_dict(est),
        "logros_nuevos": [logros.a_dict(l) for l in nuevos],
        "siguiente_leccion": None if siguiente is None else {
            "id": siguiente.id, "titulo": siguiente.titulo,
        },
    }


def completar(usuario_id, intento_id):
    est = estadisticas.obtener_bloqueada(usuario_id)
    intento = _intento_del_usuario(usuario_id, intento_id)

    if intento.estado == ESTADO_COMPLETADO:  # petición repetida: nada nuevo
        resultado = _resultado_final(intento, est, usuario_id, [], True, False)
        bd.session.commit()
        return resultado
    if intento.estado != ESTADO_EN_CURSO:
        raise ErrorAPI(409, "intento_cerrado", "Este intento terminó sin completarse.")

    preguntas = _preguntas(intento.leccion_id)
    respondidas = _respondidas(intento.id)
    if not respondidas or any(p.id not in respondidas for p in preguntas):
        raise ErrorAPI(409, "intento_incompleto", "Todavía te faltan preguntas por responder.")

    # El resultado se calcula con lo guardado, nunca con lo que diga el navegador.
    aciertos = sum(1 for r in respondidas.values() if r.es_correcta)
    total = len(respondidas)
    intento.aciertos = aciertos
    intento.errores = total - aciertos
    precision = round(100 * aciertos / total)

    leccion = bd.session.get(Leccion, intento.leccion_id)
    progreso = bd.session.execute(
        bd.select(ProgresoLeccionUsuario).where(
            ProgresoLeccionUsuario.usuario_id == usuario_id,
            ProgresoLeccionUsuario.leccion_id == leccion.id,
        )
    ).scalar_one_or_none()
    es_repeticion = progreso is not None and progreso.estado == LECCION_COMPLETADA

    xp = leccion.xp_base + XP_POR_ACIERTO * aciertos
    if es_repeticion:
        xp = int(xp * FACTOR_REPETICION)

    if progreso is None:
        progreso = ProgresoLeccionUsuario(
            usuario_id=usuario_id, leccion_id=leccion.id, estado=LECCION_COMPLETADA,
            mejor_precision=precision, veces_completada=1, completada_en=bd.func.now(),
        )
        bd.session.add(progreso)
    else:
        progreso.estado = LECCION_COMPLETADA
        progreso.mejor_precision = max(progreso.mejor_precision, precision)
        progreso.veces_completada += 1
        if progreso.completada_en is None:
            progreso.completada_en = bd.func.now()

    # XP y racha (como máximo +1 por día local).
    hoy = hoy_local()
    if est.ultima_fecha_actividad == hoy:
        pass
    elif est.ultima_fecha_actividad == hoy - timedelta(days=1):
        est.racha_actual += 1
    else:
        est.racha_actual = 1
    est.ultima_fecha_actividad = hoy
    est.mejor_racha = max(est.mejor_racha, est.racha_actual)
    est.xp_total += xp

    actividad = bd.session.execute(
        bd.select(ActividadDiaria).where(
            ActividadDiaria.usuario_id == usuario_id, ActividadDiaria.fecha == hoy
        )
    ).scalar_one_or_none()
    if actividad is None:
        bd.session.add(ActividadDiaria(
            usuario_id=usuario_id, fecha=hoy, xp_ganado=xp, lecciones_completadas=1,
        ))
    else:
        actividad.xp_ganado += xp
        actividad.lecciones_completadas += 1

    intento.estado = ESTADO_COMPLETADO
    intento.xp_ganado = xp
    intento.finalizado_en = bd.func.now()

    nuevos = logros.conceder_nuevos(usuario_id, est, precision)
    bd.session.flush()
    resultado = _resultado_final(intento, est, usuario_id, nuevos, False, es_repeticion)
    bd.session.commit()
    return resultado


# ---------- Abandonar ----------

def abandonar(usuario_id, intento_id):
    estadisticas.obtener_bloqueada(usuario_id)
    intento = _intento_del_usuario(usuario_id, intento_id)
    if intento.estado == ESTADO_EN_CURSO:
        intento.estado = ESTADO_ABANDONADO
        intento.finalizado_en = bd.func.now()
    estado = intento.estado
    bd.session.commit()
    return {"intento_id": intento_id, "estado": estado}