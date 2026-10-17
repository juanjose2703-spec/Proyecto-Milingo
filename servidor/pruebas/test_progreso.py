from datetime import timedelta

import pytest

from servidor.extensiones import bd
from servidor.modelos import (
    ActividadDiaria, Curso, EstadisticaUsuario, Leccion, Logro, LogroUsuario,
    OpcionRespuesta, Pregunta, ProgresoLeccionUsuario, Unidad, Usuario,
)
from servidor.servicios.carga_contenido import sincronizar_contenido
from servidor.servicios.fechas import hoy_local


@pytest.fixture()
def contenido(app):
    sincronizar_contenido()
    bd.session.commit()


def _alumna_id():
    return bd.session.execute(
        bd.select(Usuario.id).where(Usuario.nombre_usuario == "alumna")
    ).scalar_one()


def _estadistica():
    return bd.session.execute(
        bd.select(EstadisticaUsuario).where(EstadisticaUsuario.usuario_id == _alumna_id())
    ).scalar_one()


def _estados_de_la_unidad(cliente):
    cid = cliente.get("/api/v1/courses").get_json()["datos"]["cursos"][0]["id"]
    r = cliente.get(f"/api/v1/courses/{cid}/units")
    unidad = r.get_json()["datos"]["unidades"][0]
    return [l["estado"] for l in unidad["lecciones"]]


def _contar():
    modelos = {
        "cursos": Curso, "unidades": Unidad, "lecciones": Leccion,
        "preguntas": Pregunta, "opciones": OpcionRespuesta, "logros": Logro,
    }
    return {
        nombre: bd.session.execute(bd.select(bd.func.count()).select_from(m)).scalar_one()
        for nombre, m in modelos.items()
    }


# ---------- Acceso ----------

def test_stats_sin_sesion(cliente):
    assert cliente.get("/api/v1/stats").status_code == 401


def test_contenido_sin_sesion(cliente):
    assert cliente.get("/api/v1/courses").status_code == 401
    assert cliente.get("/api/v1/progress").status_code == 401


def test_stats_admin_prohibido(acceder, cliente):
    acceder("admin")
    assert cliente.get("/api/v1/stats").status_code == 403


# ---------- Estadísticas ----------

def test_stats_iniciales(acceder, cliente):
    acceder("alumna")
    datos = cliente.get("/api/v1/stats").get_json()["datos"]
    assert datos["xp_total"] == 0
    assert datos["nivel"] == 1
    assert datos["corazones"] == 5
    assert datos["racha_actual"] == 0
    assert datos["practico_hoy"] is False


def test_corazones_se_restauran_al_cambiar_el_dia(acceder, cliente):
    est = _estadistica()
    est.corazones = 2
    est.fecha_corazones = hoy_local() - timedelta(days=1)
    bd.session.commit()
    acceder("alumna")
    assert cliente.get("/api/v1/stats").get_json()["datos"]["corazones"] == 5


def test_corazones_no_se_restauran_el_mismo_dia(acceder, cliente):
    est = _estadistica()
    est.corazones = 2
    est.fecha_corazones = hoy_local()
    bd.session.commit()
    acceder("alumna")
    assert cliente.get("/api/v1/stats").get_json()["datos"]["corazones"] == 2


@pytest.mark.parametrize("dias,esperado", [(0, 4), (1, 4), (2, 0), (5, 0)])
def test_racha_visible(acceder, cliente, dias, esperado):
    est = _estadistica()
    est.racha_actual = 4
    est.mejor_racha = 4
    est.ultima_fecha_actividad = hoy_local() - timedelta(days=dias)
    bd.session.commit()
    acceder("alumna")
    datos = cliente.get("/api/v1/stats").get_json()["datos"]
    assert datos["racha_actual"] == esperado
    assert datos["mejor_racha"] == 4


# ---------- Carga de contenido ----------

