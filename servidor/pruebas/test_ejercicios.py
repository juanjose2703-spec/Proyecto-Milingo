import pytest

from servidor.errores import ErrorAPI
from servidor.extensiones import bd
from servidor.modelos import Pregunta
from servidor.servicios import ejercicios
from servidor.servicios.carga_contenido import sincronizar_contenido
from servidor.servicios.normalizacion import normalizar


@pytest.fixture()
def contenido(app):
    sincronizar_contenido()
    bd.session.commit()


def _pregunta(tipo, excluir_id=None):
    consulta = bd.select(Pregunta).where(Pregunta.tipo == tipo).order_by(Pregunta.id)
    if excluir_id is not None:
        consulta = consulta.where(Pregunta.id != excluir_id)
    return bd.session.execute(consulta).scalars().first()


def test_normalizar():
    assert normalizar("  ¡Hola,   AMIGO! ") == "hola amigo"
    assert normalizar("Mamá") == "mama"
    assert normalizar("I'm Ana.") == normalizar("Im ana")
    assert normalizar("") == ""


def test_evaluar_texto(contenido):
    p = _pregunta("traducir_es_en")  # Hola -> Hello / Hi
    assert ejercicios.evaluar(p, {"texto": " hello! "}, 1)[0] is True
    assert ejercicios.evaluar(p, {"texto": "HI"}, 1)[0] is True
    assert ejercicios.evaluar(p, {"texto": "goodbye"}, 1)[0] is False
    with pytest.raises(ErrorAPI):
        ejercicios.evaluar(p, {"texto": "   "}, 1)
    with pytest.raises(ErrorAPI):
        ejercicios.evaluar(p, {}, 1)


def test_evaluar_orden(contenido):
    p = _pregunta("ordenar_palabras")
    fichas = ejercicios.presentar(1, p)["fichas"]
    assert [f["texto"] for f in fichas] != [o.texto for o in p.opciones]

    libres = list(fichas)
    correcto = []
    for o in p.opciones:
        ficha = next(f for f in libres if f["texto"] == o.texto)
        libres.remove(ficha)
        correcto.append(ficha["id"])

    assert ejercicios.evaluar(p, {"orden": correcto}, 1)[0] is True
    assert ejercicios.evaluar(p, {"orden": correcto[::-1]}, 1)[0] is False

    n = len(correcto)
    malos = [
        {"orden": correcto[:-1]},
        {"orden": correcto + correcto[:1]},
        {"orden": [correcto[0]] * n},
        {"orden": "abc"},
        {"orden": [True] * n},
    ]
    for malo in malos:
        with pytest.raises(ErrorAPI):
            ejercicios.evaluar(p, malo, 1)


def test_evaluar_opcion_invalida(contenido):
    p = _pregunta("seleccion")
    mostradas = ejercicios.presentar(1, p)["opciones"]
    correcta = next(o.texto for o in p.opciones if o.es_correcta)
    indice = next(o["id"] for o in mostradas if o["texto"] == correcta)
    assert ejercicios.evaluar(p, {"opcion": indice}, 1)[0] is True

    for malo in ({"opcion": 99}, {"opcion": -1}, {"opcion": "1"}, {"opcion": True}, {}):
        with pytest.raises(ErrorAPI):
            ejercicios.evaluar(p, malo, 1)