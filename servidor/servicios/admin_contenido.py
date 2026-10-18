"""Administración del contenido (solo administrador).

Reglas:
  - Lo nuevo nace sin publicar (excepto las preguntas, que nacen publicadas).
  - Una lección solo se publica con al menos una pregunta publicada, y no puede
    quedarse sin ellas mientras esté publicada (bloquearía el recorrido).
  - No se borra contenido con intentos o respuestas de estudiantes: se despublica.
  - mover() intercambia el orden con el vecino.
  - Las opciones se guardan con la pregunta y se reemplazan completas.
"""
from sqlalchemy import true

from servidor.errores import ErrorAPI
from servidor.extensiones import bd
from servidor.modelos import (
    Curso, IntentoLeccion, Leccion, OpcionRespuesta, Pregunta,
    ProgresoLeccionUsuario, RespuestaIntento, Unidad,
)
from servidor.servicios import ejercicios as ej
from servidor.servicios.normalizacion import normalizar
from servidor.servicios.reglas import XP_BASE_LECCION

TIPOS_OPCION = (ej.SELECCION, ej.COMPLETAR_OPCION)
TIPOS_HUECO = (ej.COMPLETAR_OPCION, ej.COMPLETAR_TEXTO)
TIPOS = TIPOS_OPCION + (
    ej.TRADUCIR_ES_EN, ej.TRADUCIR_EN_ES, ej.COMPLETAR_TEXTO, ej.ORDENAR_PALABRAS,
)
MAX_OPCIONES = 12

CAMPOS_CURSO = {"titulo": (120, True), "descripcion": (2000, False), "nivel": (10, False)}
CAMPOS_UNIDAD = {"titulo": (120, True), "descripcion": (255, False)}
CAMPOS_LECCION = {"titulo": (120, True), "descripcion": (255, False)}
CAMPOS_PREGUNTA = {
    "texto": (500, True), "instrucciones": (255, False), "explicacion": (2000, False),
}


# ---------- Utilidades ----------

def _malo(mensaje):
    return ErrorAPI(400, "datos_invalidos", mensaje)


def _leer(datos, campos, parcial):
    """campos: {nombre: (maximo, obligatorio)}. Devuelve solo los campos presentes y válidos."""
    salida = {}
    for nombre, (maximo, obligatorio) in campos.items():
        if nombre not in datos:
            if obligatorio and not parcial:
                raise _malo(f"Falta el campo «{nombre}».")
            continue
        valor = datos[nombre]
        if valor is None and not obligatorio:
            salida[nombre] = None
            continue
        if not isinstance(valor, str):
            raise _malo(f"«{nombre}» debe ser texto.")
        valor = valor.strip()
        if not valor:
            if obligatorio:
                raise _malo(f"«{nombre}» no puede estar vacío.")
            valor = None
        elif len(valor) > maximo:
            raise _malo(f"«{nombre}» admite máximo {maximo} caracteres.")
        salida[nombre] = valor
    return salida


def _booleano(datos, campo):
    if campo not in datos:
        return None
    if not isinstance(datos[campo], bool):
        raise _malo(f"«{campo}» debe ser verdadero o falso.")
    return datos[campo]


def _entero(datos, campo, minimo, maximo):
    if campo not in datos:
        return None
    valor = datos[campo]
    if not ej.es_entero(valor) or not minimo <= valor <= maximo:
        raise _malo(f"«{campo}» debe ser un número entre {minimo} y {maximo}.")
    return valor


def _obtener(modelo, id_, mensaje):
    obj = bd.session.get(modelo, id_)
    if obj is None:
        raise ErrorAPI(404, "no_encontrado", mensaje)
    return obj


def obtener_curso(id_):
    return _obtener(Curso, id_, "Curso no encontrado.")


def obtener_unidad(id_):
    return _obtener(Unidad, id_, "Unidad no encontrada.")


def obtener_leccion(id_):
    return _obtener(Leccion, id_, "Lección no encontrada.")


def obtener_pregunta(id_):
    return _obtener(Pregunta, id_, "Pregunta no encontrada.")


def _siguiente_orden(modelo, condicion):
    maximo = bd.session.execute(
        bd.select(bd.func.max(modelo.orden)).where(condicion)
    ).scalar()
    return (maximo or 0) + 1


def _publicadas(leccion_id, excluyendo=None):
    consulta = bd.select(bd.func.count()).select_from(Pregunta).where(
        Pregunta.leccion_id == leccion_id, Pregunta.publicada.is_(True)
    )
    if excluyendo is not None:
        consulta = consulta.where(Pregunta.id != excluyendo)
    return bd.session.execute(consulta).scalar_one()


