import pytest

from servidor.extensiones import bd
from servidor.modelos import IntentoLeccion, RespuestaIntento, Usuario
from servidor.servicios.carga_contenido import sincronizar_contenido

BASE = "/api/v1/admin"

PREGUNTA_OK = {
    "tipo": "seleccion",
    "instrucciones": "Selecciona la traducción correcta",
    "texto": "Tea",
    "explicacion": "«Tea» significa «té».",
    "opciones": [
        {"texto": "Té", "es_correcta": True},
        {"texto": "Café", "es_correcta": False},
        {"texto": "Agua", "es_correcta": False},
    ],
}


@pytest.fixture()
def contenido(app):
    sincronizar_contenido()
    bd.session.commit()


def _h(token):
    return {"X-CSRF-Token": token}


def _post(cliente, token, url, cuerpo=None):
    return cliente.post(url, json={} if cuerpo is None else cuerpo, headers=_h(token))


def _patch(cliente, token, url, cuerpo):
    return cliente.patch(url, json=cuerpo, headers=_h(token))


def _delete(cliente, token, url):
    return cliente.delete(url, headers=_h(token))


def _d(respuesta):
    return respuesta.get_json()["datos"]


def _admin(acceder):
    _, token = acceder("admin")
    return token


def _leccion_vacia(cliente, token):
    curso = _d(_post(cliente, token, f"{BASE}/courses", {"titulo": "Curso de prueba"}))["curso"]
    unidad = _d(_post(cliente, token, f"{BASE}/courses/{curso['id']}/units", {"titulo": "U"}))["unidad"]
    return _d(_post(cliente, token, f"{BASE}/units/{unidad['id']}/lessons", {"titulo": "L"}))["leccion"]["id"]


# ---------- Acceso ----------

def test_admin_rechaza_estudiante(acceder, cliente):
    _, token = acceder("alumna")
    assert cliente.get(f"{BASE}/content").status_code == 403
    assert _post(cliente, token, f"{BASE}/courses", {"titulo": "X"}).status_code == 403
    assert cliente.get(f"{BASE}/students").status_code == 403


def test_admin_sin_sesion(cliente):
    assert cliente.get(f"{BASE}/content").status_code == 401


def test_admin_exige_csrf(acceder, cliente):
    acceder("admin")
    r = cliente.post(f"{BASE}/courses", json={"titulo": "X"})
    assert r.status_code == 403


# ---------- Creación y validación ----------

def test_crear_jerarquia_y_arbol(acceder, cliente):
    t = _admin(acceder)
    r = _post(cliente, t, f"{BASE}/courses", {"titulo": "Inglés A2", "nivel": "A2"})
    assert r.status_code == 201
    curso = _d(r)["curso"]
    assert curso["publicado"] is False and curso["orden"] == 1 and curso["nivel"] == "A2"

    u1 = _d(_post(cliente, t, f"{BASE}/courses/{curso['id']}/units", {"titulo": "Unit 1"}))["unidad"]
    u2 = _d(_post(cliente, t, f"{BASE}/courses/{curso['id']}/units", {"titulo": "Unit 2"}))["unidad"]
    assert (u1["orden"], u2["orden"]) == (1, 2)

    r = _post(cliente, t, f"{BASE}/units/{u1['id']}/lessons", {"titulo": "L1", "xp_base": 12})
    assert r.status_code == 201
    leccion = _d(r)["leccion"]
    assert leccion["publicada"] is False and leccion["xp_base"] == 12

    r = _post(cliente, t, f"{BASE}/lessons/{leccion['id']}/questions", PREGUNTA_OK)
    assert r.status_code == 201
    assert _d(r)["pregunta"]["orden"] == 1

    arbol = _d(cliente.get(f"{BASE}/content"))["cursos"]
    assert len(arbol) == 1
    assert [u["titulo"] for u in arbol[0]["unidades"]] == ["Unit 1", "Unit 2"]
    assert arbol[0]["unidades"][0]["lecciones"][0]["num_preguntas"] == 1


