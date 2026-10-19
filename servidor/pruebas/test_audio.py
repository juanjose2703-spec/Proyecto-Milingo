from servidor.extensiones import bd
from servidor.modelos import Curso, Leccion, OpcionRespuesta, Pregunta, Unidad
from servidor.pruebas.test_admin_contenido import BASE, _admin, _d, _leccion_vacia, _post
from servidor.servicios import ejercicios


def _crear(tipo, texto, opciones):
    curso = Curso(titulo="Prueba audio", publicado=True, orden=1)
    bd.session.add(curso)
    bd.session.flush()
    unidad = Unidad(curso_id=curso.id, titulo="U", orden=1, publicado=True)
    bd.session.add(unidad)
    bd.session.flush()
    leccion = Leccion(unidad_id=unidad.id, titulo="L", orden=1, publicada=True)
    bd.session.add(leccion)
    bd.session.flush()
    pregunta = Pregunta(leccion_id=leccion.id, tipo=tipo, texto=texto, orden=1, publicada=True)
    bd.session.add(pregunta)
    bd.session.flush()
    for orden, (t, correcta) in enumerate(opciones, 1):
        bd.session.add(OpcionRespuesta(
            pregunta_id=pregunta.id, texto=t, es_correcta=correcta, orden=orden,
        ))
    bd.session.commit()
    return bd.session.get(Pregunta, pregunta.id)


def test_presentar_escuchar_escribir(app):
    p = _crear("escuchar_escribir", "Good morning", [("Good morning", True)])
    d = ejercicios.presentar(1, p)
    assert d["texto"] == ""
    assert d["audio"] == {"texto": "Good morning", "idioma": "en-US"}
    assert "opciones" not in d and "fichas" not in d
    assert "es_correcta" not in str(d)


def test_evaluar_escuchar_escribir(app):
    p = _crear("escuchar_escribir", "Good morning", [("Good morning", True)])
    assert ejercicios.evaluar(p, {"texto": " good MORNING! "}, 1)[0] is True
    assert ejercicios.evaluar(p, {"texto": "good night"}, 1)[0] is False


def test_escuchar_elegir(app):
    p = _crear("escuchar_elegir", "Thank you",
               [("Gracias", True), ("Hola", False), ("Adiós", False)])
    d = ejercicios.presentar(1, p)
    assert d["audio"]["texto"] == "Thank you"
    assert len(d["opciones"]) == 3
    bien = next(o["id"] for o in d["opciones"] if o["texto"] == "Gracias")
    mal = next(o["id"] for o in d["opciones"] if o["texto"] == "Hola")
    assert ejercicios.evaluar(p, {"opcion": bien}, 1)[0] is True
    assert ejercicios.evaluar(p, {"opcion": mal}, 1)[0] is False


def test_admin_crea_preguntas_de_audio(acceder, cliente):
    t = _admin(acceder)
    url = f"{BASE}/lessons/{_leccion_vacia(cliente, t)}/questions"

    elegir = {
        "tipo": "escuchar_elegir", "texto": "Thank you",
        "opciones": [
            {"texto": "Gracias", "es_correcta": True},
            {"texto": "Hola", "es_correcta": False},
        ],
    }
    assert _post(cliente, t, url, elegir).status_code == 201

    dos_correctas = {**elegir, "opciones": [
        {"texto": "Gracias", "es_correcta": True},
        {"texto": "Hola", "es_correcta": True},
    ]}
    assert _post(cliente, t, url, dos_correctas).status_code == 400

    r = _post(cliente, t, url, {
        "tipo": "escuchar_escribir", "texto": "Good morning",
        "opciones": [{"texto": "Good morning"}],
    })
    assert r.status_code == 201
    assert all(o["es_correcta"] for o in _d(r)["pregunta"]["opciones"])