def _verificar_no_queda_vacia(leccion, excluyendo_id):
    if leccion.publicada and _publicadas(leccion.id, excluyendo_id) == 0:
        raise ErrorAPI(
            409, "leccion_vacia",
            "La lección está publicada y se quedaría sin preguntas. "
            "Despublica la lección primero, o añade otra pregunta.",
        )


# ---------- Serializadores ----------

def curso_dict(c):
    return {"id": c.id, "titulo": c.titulo, "descripcion": c.descripcion,
            "nivel": c.nivel, "orden": c.orden, "publicado": c.publicado}


def unidad_dict(u):
    return {"id": u.id, "curso_id": u.curso_id, "titulo": u.titulo,
            "descripcion": u.descripcion, "orden": u.orden, "publicado": u.publicado}


def leccion_dict(l):
    return {"id": l.id, "unidad_id": l.unidad_id, "titulo": l.titulo,
            "descripcion": l.descripcion, "orden": l.orden, "xp_base": l.xp_base,
            "publicada": l.publicada}


def pregunta_dict(p):
    return {
        "id": p.id, "leccion_id": p.leccion_id, "tipo": p.tipo,
        "instrucciones": p.instrucciones, "texto": p.texto,
        "explicacion": p.explicacion, "orden": p.orden, "publicada": p.publicada,
        "opciones": [
            {"texto": o.texto, "es_correcta": o.es_correcta, "orden": o.orden}
            for o in p.opciones
        ],
    }


def arbol():
    """Todo el contenido (publicado o no), con conteos de preguntas."""
    cursos = bd.session.execute(bd.select(Curso).order_by(Curso.orden)).scalars().all()
    salida = []
    for c in cursos:
        datos = curso_dict(c)
        datos["unidades"] = []
        for u in c.unidades:
            du = unidad_dict(u)
            du["lecciones"] = []
            for l in u.lecciones:
                dl = leccion_dict(l)
                dl["num_preguntas"] = len(l.preguntas)
                dl["num_publicadas"] = sum(1 for p in l.preguntas if p.publicada)
                du["lecciones"].append(dl)
            datos["unidades"].append(du)
        salida.append(datos)
    return salida


# ---------- Cursos, unidades y lecciones ----------

def _validar_titulo_curso(titulo, excluir_id=None):
    consulta = bd.select(Curso.id).where(Curso.titulo == titulo)
    if excluir_id is not None:
        consulta = consulta.where(Curso.id != excluir_id)
    if bd.session.execute(consulta).first():
        raise ErrorAPI(409, "duplicado", "Ya existe un curso con ese título.")


def crear_curso(datos):
    valores = _leer(datos, CAMPOS_CURSO, parcial=False)
    _validar_titulo_curso(valores["titulo"])
    valores["nivel"] = valores.get("nivel") or "A1"
    curso = Curso(
        **valores, orden=_siguiente_orden(Curso, true()),
        publicado=bool(_booleano(datos, "publicado")),
    )
    bd.session.add(curso)
    bd.session.commit()
    return curso_dict(curso)


def crear_unidad(curso_id, datos):
    curso = obtener_curso(curso_id)
    valores = _leer(datos, CAMPOS_UNIDAD, parcial=False)
    unidad = Unidad(
        **valores, curso_id=curso.id,
        orden=_siguiente_orden(Unidad, Unidad.curso_id == curso.id),
        publicado=bool(_booleano(datos, "publicado")),
    )
    bd.session.add(unidad)
    bd.session.commit()
    return unidad_dict(unidad)


def crear_leccion(unidad_id, datos):
    """Las lecciones nacen sin publicar: primero hay que añadirles preguntas."""
    unidad = obtener_unidad(unidad_id)
    valores = _leer(datos, CAMPOS_LECCION, parcial=False)
    xp = _entero(datos, "xp_base", 0, 1000)
    leccion = Leccion(
        **valores, unidad_id=unidad.id,
        orden=_siguiente_orden(Leccion, Leccion.unidad_id == unidad.id),
        xp_base=XP_BASE_LECCION if xp is None else xp, publicada=False,
    )
    bd.session.add(leccion)
    bd.session.commit()
    return leccion_dict(leccion)


def editar_curso(id_, datos):
    curso = obtener_curso(id_)
    valores = _leer(datos, CAMPOS_CURSO, parcial=True)
    if "titulo" in valores:
        _validar_titulo_curso(valores["titulo"], curso.id)
    if "nivel" in valores and valores["nivel"] is None:
        raise _malo("El nivel no puede quedar vacío.")
    for campo, valor in valores.items():
        setattr(curso, campo, valor)
    publicado = _booleano(datos, "publicado")
    if publicado is not None:
        curso.publicado = publicado
    bd.session.commit()
    return curso_dict(curso)


