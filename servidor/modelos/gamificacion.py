from servidor.extensiones import bd


class EstadisticaUsuario(bd.Model):
    """Contadores del estudiante. Solo el servidor los modifica."""

    __tablename__ = "estadisticas_usuario"

    id = bd.Column(bd.Integer, primary_key=True)
    usuario_id = bd.Column(
        bd.Integer, bd.ForeignKey("usuarios.id"), nullable=False, unique=True
    )
    xp_total = bd.Column(bd.Integer, nullable=False, default=0)
    corazones = bd.Column(bd.Integer, nullable=False, default=5)
    racha_actual = bd.Column(bd.Integer, nullable=False, default=0)
    mejor_racha = bd.Column(bd.Integer, nullable=False, default=0)
    ultima_fecha_actividad = bd.Column(bd.Date)
    fecha_corazones = bd.Column(bd.Date)  # día local de la última recarga
    actualizado_en = bd.Column(
        bd.DateTime, nullable=False, server_default=bd.func.now(), onupdate=bd.func.now()
    )


class ActividadDiaria(bd.Model):
    __tablename__ = "actividad_diaria"
    __table_args__ = (
        bd.UniqueConstraint("usuario_id", "fecha", name="uq_actividad_usuario_fecha"),
    )

    id = bd.Column(bd.Integer, primary_key=True)
    usuario_id = bd.Column(bd.Integer, bd.ForeignKey("usuarios.id"), nullable=False)
    fecha = bd.Column(bd.Date, nullable=False)
    xp_ganado = bd.Column(bd.Integer, nullable=False, default=0)
    lecciones_completadas = bd.Column(bd.Integer, nullable=False, default=0)


class Logro(bd.Model):
    __tablename__ = "logros"

    id = bd.Column(bd.Integer, primary_key=True)
    codigo = bd.Column(bd.String(50), nullable=False, unique=True)
    nombre = bd.Column(bd.String(80), nullable=False)
    descripcion = bd.Column(bd.String(255), nullable=False)
    icono = bd.Column(bd.String(40))


class LogroUsuario(bd.Model):
    __tablename__ = "logros_usuario"
    __table_args__ = (
        bd.UniqueConstraint("usuario_id", "logro_id", name="uq_logro_usuario"),
    )

    id = bd.Column(bd.Integer, primary_key=True)
    usuario_id = bd.Column(bd.Integer, bd.ForeignKey("usuarios.id"), nullable=False)
    logro_id = bd.Column(bd.Integer, bd.ForeignKey("logros.id"), nullable=False)
    desbloqueado_en = bd.Column(bd.DateTime, nullable=False, server_default=bd.func.now())

    logro = bd.relationship("Logro")