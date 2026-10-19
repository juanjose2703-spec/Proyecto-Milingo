import pytest

from servidor.contenido.a2 import CURSO_A2
from servidor.extensiones import bd
from servidor.modelos import (
    Curso, Leccion, Logro, OpcionRespuesta, Pregunta, ProgresoLeccionUsuario,
    Unidad, Usuario,
)
from servidor.pruebas.test_intentos import _completar, _datos, _iniciar, _jugar_todo
from servidor.servicios import desbloqueo
from servidor.servicios.carga_contenido import sincronizar_todo
from servidor.servicios.normalizacion import normalizar

TIPOS_OPCION = {"seleccion", "completar_opcion", "escuchar_elegir"}
TIPOS_TEXTO = {"traducir_es_en", "traducir_en_es", "completar_texto", "escuchar_escribir"}
TIPOS = TIPOS_OPCION | TIPOS_TEXTO | {"ordenar_palabras"}
TIPOS_AUDIO = {"escuchar_elegir", "escuchar_escribir"}


@pytest.fixture()
def todo(app):
    sincronizar_todo()
    bd.session.commit()


def _preguntas():
    for unidad in CURSO_A2["unidades"]:
        for leccion in unidad["lecciones"]:
            for n, pregunta in enumerate(leccion["preguntas"], 1):
                yield f'{unidad["titulo"]} / {leccion["titulo"]} / pregunta {n}', pregunta


def _contar():
    modelos = {
        "cursos": Curso, "unidades": Unidad, "lecciones": Leccion,
        "preguntas": Pregunta, "opciones": OpcionRespuesta, "logros": Logro,
    }
    return {
        nombre: bd.session.execute(bd.select(bd.func.count()).select_from(m)).scalar_one()
        for nombre, m in modelos.items()
    }


# ---------- Calidad del contenido (no usan la base) ----------

def test_estructura_de_a2():
    assert CURSO_A2["nivel"] == "A2" and CURSO_A2["orden"] == 2
    assert len(CURSO_A2["unidades"]) == 6
    for u in CURSO_A2["unidades"]:
        assert len(u["lecciones"]) == 2, u["titulo"]
        for l in u["lecciones"]:
            assert len(l["preguntas"]) == 8, f'{u["titulo"]} / {l["titulo"]}'


def test_cada_leccion_tiene_audio_y_variedad():
    for u in CURSO_A2["unidades"]:
        for l in u["lecciones"]:
            tipos = [p["tipo"] for p in l["preguntas"]]
            donde = f'{u["titulo"]} / {l["titulo"]}'
            assert sum(1 for t in tipos if t in TIPOS_AUDIO) >= 3, donde
            assert len(set(tipos)) >= 5, donde


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


def test_huecos_y_audio_coherentes():
    for donde, p in _preguntas():
        if p["tipo"] in ("completar_opcion", "completar_texto"):
            assert "___" in p["texto"], f"{donde}: falta el hueco ___"
        if p["tipo"] in TIPOS_AUDIO:
            assert "___" not in p["texto"], f"{donde}: la frase que suena no lleva hueco"
        if p["tipo"] == "escuchar_escribir":
            aceptadas = [normalizar(t) for t, _ in p["opciones"]]
            assert normalizar(p["texto"]) in aceptadas, \
                f"{donde}: la frase que suena debe estar entre las respuestas aceptadas"


# ---------- Con la base ----------

def test_carga_a1_y_a2_es_idempotente(app):
    sincronizar_todo()
    bd.session.commit()
    primero = _contar()
    sincronizar_todo()
    bd.session.commit()
    assert _contar() == primero
    assert primero["cursos"] == 2
    assert primero["unidades"] == 14
    assert primero["lecciones"] == 28
    assert primero["preguntas"] == 192
    assert primero["logros"] == 5


def test_a2_se_ve_pero_esta_bloqueado(acceder, cliente, todo):
    acceder("alumna")
    cursos = _datos(cliente.get("/api/v1/courses"))["cursos"]
    assert [c["titulo"] for c in cursos] == ["Inglés A1", "Inglés A2"]

    unidades = _datos(cliente.get(f"/api/v1/courses/{cursos[1]['id']}/units"))["unidades"]
    assert len(unidades) == 6
    assert all(l["estado"] == "bloqueada" for u in unidades for l in u["lecciones"])

    siguiente = _datos(cliente.get("/api/v1/progress"))["siguiente"]
    assert siguiente["curso_id"] == cursos[0]["id"]  # primero toca A1


def test_recorrido_a2_completo(acceder, cliente, todo):
    alumna = bd.session.execute(
        bd.select(Usuario).where(Usuario.nombre_usuario == "alumna")
    ).scalar_one()
    lecciones = desbloqueo.lecciones_ordenadas()
    assert len(lecciones) == 28
    for l in lecciones[:16]:  # A1 ya terminado
        bd.session.add(ProgresoLeccionUsuario(
            usuario_id=alumna.id, leccion_id=l.id, estado="completada",
            mejor_precision=100, veces_completada=1,
        ))
    bd.session.commit()

    _, token = acceder("alumna")
    cursos = _datos(cliente.get("/api/v1/courses"))["cursos"]
    primera = _datos(cliente.get("/api/v1/progress"))["siguiente"]
    assert primera["curso_id"] == cursos[1]["id"]  # ahora toca A2

    completadas = 0
    while True:
        siguiente = _datos(cliente.get("/api/v1/progress"))["siguiente"]
        if siguiente is None:
            break
        assert completadas < 12, "el recorrido no termina"
        r = _iniciar(cliente, token, siguiente["id"])
        assert r.status_code == 201
        d = _datos(r)
        _jugar_todo(cliente, token, d["intento_id"], d["pregunta"])
        res = _datos(_completar(cliente, token, d["intento_id"]))
        assert res["precision"] == 100
        completadas += 1

    assert completadas == 12
    stats = _datos(cliente.get("/api/v1/stats"))
    assert stats["xp_total"] == 12 * 26  # 10 base + 2 por cada uno de los 8 aciertos
    assert _datos(cliente.get("/api/v1/progress"))["porcentaje"] == 100