def editar_unidad(id_, datos):
    unidad = obtener_unidad(id_)
    for campo, valor in _leer(datos, CAMPOS_UNIDAD, parcial=True).items():
        setattr(unidad, campo, valor)
    publicado = _booleano(datos, "publicado")
    if publicado is not None:
        unidad.publicado = publicado
    bd.session.commit()
    return unidad_dict(unidad)


def editar_leccion(id_, datos):
    leccion = obtener_leccion(id_)
    valores = _leer(datos, CAMPOS_LECCION, parcial=True)
    xp = _entero(datos, "xp_base", 0, 1000)
    publicada = _booleano(datos, "publicada")
    if publicada and _publicadas(leccion.id) == 0:
        raise ErrorAPI(
            409, "sin_preguntas",
            "Para publicar la lección necesitas al menos una pregunta publicada.",
        )
    for campo, valor in valores.items():
        setattr(leccion, campo, valor)
    if xp is not None:
        leccion.xp_base = xp
    if publicada is not None:
        leccion.publicada = publicada
    bd.session.commit()
    return leccion_dict(leccion)


# ---------- Preguntas ----------

def _validar_pregunta(tipo, texto, opciones):
    """Devuelve las opciones limpias [(texto, es_correcta)] o lanza ErrorAPI 400."""
    if tipo not in TIPOS:
        raise _malo("Tipo de ejercicio no válido.")
    if tipo in TIPOS_HUECO and "___" not in texto:
        raise _malo("El texto debe incluir el hueco «___».")
    if not isinstance(opciones, list) or not 1 <= len(opciones) <= MAX_OPCIONES:
        raise _malo(f"Indica entre 1 y {MAX_OPCIONES} opciones.")

    limpias = []
    for o in opciones:
        if not isinstance(o, dict) or not isinstance(o.get("texto"), str):
            raise _malo("Cada opción necesita un texto.")
        t = o["texto"].strip()
        if not t or not normalizar(t):
            raise _malo("Hay una opción vacía.")
        if len(t) > 255:
            raise _malo("Una opción es demasiado larga (máximo 255 caracteres).")
        correcta = o.get("es_correcta", False)
        if not isinstance(correcta, bool):
            raise _malo("«es_correcta» debe ser verdadero o falso.")
        limpias.append((t, correcta))

    if tipo in TIPOS_OPCION:
        if len(limpias) < 2:
            raise _malo("Añade al menos 2 opciones.")
        if sum(1 for _, c in limpias if c) != 1:
            raise _malo("Marca exactamente una opción correcta.")
    else:
        # Respuestas escritas: todas son aceptadas. Ordenar: todas son fichas en orden.
        limpias = [(t, True) for t, _ in limpias]
        if tipo == ej.ORDENAR_PALABRAS and len(limpias) < 2:
            raise _malo("Añade al menos 2 palabras.")

    if tipo != ej.ORDENAR_PALABRAS:  # al ordenar, una palabra puede repetirse
        normalizadas = [normalizar(t) for t, _ in limpias]
        if len(set(normalizadas)) != len(normalizadas):
            raise _malo("Hay opciones repetidas.")
    return limpias


def _guardar_opciones(pregunta, limpias):
    nuevas = [(t, c, i) for i, (t, c) in enumerate(limpias, 1)]
    actuales = [(o.texto, o.es_correcta, o.orden) for o in pregunta.opciones]
    if actuales == nuevas:
        return
    # Se borra antes de insertar para no chocar con la restricción única (pregunta, orden).
    bd.session.execute(
        bd.delete(OpcionRespuesta).where(OpcionRespuesta.pregunta_id == pregunta.id)
    )
    bd.session.flush()
    for texto, correcta, orden in nuevas:
        bd.session.add(OpcionRespuesta(
            pregunta_id=pregunta.id, texto=texto, es_correcta=correcta, orden=orden,
        ))
    bd.session.flush()
    bd.session.expire(pregunta, ["opciones"])


def listar_preguntas(leccion_id):
    leccion = obtener_leccion(leccion_id)
    return {
        "leccion": leccion_dict(leccion),
        "preguntas": [pregunta_dict(p) for p in leccion.preguntas],
    }


def crear_pregunta(leccion_id, datos):
    leccion = obtener_leccion(leccion_id)
    tipo = datos.get("tipo")
    if not isinstance(tipo, str):
        raise _malo("Falta el tipo de ejercicio.")
    valores = _leer(datos, CAMPOS_PREGUNTA, parcial=False)
    limpias = _validar_pregunta(tipo, valores["texto"], datos.get("opciones"))
    publicada = _booleano(datos, "publicada")

    pregunta = Pregunta(
        **valores, tipo=tipo, leccion_id=leccion.id,
        orden=_siguiente_orden(Pregunta, Pregunta.leccion_id == leccion.id),
        publicada=True if publicada is None else publicada,
    )
    bd.session.add(pregunta)
    bd.session.flush()
    _guardar_opciones(pregunta, limpias)
    bd.session.commit()
    return pregunta_dict(pregunta)


