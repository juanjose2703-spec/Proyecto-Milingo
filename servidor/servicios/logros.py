from servidor.extensiones import bd
from servidor.modelos import Logro, LogroUsuario, ProgresoLeccionUsuario
from servidor.servicios.reglas import LECCION_COMPLETADA, PRECISION_LOGRO_ALTA


def a_dict(logro):
    return {
        "codigo": logro.codigo, "nombre": logro.nombre,
        "descripcion": logro.descripcion, "icono": logro.icono,
    }


def conceder_nuevos(usuario_id, est, precision):
    """Concede los logros cumplidos que aún no tiene. Devuelve los nuevos.

    No hace commit. La restricción única (usuario, logro) impide duplicados.
    """
    bd.session.flush()
    completadas = bd.session.execute(
        bd.select(bd.func.count()).select_from(ProgresoLeccionUsuario).where(
            ProgresoLeccionUsuario.usuario_id == usuario_id,
            ProgresoLeccionUsuario.estado == LECCION_COMPLETADA,
        )
    ).scalar_one()

    cumplidos = set()
    if completadas >= 1:
        cumplidos.add("primera_leccion")
    if completadas >= 5:
        cumplidos.add("cinco_lecciones")
    if est.racha_actual >= 3:
        cumplidos.add("racha_3")
    if est.xp_total >= 100:
        cumplidos.add("xp_100")
    if precision >= PRECISION_LOGRO_ALTA:
        cumplidos.add("precision_alta")

    ya = set(bd.session.execute(
        bd.select(Logro.codigo)
        .join(LogroUsuario, LogroUsuario.logro_id == Logro.id)
        .where(LogroUsuario.usuario_id == usuario_id)
    ).scalars())
    pendientes = cumplidos - ya
    if not pendientes:
        return []

    nuevos = bd.session.execute(
        bd.select(Logro).where(Logro.codigo.in_(pendientes)).order_by(Logro.id)
    ).scalars().all()
    for logro in nuevos:
        bd.session.add(LogroUsuario(usuario_id=usuario_id, logro_id=logro.id))
    bd.session.flush()
    return nuevos