import pytest

from servidor.extensiones import bd
from servidor.modelos import IntentoLeccion, Leccion, Pregunta, Usuario
from servidor.pruebas.conftest import CLAVE
from servidor.seguridad import hashear
from servidor.servicios.carga_contenido import sincronizar_contenido


@pytest.fixture()
def contenido(app):
    sincronizar_contenido()
    bd.session.commit()


@pytest.fixture()
def sesion(acceder):
    """Alumna con sesión iniciada. Devuelve su token CSRF."""
    _, token = acceder("alumna")
    return token


def _cab(token):
    return {"X-CSRF-Token": token}


def _id_leccion(n):
    lecciones = bd.session.execute(
        bd.select(Leccion).order_by(Leccion.unidad_id, Leccion.orden)
    ).scalars().all()
    return lecciones[n - 1].id


def _primera_pregunta_id(leccion_id):
    return bd.session.execute(
        bd.select(Pregunta.id).where(Pregunta.leccion_id == leccion_id)
        .order_by(Pregunta.orden)
    ).scalars().first()


def _iniciar(cliente, token, leccion_id):
    return cliente.post(f"/api/v1/lessons/{leccion_id}/attempts", json={}, headers=_cab(token))


def _responder(cliente, token, intento_id, pregunta_id, cuerpo):
    return cliente.post(
        f"/api/v1/attempts/{intento_id}/answers",
        json={"pregunta_id": pregunta_id, **cuerpo}, headers=_cab(token),
    )


def _completar(cliente, token, intento_id):
    return cliente.post(f"/api/v1/attempts/{intento_id}/complete", json={}, headers=_cab(token))


def _abandonar(cliente, token, intento_id):
    return cliente.post(f"/api/v1/attempts/{intento_id}/abandon", json={}, headers=_cab(token))


def _datos(r):
    return r.get_json()["datos"]


def _codigo_error(r):
    return r.get_json()["error"]["codigo"]


def _cuerpo(pregunta, bien):
    """Arma la respuesta a partir de la pregunta que mostró el servidor.

    Busca la respuesta correcta en la base (el navegador real no puede hacerlo).
    """
    p = bd.session.get(Pregunta, pregunta["id"])
    if p.tipo in ("seleccion", "completar_opcion"):
        texto = next(o.texto for o in p.opciones if o.es_correcta == bien)
        indice = next(o["id"] for o in pregunta["opciones"] if o["texto"] == texto)
        return {"opcion": indice}
    if p.tipo == "ordenar_palabras":
        libres = list(pregunta["fichas"])
        orden = []
        for o in p.opciones:
            ficha = next(f for f in libres if f["texto"] == o.texto)
            libres.remove(ficha)
            orden.append(ficha["id"])
        return {"orden": orden if bien else orden[::-1]}
    return {"texto": p.opciones[0].texto if bien else "respuesta equivocada"}


def _jugar_todo(cliente, token, intento_id, pregunta, bien=True):
    """Responde en orden hasta terminar. Devuelve la última respuesta del servidor."""
    ultima = None
    while pregunta is not None:
        r = _responder(cliente, token, intento_id, pregunta["id"], _cuerpo(pregunta, bien))
        assert r.status_code == 200, r.get_json()
        ultima = _datos(r)
        if ultima["terminado"]:
            break
        pregunta = ultima["siguiente_pregunta"]
    return ultima


# ---------- Acceso ----------

def test_iniciar_sin_sesion(cliente):
    token = cliente.get("/api/v1/auth/csrf").get_json()["datos"]["csrf_token"]
    assert _iniciar(cliente, token, 1).status_code == 401


def test_iniciar_admin_prohibido(acceder, cliente):
    _, token = acceder("admin")
    assert _iniciar(cliente, token, 1).status_code == 403


def test_respuesta_sin_csrf(sesion, cliente):
    r = cliente.post("/api/v1/attempts/1/answers", json={"pregunta_id": 1, "opcion": 0})
    assert r.status_code == 403


