from servidor.extensiones import bd
from servidor.modelos import EstadisticaUsuario
from servidor.servicios.fechas import hoy_local
from servidor.servicios.reglas import (
    CORAZONES_INICIALES, CORAZONES_MAXIMOS, XP_POR_NIVEL,
)


def obtener(usuario_id):
    """Devuelve las estadísticas del estudiante.

    Si faltan, las crea. Si cambió el día local, restaura los corazones.
    """
    est = bd.session.execute(
        bd.select(EstadisticaUsuario).where(EstadisticaUsuario.usuario_id == usuario_id)
    ).scalar_one_or_none()

    cambio = False
    if est is None:
        est = EstadisticaUsuario(usuario_id=usuario_id, corazones=CORAZONES_INICIALES)
        bd.session.add(est)
        cambio = True

    hoy = hoy_local()
    if est.fecha_corazones != hoy:
        est.corazones = CORAZONES_MAXIMOS
        est.fecha_corazones = hoy
        cambio = True

    if cambio:
        bd.session.commit()
    return est


def racha_visible(est):
    """La racha se muestra solo si hubo actividad hoy o ayer; si no, vale 0."""
    ultima = est.ultima_fecha_actividad
    if ultima is None:
        return 0
    if (hoy_local() - ultima).days <= 1:
        return est.racha_actual
    return 0


def a_dict(est):
    return {
        "xp_total": est.xp_total,
        "nivel": est.xp_total // XP_POR_NIVEL + 1,
        "xp_en_nivel": est.xp_total % XP_POR_NIVEL,
        "xp_por_nivel": XP_POR_NIVEL,
        "corazones": est.corazones,
        "corazones_maximos": CORAZONES_MAXIMOS,
        "racha_actual": racha_visible(est),
        "mejor_racha": est.mejor_racha,
        "practico_hoy": est.ultima_fecha_actividad == hoy_local(),
    }