"""Ejercicios: cómo se muestran (sin respuestas) y cómo se evalúan (solo en el servidor).

Para añadir un tipo nuevo: una constante, una función evaluadora, y registrarla en
EVALUADORES. Si usa opciones, añadirlo también en presentar().

Las opciones y fichas se envían con ids opacos (0, 1, 2...) en orden barajado.
El barajado depende de SECRET_KEY, del intento y de la pregunta, así que el
servidor lo repite igual al evaluar, pero el navegador no puede deducir nada.
"""
import random

from flask import current_app

from servidor.errores import ErrorAPI
from servidor.servicios.normalizacion import normalizar

SELECCION = "seleccion"
COMPLETAR_OPCION = "completar_opcion"
TRADUCIR_ES_EN = "traducir_es_en"
TRADUCIR_EN_ES = "traducir_en_es"
COMPLETAR_TEXTO = "completar_texto"
ORDENAR_PALABRAS = "ordenar_palabras"

LARGO_MAXIMO_TEXTO = 300


def es_entero(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _invalida(mensaje):
    return ErrorAPI(400, "respuesta_invalida", mensaje)


def _correctas(pregunta):
    correctas = [o for o in pregunta.opciones if o.es_correcta]
    if not correctas:
        raise ErrorAPI(
            500, "contenido_invalido",
            "Esta pregunta tiene un problema. Avísale a quien administra el contenido.",
        )
    return correctas


def _barajar(intento_id, pregunta):
    """Opciones en el orden en que se muestran al estudiante."""
    originales = list(pregunta.opciones)
    piezas = list(originales)
    azar = random.Random(f"{current_app.config['SECRET_KEY']}|{intento_id}|{pregunta.id}")
    azar.shuffle(piezas)
    if pregunta.tipo == ORDENAR_PALABRAS and len(piezas) > 1:
        for _ in range(10):  # que no aparezcan ya en el orden correcto
            if [o.id for o in piezas] != [o.id for o in originales]:
                break
            azar.shuffle(piezas)
    return piezas


def presentar(intento_id, pregunta):
    """Datos de la pregunta para el navegador. Nunca incluye respuestas."""
    datos = {
        "id": pregunta.id,
        "tipo": pregunta.tipo,
        "instrucciones": pregunta.instrucciones,
        "texto": pregunta.texto,
    }
    if pregunta.tipo in (SELECCION, COMPLETAR_OPCION):
        datos["opciones"] = [
            {"id": i, "texto": o.texto} for i, o in enumerate(_barajar(intento_id, pregunta))
        ]
    elif pregunta.tipo == ORDENAR_PALABRAS:
        datos["fichas"] = [
            {"id": i, "texto": o.texto} for i, o in enumerate(_barajar(intento_id, pregunta))
        ]
    return datos


def respuesta_correcta(pregunta):
    """Texto de la respuesta correcta, para mostrarlo DESPUÉS de responder."""
    if pregunta.tipo == ORDENAR_PALABRAS:
        return " ".join(o.texto for o in pregunta.opciones)
    return _correctas(pregunta)[0].texto


def _evaluar_opcion(pregunta, respuesta, intento_id):
    piezas = _barajar(intento_id, pregunta)
    indice = respuesta.get("opcion")
    if not es_entero(indice) or not 0 <= indice < len(piezas):
        raise _invalida("Elige una opción.")
    elegida = piezas[indice]
    return bool(elegida.es_correcta), elegida.texto


def _evaluar_texto(pregunta, respuesta, intento_id):
    texto = respuesta.get("texto")
    if not isinstance(texto, str) or not texto.strip():
        raise _invalida("Escribe tu respuesta.")
    if len(texto) > LARGO_MAXIMO_TEXTO:
        raise _invalida("La respuesta es demasiado larga.")
    escrito = normalizar(texto)
    correcta = any(normalizar(o.texto) == escrito for o in _correctas(pregunta))
    return correcta, texto.strip()


def _evaluar_orden(pregunta, respuesta, intento_id):
    piezas = _barajar(intento_id, pregunta)
    n = len(piezas)
    indices = respuesta.get("orden")
    if (not isinstance(indices, list) or len(indices) != n
            or not all(es_entero(i) for i in indices)
            or sorted(indices) != list(range(n))):
        raise _invalida("Ordena todas las palabras.")
    enviado = [normalizar(piezas[i].texto) for i in indices]
    esperado = [normalizar(o.texto) for o in pregunta.opciones]
    return enviado == esperado, " ".join(piezas[i].texto for i in indices)


EVALUADORES = {
    SELECCION: _evaluar_opcion,
    COMPLETAR_OPCION: _evaluar_opcion,
    TRADUCIR_ES_EN: _evaluar_texto,
    TRADUCIR_EN_ES: _evaluar_texto,
    COMPLETAR_TEXTO: _evaluar_texto,
    ORDENAR_PALABRAS: _evaluar_orden,
}


def evaluar(pregunta, respuesta, intento_id):
    """Devuelve (es_correcta, texto_guardado). Lanza ErrorAPI si el formato es inválido."""
    evaluador = EVALUADORES.get(pregunta.tipo)
    if evaluador is None:
        raise ErrorAPI(500, "tipo_no_soportado", "Este tipo de ejercicio no está disponible.")
    return evaluador(pregunta, respuesta, intento_id)