def editar_pregunta(id_, datos):
    pregunta = obtener_pregunta(id_)
    valores = _leer(datos, CAMPOS_PREGUNTA, parcial=True)
    tipo = datos.get("tipo", pregunta.tipo)
    if not isinstance(tipo, str):
        raise _malo("El tipo de ejercicio no es válido.")
    texto = valores.get("texto", pregunta.texto)
    if "opciones" in datos:
        opciones = datos["opciones"]
    else:
        opciones = [{"texto": o.texto, "es_correcta": o.es_correcta} for o in pregunta.opciones]
    limpias = _validar_pregunta(tipo, texto, opciones)

    publicada = _booleano(datos, "publicada")
    if publicada is False and pregunta.publicada:
        _verificar_no_queda_vacia(pregunta.leccion, pregunta.id)

    pregunta.tipo = tipo
    for campo, valor in valores.items():
        setattr(pregunta, campo, valor)
    if publicada is not None:
        pregunta.publicada = publicada
    bd.session.flush()
    _guardar_opciones(pregunta, limpias)
    bd.session.commit()
    return pregunta_dict(pregunta)


# ---------- Editar, borrar y mover (por tipo) ----------

_EDITAR = {
    "curso": editar_curso, "unidad": editar_unidad,
    "leccion": editar_leccion, "pregunta": editar_pregunta,
}


def editar(tipo, id_, datos):
    return _EDITAR[tipo](id_, datos)


def _bloquear_si_hay_actividad(leccion_ids):
    if not leccion_ids:
        return
    intentos = bd.session.execute(
        bd.select(bd.func.count()).select_from(IntentoLeccion)
        .where(IntentoLeccion.leccion_id.in_(leccion_ids))
    ).scalar_one()
    progreso = bd.session.execute(
        bd.select(bd.func.count()).select_from(ProgresoLeccionUsuario)
        .where(ProgresoLeccionUsuario.leccion_id.in_(leccion_ids))
    ).scalar_one()
    if intentos or progreso:
        raise ErrorAPI(
            409, "tiene_actividad",
            "Hay intentos o progreso de estudiantes en este contenido. "
            "Despublícalo en lugar de borrarlo.",
        )


def borrar(tipo, id_):
    if tipo == "curso":
        obj = obtener_curso(id_)
        _bloquear_si_hay_actividad([l.id for u in obj.unidades for l in u.lecciones])
    elif tipo == "unidad":
        obj = obtener_unidad(id_)
        _bloquear_si_hay_actividad([l.id for l in obj.lecciones])
    elif tipo == "leccion":
        obj = obtener_leccion(id_)
        _bloquear_si_hay_actividad([obj.id])
    else:
        obj = obtener_pregunta(id_)
        respuestas = bd.session.execute(
            bd.select(bd.func.count()).select_from(RespuestaIntento)
            .where(RespuestaIntento.pregunta_id == obj.id)
        ).scalar_one()
        if respuestas:
            raise ErrorAPI(
                409, "tiene_actividad",
                "Hay respuestas de estudiantes a esta pregunta. Despublícala en lugar de borrarla.",
            )
        _verificar_no_queda_vacia(obj.leccion, obj.id)
    bd.session.delete(obj)  # el borrado en cascada se encarga de los hijos
    bd.session.commit()


_OBTENER = {
    "curso": obtener_curso, "unidad": obtener_unidad,
    "leccion": obtener_leccion, "pregunta": obtener_pregunta,
}
_HERMANOS = {
    "curso": lambda o: true(),
    "unidad": lambda o: Unidad.curso_id == o.curso_id,
    "leccion": lambda o: Leccion.unidad_id == o.unidad_id,
    "pregunta": lambda o: Pregunta.leccion_id == o.leccion_id,
}


def mover(tipo, id_, direccion):
    """Intercambia el orden con el vecino. Devuelve True si se movió."""
    if direccion not in ("arriba", "abajo"):
        raise _malo("La dirección debe ser «arriba» o «abajo».")
    obj = _OBTENER[tipo](id_)
    modelo = type(obj)
    consulta = bd.select(modelo).where(_HERMANOS[tipo](obj))
    if direccion == "arriba":
        consulta = consulta.where(modelo.orden < obj.orden).order_by(modelo.orden.desc())
    else:
        consulta = consulta.where(modelo.orden > obj.orden).order_by(modelo.orden.asc())
    vecino = bd.session.execute(consulta).scalars().first()
    if vecino is None:
        return False

    # El orden es único dentro del padre: se pasa por un valor temporal.
    a, b = obj.orden, vecino.orden
    obj.orden = -1
    bd.session.flush()
    vecino.orden = a
    bd.session.flush()
    obj.orden = b
    bd.session.commit()
    return True