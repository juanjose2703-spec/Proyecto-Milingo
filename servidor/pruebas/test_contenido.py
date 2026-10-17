import pytest

from servidor.extensiones import bd
from servidor.modelos import Curso, Unidad
from servidor.servicios.carga_contenido import sincronizar_contenido


@pytest.fixture()
def contenido(app):
    sincronizar_contenido()
    bd.session.commit()


def _curso_id():
    return bd.session.execute(bd.select(Curso.id)).scalar_one()


def test_unidades_sin_sesion(cliente, contenido):
    assert cliente.get(f"/api/v1/courses/{_curso_id()}/units").status_code == 401


def test_unidades_con_lecciones_y_estados(acceder, cliente, contenido):
    cid = _curso_id()
    acceder("alumna")
    r = cliente.get(f"/api/v1/courses/{cid}/units")
    assert r.status_code == 200
    unidades = r.get_json()["datos"]["unidades"]
    assert len(unidades) == 1
    assert unidades[0]["titulo"] == "Hello!"
    assert [l["orden"] for l in unidades[0]["lecciones"]] == [1, 2]
    assert [l["estado"] for l in unidades[0]["lecciones"]] == ["disponible", "bloqueada"]
    assert "es_correcta" not in r.get_data(as_text=True)


def test_unidad_no_publicada_se_oculta(acceder, cliente, contenido):
    cid = _curso_id()
    unidad = bd.session.execute(bd.select(Unidad)).scalars().first()
    unidad_id = unidad.id
    unidad.publicado = False
    bd.session.commit()
    acceder("alumna")
    unidades = cliente.get(f"/api/v1/courses/{cid}/units").get_json()["datos"]["unidades"]
    assert unidades == []
    assert cliente.get(f"/api/v1/units/{unidad_id}/lessons").status_code == 404


def test_curso_inexistente_da_404(acceder, cliente):
    acceder("alumna")
    assert cliente.get("/api/v1/courses/999999/units").status_code == 404


def test_lecciones_de_una_unidad(acceder, cliente, contenido):
    unidad_id = bd.session.execute(bd.select(Unidad.id)).scalars().first()
    acceder("alumna")
    r = cliente.get(f"/api/v1/units/{unidad_id}/lessons")
    assert r.status_code == 200
    assert [l["estado"] for l in r.get_json()["datos"]["lecciones"]] == ["disponible", "bloqueada"]


def test_pagina_recorrido_se_sirve(cliente):
    r = cliente.get("/recorrido")
    assert r.status_code == 200
    assert "text/html" in r.content_type