from servidor.extensiones import bd


class IntentoLeccion(bd.Model):
    """Una sesión de práctica de una lección. El servidor controla su estado."""

    __tablename__ = "intentos_leccion"
    __table_args__ = (
        bd.Index("ix_intento_usuario_leccion_estado", "usuario_id", "leccion_id", "estado"),
    )

    id = bd.Column(bd.Integer, primary_key=True)
    usuario_id = bd.Column(bd.Integer, bd.ForeignKey("usuarios.id"), nullable=False)
    leccion_id = bd.Column(bd.Integer, bd.ForeignKey("lecciones.id"), nullable=False)
    estado = bd.Column(bd.String(20), nullable=False, default="en_curso")
    aciertos = bd.Column(bd.Integer, nullable=False, default=0)
    errores = bd.Column(bd.Integer, nullable=False, default=0)
    xp_ganado = bd.Column(bd.Integer, nullable=False, default=0)
    iniciado_en = bd.Column(bd.DateTime, nullable=False, server_default=bd.func.now())
    finalizado_en = bd.Column(bd.DateTime)

    respuestas = bd.relationship(
        "RespuestaIntento", back_populates="intento", cascade="all, delete-orphan"
    )


class RespuestaIntento(bd.Model):
    """Una respuesta por pregunta y por intento (impide responder dos veces)."""

    __tablename__ = "respuestas_intento"
    __table_args__ = (
        bd.UniqueConstraint("intento_id", "pregunta_id", name="uq_respuesta_intento_pregunta"),
    )

    id = bd.Column(bd.Integer, primary_key=True)
    intento_id = bd.Column(bd.Integer, bd.ForeignKey("intentos_leccion.id"), nullable=False)
    pregunta_id = bd.Column(bd.Integer, bd.ForeignKey("preguntas.id"), nullable=False)
    respuesta_usuario = bd.Column(bd.Text, nullable=False)
    es_correcta = bd.Column(bd.Boolean, nullable=False)
    respondida_en = bd.Column(bd.DateTime, nullable=False, server_default=bd.func.now())

    intento = bd.relationship("IntentoLeccion", back_populates="respuestas")


class ProgresoLeccionUsuario(bd.Model):
    """Resumen por usuario y lección. Una sola fila por par."""

    __tablename__ = "progreso_leccion_usuario"
    __table_args__ = (
        bd.UniqueConstraint("usuario_id", "leccion_id", name="uq_progreso_usuario_leccion"),
    )

    id = bd.Column(bd.Integer, primary_key=True)
    usuario_id = bd.Column(bd.Integer, bd.ForeignKey("usuarios.id"), nullable=False)
    leccion_id = bd.Column(bd.Integer, bd.ForeignKey("lecciones.id"), nullable=False)
    estado = bd.Column(bd.String(20), nullable=False, default="en_progreso")
    mejor_precision = bd.Column(bd.Integer, nullable=False, default=0)
    veces_completada = bd.Column(bd.Integer, nullable=False, default=0)
    completada_en = bd.Column(bd.DateTime)