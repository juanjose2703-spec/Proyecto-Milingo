import pytest

from servidor.extensiones import bd
from servidor.pruebas.test_intentos import _completar, _datos, _iniciar, _jugar_todo
from servidor.servicios.carga_contenido import sincronizar_contenido


@pytest.fixture()
def contenido(app):
    sincronizar_contenido()
    bd.session.commit()


def test_recorrido_a1_completo(acceder, cliente, contenido):
    _, token = acceder("alumna")
    completadas = 0
    while True:
        siguiente = _datos(cliente.get("/api/v1/progress"))["siguiente"]
        if siguiente is None:
            break
        assert completadas < 16, "el recorrido no termina"
        r = _iniciar(cliente, token, siguiente["id"])
        assert r.status_code == 201
        d = _datos(r)
        _jugar_todo(cliente, token, d["intento_id"], d["pregunta"])
        res = _datos(_completar(cliente, token, d["intento_id"]))
        assert res["precision"] == 100
        completadas += 1

    assert completadas == 16
    progreso = _datos(cliente.get("/api/v1/progress"))
    assert progreso["lecciones_completadas"] == 16 and progreso["porcentaje"] == 100

    stats = _datos(cliente.get("/api/v1/stats"))
    assert stats["xp_total"] == 16 * 22
    assert stats["nivel"] == 4
    assert stats["racha_actual"] == 1  # todo el mismo día: la racha sube una sola vez

    codigos = {l["codigo"] for l in _datos(cliente.get("/api/v1/achievements/unlocked"))["logros"]}
    assert codigos == {"primera_leccion", "cinco_lecciones", "xp_100", "precision_alta"}