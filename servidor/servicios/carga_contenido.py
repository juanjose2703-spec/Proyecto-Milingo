"""Carga reproducible del contenido. Se puede ejecutar varias veces sin duplicar.

Busca cada elemento por su clave natural (título, o posición dentro del padre),
lo crea si falta y lo actualiza si ya existe. Ojo: si editas desde el panel de
administración algo que también está en estos archivos, la próxima carga
volverá a poner el texto del archivo.
"""
from servidor.contenido.a1 import CURSO_A1
from servidor.contenido.logros import LOGROS
from servidor.extensiones import bd
from servidor.modelos import Curso, Unidad, Leccion, Pregunta, OpcionRespuesta, Logro
from servidor.servicios.reglas import XP_BASE_LECCION


def _upsert(modelo, claves, valores):
    obj = bd.session.execute(bd.select(modelo).filter_by(**claves)).scalar_one_or_none()
    if obj is None:
        obj = modelo(**claves, **valores)
        bd.session.add(obj)
    else:
        for campo, valor in valores.items():
            setattr(obj, campo, valor)
    bd.session.flush()
    return obj


def _sincronizar_opciones(pregunta, opciones):
    nuevas = [(texto, correcta, i) for i, (texto, correcta) in enumerate(opciones, 1)]
    actuales = [
        (o.texto, o.es_correcta, o.orden)
        for o in bd.session.execute(
            bd.select(OpcionRespuesta)
            .where(OpcionRespuesta.pregunta_id == pregunta.id)
            .order_by(OpcionRespuesta.orden)
        ).scalars()
    ]
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


def sincronizar_contenido():
    """No hace commit: quien llama decide cuándo confirmar."""
    for datos in LOGROS:
        _upsert(Logro, {"codigo": datos["codigo"]}, {
            "nombre": datos["nombre"],
            "descripcion": datos["descripcion"],
            "icono": datos["icono"],
        })

    curso = _upsert(Curso, {"titulo": CURSO_A1["titulo"]}, {
        "descripcion": CURSO_A1["descripcion"],
        "nivel": CURSO_A1["nivel"],
        "orden": CURSO_A1["orden"],
        "publicado": True,
    })

    for n_unidad, datos_unidad in enumerate(CURSO_A1["unidades"], 1):
        unidad = _upsert(Unidad, {"curso_id": curso.id, "orden": n_unidad}, {
            "titulo": datos_unidad["titulo"],
            "descripcion": datos_unidad["descripcion"],
            "publicado": True,
        })
        for n_leccion, datos_leccion in enumerate(datos_unidad["lecciones"], 1):
            leccion = _upsert(Leccion, {"unidad_id": unidad.id, "orden": n_leccion}, {
                "titulo": datos_leccion["titulo"],
                "descripcion": datos_leccion["descripcion"],
                "xp_base": XP_BASE_LECCION,
                "publicada": True,
            })
            for n_pregunta, datos_pregunta in enumerate(datos_leccion["preguntas"], 1):
                pregunta = _upsert(Pregunta, {"leccion_id": leccion.id, "orden": n_pregunta}, {
                    "tipo": datos_pregunta["tipo"],
                    "instrucciones": datos_pregunta["instrucciones"],
                    "texto": datos_pregunta["texto"],
                    "explicacion": datos_pregunta["explicacion"],
                    "publicada": True,
                })
                _sincronizar_opciones(pregunta, datos_pregunta["opciones"])