def test_titulo_de_curso_duplicado(acceder, cliente):
    t = _admin(acceder)
    assert _post(cliente, t, f"{BASE}/courses", {"titulo": "Repetido"}).status_code == 201
    r = _post(cliente, t, f"{BASE}/courses", {"titulo": "Repetido"})
    assert r.status_code == 409
    assert r.get_json()["error"]["codigo"] == "duplicado"


def test_validaciones_de_pregunta(acceder, cliente):
    t = _admin(acceder)
    lid = _leccion_vacia(cliente, t)
    url = f"{BASE}/lessons/{lid}/questions"
    si, no = {"es_correcta": True}, {"es_correcta": False}
    malos = [
        {**PREGUNTA_OK, "tipo": "inventado"},
        {**PREGUNTA_OK, "texto": "  "},
        {**PREGUNTA_OK, "opciones": [{"texto": "Té", **no}, {"texto": "Café", **no}]},
        {**PREGUNTA_OK, "opciones": [{"texto": "Té", **si}, {"texto": "Café", **si}]},
        {**PREGUNTA_OK, "opciones": [{"texto": "Té", **si}]},
        {**PREGUNTA_OK, "opciones": [{"texto": "Té", **si}, {"texto": "té", **no}]},
        {**PREGUNTA_OK, "tipo": "completar_texto", "texto": "Sin hueco",
         "opciones": [{"texto": "x", **si}]},
        {**PREGUNTA_OK, "opciones": "no es una lista"},
    ]
    for malo in malos:
        assert _post(cliente, t, url, malo).status_code == 400, malo

    r = _post(cliente, t, url, {
        "tipo": "traducir_es_en", "texto": "Té",
        "opciones": [{"texto": "Tea"}, {"texto": "A tea"}],
    })
    assert r.status_code == 201
    assert all(o["es_correcta"] for o in _d(r)["pregunta"]["opciones"])


# ---------- Publicación ----------

def test_leccion_vacia_no_se_publica(acceder, cliente):
    t = _admin(acceder)
    lid = _leccion_vacia(cliente, t)
    r = _patch(cliente, t, f"{BASE}/lessons/{lid}", {"publicada": True})
    assert r.status_code == 409
    assert r.get_json()["error"]["codigo"] == "sin_preguntas"

    _post(cliente, t, f"{BASE}/lessons/{lid}/questions", PREGUNTA_OK)
    r = _patch(cliente, t, f"{BASE}/lessons/{lid}", {"publicada": True})
    assert r.status_code == 200
    assert _d(r)["leccion"]["publicada"] is True


def test_no_se_vacia_una_leccion_publicada(acceder, cliente):
    t = _admin(acceder)
    lid = _leccion_vacia(cliente, t)
    qid = _d(_post(cliente, t, f"{BASE}/lessons/{lid}/questions", PREGUNTA_OK))["pregunta"]["id"]
    assert _patch(cliente, t, f"{BASE}/lessons/{lid}", {"publicada": True}).status_code == 200

    assert _patch(cliente, t, f"{BASE}/questions/{qid}", {"publicada": False}).status_code == 409
    assert _delete(cliente, t, f"{BASE}/questions/{qid}").status_code == 409

    assert _patch(cliente, t, f"{BASE}/lessons/{lid}", {"publicada": False}).status_code == 200
    assert _patch(cliente, t, f"{BASE}/questions/{qid}", {"publicada": False}).status_code == 200


def test_contenido_publicado_aparece_al_estudiante(acceder, cliente):
    t = _admin(acceder)
    curso = _d(_post(cliente, t, f"{BASE}/courses",
                     {"titulo": "Inglés A2", "publicado": True}))["curso"]
    _post(cliente, t, f"{BASE}/courses", {"titulo": "Borrador"})  # sin publicar
    unidad = _d(_post(cliente, t, f"{BASE}/courses/{curso['id']}/units",
                      {"titulo": "Unit 1", "publicado": True}))["unidad"]
    lid = _d(_post(cliente, t, f"{BASE}/units/{unidad['id']}/lessons", {"titulo": "L1"}))["leccion"]["id"]
    _post(cliente, t, f"{BASE}/lessons/{lid}/questions", PREGUNTA_OK)
    assert _patch(cliente, t, f"{BASE}/lessons/{lid}", {"publicada": True}).status_code == 200

    acceder("alumna")
    cursos = _d(cliente.get("/api/v1/courses"))["cursos"]
    assert [c["titulo"] for c in cursos] == ["Inglés A2"]
    unidades = _d(cliente.get(f"/api/v1/courses/{curso['id']}/units"))["unidades"]
    assert [l["estado"] for l in unidades[0]["lecciones"]] == ["disponible"]