def test_intento_ajeno(contenido, sesion, cliente):
    otra = Usuario(nombre_usuario="otra", correo="otra@ejemplo.test", nombre_mostrar="Otra",
                   hash_contrasena=hashear(CLAVE), rol="estudiante")
    bd.session.add(otra)
    bd.session.flush()
    intento = IntentoLeccion(usuario_id=otra.id, leccion_id=_id_leccion(1),
                             estado="en_curso", aciertos=0, errores=0, xp_ganado=0)
    bd.session.add(intento)
    bd.session.commit()
    intento_id = intento.id
    pregunta_id = _primera_pregunta_id(_id_leccion(1))

    r = _responder(cliente, sesion, intento_id, pregunta_id, {"opcion": 0})
    assert r.status_code == 404
    assert _completar(cliente, sesion, intento_id).status_code == 404
    assert _abandonar(cliente, sesion, intento_id).status_code == 404


# ---------- Inicio ----------

def test_iniciar_no_filtra_respuestas(contenido, sesion, cliente):
    r = _iniciar(cliente, sesion, _id_leccion(1))
    assert r.status_code == 201
    d = _datos(r)
    p = d["pregunta"]
    assert set(p) == {"id", "tipo", "instrucciones", "texto", "opciones"}
    assert len(p["opciones"]) == 4
    assert all(set(o) == {"id", "texto"} for o in p["opciones"])
    texto = r.get_data(as_text=True)
    assert "es_correcta" not in texto
    assert "explicacion" not in texto
    assert d["total"] == 6 and d["respondidas"] == 0 and d["reanudado"] is False


def test_leccion_bloqueada_no_inicia(contenido, sesion, cliente):
    r = _iniciar(cliente, sesion, _id_leccion(2))
    assert r.status_code == 403
    assert _codigo_error(r) == "leccion_bloqueada"


def test_reanudar_intento(contenido, sesion, cliente):
    d = _datos(_iniciar(cliente, sesion, _id_leccion(1)))
    p1 = d["pregunta"]
    r1 = _datos(_responder(cliente, sesion, d["intento_id"], p1["id"], _cuerpo(p1, True)))

    r = _iniciar(cliente, sesion, _id_leccion(1))
    assert r.status_code == 200
    d2 = _datos(r)
    assert d2["reanudado"] is True
    assert d2["intento_id"] == d["intento_id"]
    assert d2["respondidas"] == 1
    assert d2["pregunta"]["id"] == r1["siguiente_pregunta"]["id"]


def test_abandonar(contenido, sesion, cliente):
    d = _datos(_iniciar(cliente, sesion, _id_leccion(1)))
    r = _abandonar(cliente, sesion, d["intento_id"])
    assert r.status_code == 200
    assert _datos(r)["estado"] == "abandonado"
    assert _completar(cliente, sesion, d["intento_id"]).status_code == 409

    r2 = _iniciar(cliente, sesion, _id_leccion(1))
    assert r2.status_code == 201
    assert _datos(r2)["intento_id"] != d["intento_id"]


# ---------- Respuestas ----------

def test_acierto_y_error(contenido, sesion, cliente):
    d = _datos(_iniciar(cliente, sesion, _id_leccion(1)))
    p1 = d["pregunta"]
    r1 = _datos(_responder(cliente, sesion, d["intento_id"], p1["id"], _cuerpo(p1, True)))
    assert r1["correcta"] is True
    assert r1["respuesta_correcta"] == "Hola"
    assert r1["corazones"] == 5
    assert r1["respondidas"] == 1

    p2 = r1["siguiente_pregunta"]
    r2 = _datos(_responder(cliente, sesion, d["intento_id"], p2["id"], _cuerpo(p2, False)))
    assert r2["correcta"] is False
    assert r2["respuesta_correcta"] == "Adiós"
    assert r2["corazones"] == 4
    assert r2["explicacion"]


def test_pregunta_fuera_de_turno(contenido, sesion, cliente):
    d = _datos(_iniciar(cliente, sesion, _id_leccion(1)))
    ultima = bd.session.execute(
        bd.select(Pregunta.id).where(Pregunta.leccion_id == _id_leccion(1))
        .order_by(Pregunta.orden.desc())
    ).scalars().first()
    r = _responder(cliente, sesion, d["intento_id"], ultima, {"opcion": 0})
    assert r.status_code == 409
    assert _codigo_error(r) == "pregunta_incorrecta"

    de_otra_leccion = _primera_pregunta_id(_id_leccion(2))
    r = _responder(cliente, sesion, d["intento_id"], de_otra_leccion, {"opcion": 0})
    assert r.status_code == 409


