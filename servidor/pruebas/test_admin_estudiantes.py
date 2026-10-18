import pytest

from servidor.extensiones import bd
from servidor.modelos import ActividadDiaria, Logro, LogroUsuario
from servidor.pruebas.test_admin_contenido import _admin, _d, _patch, _post
from servidor.servicios.carga_contenido import sincronizar_contenido
from servidor.servicios.fechas import hoy_local

BASE = "/api/v1/admin/students"


@pytest.fixture()
def contenido(app):
    sincronizar_contenido()
    bd.session.commit()


def _alumna_id(cliente):
    alumnos = _d(cliente.get(BASE))["estudiantes"]
    return next(a["id"] for a in alumnos if a["nombre_usuario"] == "alumna")


def _detalle(cliente, sid):
    return _d(cliente.get(f"{BASE}/{sid}"))


def _estados(cliente, sid):
    return [l["estado"] for l in _detalle(cliente, sid)["lecciones"]]


def test_estudiantes_prohibido_para_estudiante(acceder, cliente):
    acceder("alumna")
    assert cliente.get(BASE).status_code == 403
    assert cliente.get(f"{BASE}/1").status_code == 403


def test_listado_de_estudiantes(acceder, cliente):
    _admin(acceder)
    r = cliente.get(BASE)
    alumnos = _d(r)["estudiantes"]
    assert len(alumnos) == 1  # el administrador no aparece
    a = alumnos[0]
    assert a["nombre_usuario"] == "alumna"
    assert (a["xp_total"], a["corazones"], a["lecciones_completadas"]) == (0, 5, 0)
    assert "hash" not in r.get_data(as_text=True)


def test_detalle_del_estudiante(acceder, cliente, contenido):
    _admin(acceder)
    d = _detalle(cliente, _alumna_id(cliente))
    assert d["estudiante"]["nombre_mostrar"] == "Alumna"
    assert len(d["lecciones"]) == 16
    assert [l["estado"] for l in d["lecciones"]][:2] == ["disponible", "bloqueada"]
    assert len(d["actividad"]) == 14 and len(d["logros"]) == 5
    assert d["intentos"] == []


def test_completar_hasta_una_leccion(acceder, cliente, contenido):
    t = _admin(acceder)
    sid = _alumna_id(cliente)
    tercera = _detalle(cliente, sid)["lecciones"][2]["id"]
    r = _post(cliente, t, f"{BASE}/{sid}/lessons/{tercera}/complete-until")
    assert r.status_code == 200 and _d(r)["lecciones_completadas"] == 3

    assert _estados(cliente, sid) == ["completada"] * 3 + ["disponible"] + ["bloqueada"] * 12
    assert _detalle(cliente, sid)["estadisticas"]["xp_total"] == 0  # no da XP


def test_reiniciar_una_leccion(acceder, cliente, contenido):
    t = _admin(acceder)
    sid = _alumna_id(cliente)
    tercera = _detalle(cliente, sid)["lecciones"][2]["id"]
    _post(cliente, t, f"{BASE}/{sid}/lessons/{tercera}/complete-until")

    assert _post(cliente, t, f"{BASE}/{sid}/lessons/{tercera}/reset").status_code == 200
    assert _estados(cliente, sid) == ["completada"] * 2 + ["disponible"] + ["bloqueada"] * 13


def test_fijar_estadisticas(acceder, cliente):
    t = _admin(acceder)
    sid = _alumna_id(cliente)
    r = _patch(cliente, t, f"{BASE}/{sid}/stats", {"xp_total": 150, "corazones": 2})
    assert r.status_code == 200
    e = _d(r)["estadisticas"]
    assert (e["xp_total"], e["nivel"], e["corazones"]) == (150, 2, 2)

    for malo in ({"corazones": 9}, {"xp_total": -1}, {"xp_total": True}, {}):
        assert _patch(cliente, t, f"{BASE}/{sid}/stats", malo).status_code == 400, malo

    cliente.post("/api/v1/auth/logout", headers={"X-CSRF-Token": t})
    r, _ = acceder("alumna")
    assert r.status_code == 200
    stats = _d(cliente.get("/api/v1/stats"))


def test_reiniciar_todo(acceder, cliente, contenido):
    t = _admin(acceder)
    sid = _alumna_id(cliente)
    _patch(cliente, t, f"{BASE}/{sid}/stats", {"xp_total": 50})
    segunda = _detalle(cliente, sid)["lecciones"][1]["id"]
    _post(cliente, t, f"{BASE}/{sid}/lessons/{segunda}/complete-until")

    logro_id = bd.session.execute(bd.select(Logro.id)).scalars().first()
    bd.session.add(LogroUsuario(usuario_id=sid, logro_id=logro_id))
    bd.session.add(ActividadDiaria(usuario_id=sid, fecha=hoy_local(),
                                   xp_ganado=10, lecciones_completadas=1))
    bd.session.commit()

    assert _post(cliente, t, f"{BASE}/{sid}/reset").status_code == 400
    assert _post(cliente, t, f"{BASE}/{sid}/reset", {"confirmar": False}).status_code == 400

    r = _post(cliente, t, f"{BASE}/{sid}/reset", {"confirmar": True})
    assert r.status_code == 200
    d = _detalle(cliente, sid)
    assert d["estadisticas"]["xp_total"] == 0 and d["estadisticas"]["corazones"] == 5
    assert [l["estado"] for l in d["lecciones"]][:2] == ["disponible", "bloqueada"]
    assert not any(l["desbloqueado"] for l in d["logros"])
    assert not any(a["activo"] for a in d["actividad"])


def test_estudiante_inexistente_o_administrador(acceder, cliente):
    _admin(acceder)
    admin_id = _d(cliente.get("/api/v1/auth/me"))["usuario"]["id"]
    assert cliente.get(f"{BASE}/{admin_id}").status_code == 404
    assert cliente.get(f"{BASE}/999999").status_code == 404