# ---------- Edición, orden y borrado ----------

def test_editar_pregunta_reemplaza_las_opciones(acceder, cliente):
    t = _admin(acceder)
    lid = _leccion_vacia(cliente, t)
    qid = _d(_post(cliente, t, f"{BASE}/lessons/{lid}/questions", PREGUNTA_OK))["pregunta"]["id"]

    r = _patch(cliente, t, f"{BASE}/questions/{qid}", {
        "texto": "Coffee",
        "opciones": [{"texto": "Té", "es_correcta": False}, {"texto": "Café", "es_correcta": True}],
    })
    assert r.status_code == 200
    p = _d(r)["pregunta"]
    assert p["texto"] == "Coffee"
    assert [(o["texto"], o["es_correcta"]) for o in p["opciones"]] == [("Té", False), ("Café", True)]

    listado = _d(cliente.get(f"{BASE}/lessons/{lid}/questions"))["preguntas"]
    assert len(listado) == 1 and len(listado[0]["opciones"]) == 2


def test_mover_unidades(acceder, cliente, contenido):
    t = _admin(acceder)
    unidades = _d(cliente.get(f"{BASE}/content"))["cursos"][0]["unidades"]
    segunda = unidades[1]["id"]
    r = _post(cliente, t, f"{BASE}/units/{segunda}/move", {"direccion": "arriba"})
    assert r.status_code == 200 and _d(r)["movido"] is True

    nuevas = _d(cliente.get(f"{BASE}/content"))["cursos"][0]["unidades"]
    assert [u["titulo"] for u in nuevas[:2]] == ["About Me", "Hello!"]

    r = _post(cliente, t, f"{BASE}/units/{segunda}/move", {"direccion": "arriba"})
    assert _d(r)["movido"] is False  # ya es la primera
    assert _post(cliente, t, f"{BASE}/units/{segunda}/move", {"direccion": "lado"}).status_code == 400


def test_no_se_borra_contenido_con_actividad(acceder, cliente, contenido):
    t = _admin(acceder)
    unidades = _d(cliente.get(f"{BASE}/content"))["cursos"][0]["unidades"]
    leccion = unidades[0]["lecciones"][0]
    pregunta_id = _d(cliente.get(f"{BASE}/lessons/{leccion['id']}/questions"))["preguntas"][0]["id"]

    alumna = bd.session.execute(
        bd.select(Usuario).where(Usuario.nombre_usuario == "alumna")
    ).scalar_one()
    intento = IntentoLeccion(usuario_id=alumna.id, leccion_id=leccion["id"], estado="abandonado",
                             aciertos=0, errores=1, xp_ganado=0)
    bd.session.add(intento)
    bd.session.flush()
    bd.session.add(RespuestaIntento(intento_id=intento.id, pregunta_id=pregunta_id,
                                    respuesta_usuario="x", es_correcta=False))
    bd.session.commit()

    assert _delete(cliente, t, f"{BASE}/questions/{pregunta_id}").status_code == 409
    assert _delete(cliente, t, f"{BASE}/lessons/{leccion['id']}").status_code == 409
    assert _delete(cliente, t, f"{BASE}/units/{unidades[0]['id']}").status_code == 409

    assert _delete(cliente, t, f"{BASE}/units/{unidades[-1]['id']}").status_code == 200
    nuevas = _d(cliente.get(f"{BASE}/content"))["cursos"][0]["unidades"]
    assert len(nuevas) == 7