def test_respuesta_repetida(contenido, sesion, cliente):
    d = _datos(_iniciar(cliente, sesion, _id_leccion(1)))
    p1 = d["pregunta"]
    cuerpo = _cuerpo(p1, False)
    r1 = _datos(_responder(cliente, sesion, d["intento_id"], p1["id"], cuerpo))
    assert r1["corazones"] == 4 and r1["repetida"] is False

    r2 = _responder(cliente, sesion, d["intento_id"], p1["id"], cuerpo)
    assert r2.status_code == 200
    assert _datos(r2)["repetida"] is True
    assert _datos(r2)["corazones"] == 4
    assert _datos(r2)["errores"] == 1


# ---------- Cierre, XP y progreso ----------

def test_completar_antes_de_responder(contenido, sesion, cliente):
    d = _datos(_iniciar(cliente, sesion, _id_leccion(1)))
    r = _completar(cliente, sesion, d["intento_id"])
    assert r.status_code == 409
    assert _codigo_error(r) == "intento_incompleto"


def test_completar_da_xp_una_vez(contenido, sesion, cliente):
    d = _datos(_iniciar(cliente, sesion, _id_leccion(1)))
    ultima = _jugar_todo(cliente, sesion, d["intento_id"], d["pregunta"])
    assert ultima["listo_para_completar"] is True

    r = _completar(cliente, sesion, d["intento_id"])
    assert r.status_code == 200
    res = _datos(r)
    assert res["aciertos"] == 6 and res["errores"] == 0 and res["precision"] == 100
    assert res["xp_ganado"] == 22  # 10 base + 2 por cada uno de los 6 aciertos
    assert {"primera_leccion", "precision_alta"} <= {l["codigo"] for l in res["logros_nuevos"]}

    r2 = _completar(cliente, sesion, d["intento_id"])
    assert r2.status_code == 200
    assert _datos(r2)["repetido"] is True
    assert _datos(r2)["logros_nuevos"] == []

    stats = cliente.get("/api/v1/stats").get_json()["datos"]
    assert stats["xp_total"] == 22
    assert stats["racha_actual"] == 1
    assert stats["practico_hoy"] is True


def test_desbloquea_siguiente(contenido, sesion, cliente):
    d = _datos(_iniciar(cliente, sesion, _id_leccion(1)))
    _jugar_todo(cliente, sesion, d["intento_id"], d["pregunta"])
    _completar(cliente, sesion, d["intento_id"])

    cid = cliente.get("/api/v1/courses").get_json()["datos"]["cursos"][0]["id"]
    unidad = cliente.get(f"/api/v1/courses/{cid}/units").get_json()["datos"]["unidades"][0]
    assert [l["estado"] for l in unidad["lecciones"]] == ["completada", "disponible"]
    assert _iniciar(cliente, sesion, _id_leccion(2)).status_code == 201


def test_repeticion_da_la_mitad(contenido, sesion, cliente):
    for _ in range(2):
        d = _datos(_iniciar(cliente, sesion, _id_leccion(1)))
        _jugar_todo(cliente, sesion, d["intento_id"], d["pregunta"])
        res = _datos(_completar(cliente, sesion, d["intento_id"]))

    assert res["repeticion"] is True
    assert res["xp_ganado"] == 11
    assert res["logros_nuevos"] == []
    stats = cliente.get("/api/v1/stats").get_json()["datos"]
    assert stats["xp_total"] == 33
    assert stats["racha_actual"] == 1  # no sube dos veces el mismo día
    desbloqueados = cliente.get("/api/v1/achievements/unlocked").get_json()["datos"]["logros"]
    assert len(desbloqueados) == 2  # primera_leccion y precision_alta, sin duplicados


def test_sin_corazones(contenido, sesion, cliente):
    d = _datos(_iniciar(cliente, sesion, _id_leccion(1)))
    ultima = _jugar_todo(cliente, sesion, d["intento_id"], d["pregunta"], bien=False)
    assert ultima["terminado"] == "sin_corazones"
    assert ultima["corazones"] == 0
    assert ultima["siguiente_pregunta"] is None

    r = _completar(cliente, sesion, d["intento_id"])
    assert r.status_code == 409
    assert _codigo_error(r) == "intento_cerrado"

    r = _iniciar(cliente, sesion, _id_leccion(1))
    assert r.status_code == 409
    assert _codigo_error(r) == "sin_corazones"

    stats = cliente.get("/api/v1/stats").get_json()["datos"]
    assert stats["xp_total"] == 0 and stats["corazones"] == 0