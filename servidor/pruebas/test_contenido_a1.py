from servidor.contenido.a1 import CURSO_A1
from servidor.servicios.normalizacion import normalizar

TIPOS_OPCION = {"seleccion", "completar_opcion"}
TIPOS_TEXTO = {"traducir_es_en", "traducir_en_es", "completar_texto"}
TIPOS = TIPOS_OPCION | TIPOS_TEXTO | {"ordenar_palabras"}

TITULOS = [
    "Hello!", "About Me", "Everyday Words", "My Routine",
    "Food and Drinks", "My World", "Time and Numbers", "Simple Conversations",
]


def _preguntas():
    for unidad in CURSO_A1["unidades"]:
        for leccion in unidad["lecciones"]:
            for n, pregunta in enumerate(leccion["preguntas"], 1):
                yield f'{unidad["titulo"]} / {leccion["titulo"]} / pregunta {n}', pregunta


def test_estructura_del_curso():
    unidades = CURSO_A1["unidades"]
    assert [u["titulo"] for u in unidades] == TITULOS
    for u in unidades:
        assert len(u["lecciones"]) == 2, u["titulo"]
        for l in u["lecciones"]:
            assert 5 <= len(l["preguntas"]) <= 8, f'{u["titulo"]} / {l["titulo"]}'


def test_cada_pregunta_esta_completa():
    for donde, p in _preguntas():
        assert p["tipo"] in TIPOS, donde
        for campo in ("instrucciones", "texto", "explicacion"):
            assert p[campo] and p[campo].strip(), f"{donde}: falta {campo}"
        assert p["opciones"], f"{donde}: sin opciones"


def test_opciones_bien_formadas():
    for donde, p in _preguntas():
        textos = [normalizar(t) for t, _ in p["opciones"]]
        assert all(textos), f"{donde}: opción vacía"
        assert len(set(textos)) == len(textos), f"{donde}: opciones repetidas"
        correctas = [c for _, c in p["opciones"] if c]
        if p["tipo"] in TIPOS_OPCION:
            assert len(p["opciones"]) >= 3, donde
            assert len(correctas) == 1, f"{donde}: debe haber exactamente 1 correcta"
        elif p["tipo"] in TIPOS_TEXTO:
            assert len(correctas) == len(p["opciones"]), f"{donde}: todas deben ser aceptadas"
        else:
            assert len(p["opciones"]) >= 3, f"{donde}: pocas fichas"
            assert len(correctas) == len(p["opciones"]), donde


def test_huecos_en_los_ejercicios_de_completar():
    for donde, p in _preguntas():
        if p["tipo"] in ("completar_opcion", "completar_texto"):
            assert "___" in p["texto"], f"{donde}: falta el hueco ___"