def test_carga_contenido_es_idempotente(app):
    sincronizar_contenido()
    bd.session.commit()
    primero = _contar()
    sincronizar_contenido()
    bd.session.commit()
    assert _contar() == primero
    assert primero["unidades"] == 8
    assert primero["lecciones"] == 16
    assert primero["preguntas"] == 96
    assert primero["logros"] == 5


# ---------- Mapa y desbloqueo ----------

def test_mapa_estados_iniciales(acceder, cliente, contenido):
    acceder("alumna")
    assert _estados_de_la_unidad(cliente) == ["disponible", "bloqueada"]


def test_desbloqueo_al_completar(acceder, cliente, contenido):
    lecciones = bd.session.execute(
        bd.select(Leccion).order_by(Leccion.orden)
    ).scalars().all()
    bd.session.add(ProgresoLeccionUsuario(
        usuario_id=_alumna_id(), leccion_id=lecciones[0].id,
        estado="completada", mejor_precision=100, veces_completada=1,
    ))
    bd.session.commit()
    acceder("alumna")
    assert _estados_de_la_unidad(cliente) == ["completada", "disponible"]


def test_progress_recomienda_la_primera(acceder, cliente, contenido):
    acceder("alumna")
    datos = cliente.get("/api/v1/progress").get_json()["datos"]
    assert datos["total_lecciones"] == 16
    assert datos["lecciones_completadas"] == 0
    assert datos["porcentaje"] == 0
    assert datos["siguiente"]["estado"] == "disponible"


def test_leccion_no_filtra_respuestas(acceder, cliente, contenido):
    leccion = bd.session.execute(bd.select(Leccion).order_by(Leccion.orden)).scalars().first()
    acceder("alumna")
    r = cliente.get(f"/api/v1/lessons/{leccion.id}")
    assert r.status_code == 200
    texto = r.get_data(as_text=True)
    assert "es_correcta" not in texto
    assert "opciones" not in texto
    assert r.get_json()["datos"]["leccion"]["num_preguntas"] == 6


def test_leccion_no_publicada_da_404(acceder, cliente, contenido):
    leccion = bd.session.execute(bd.select(Leccion).order_by(Leccion.orden)).scalars().first()
    leccion.publicada = False
    bd.session.commit()
    acceder("alumna")
    assert cliente.get(f"/api/v1/lessons/{leccion.id}").status_code == 404


# ---------- Logros y actividad ----------

def test_logros_listado(acceder, cliente, contenido):
    acceder("alumna")
    logros = cliente.get("/api/v1/achievements").get_json()["datos"]["logros"]
    assert len(logros) == 5
    assert not any(l["desbloqueado"] for l in logros)
    desbloqueados = cliente.get("/api/v1/achievements/unlocked").get_json()["datos"]["logros"]
    assert desbloqueados == []


def test_logros_desbloqueados(acceder, cliente, contenido):
    logro = bd.session.execute(bd.select(Logro).order_by(Logro.id)).scalars().first()
    bd.session.add(LogroUsuario(usuario_id=_alumna_id(), logro_id=logro.id))
    bd.session.commit()
    acceder("alumna")
    desbloqueados = cliente.get("/api/v1/achievements/unlocked").get_json()["datos"]["logros"]
    assert [l["codigo"] for l in desbloqueados] == [logro.codigo]
    todos = cliente.get("/api/v1/achievements").get_json()["datos"]["logros"]
    assert sum(1 for l in todos if l["desbloqueado"]) == 1


def test_actividad_siete_dias(acceder, cliente):
    hoy = hoy_local()
    bd.session.add(ActividadDiaria(
        usuario_id=_alumna_id(), fecha=hoy, xp_ganado=10, lecciones_completadas=1,
    ))
    bd.session.commit()
    acceder("alumna")
    dias = cliente.get("/api/v1/activity").get_json()["datos"]["dias"]
    assert len(dias) == 7
    assert dias[-1]["fecha"] == hoy.isoformat()
    assert dias[-1]["activo"] is True
    assert dias[-1]["xp"] == 10
    assert dias[0]["activo"] is False