from servidor.extensiones import bd


class Curso(bd.Model):
    __tablename__ = "cursos"

    id = bd.Column(bd.Integer, primary_key=True)
    titulo = bd.Column(bd.String(120), nullable=False, unique=True)
    descripcion = bd.Column(bd.Text)
    nivel = bd.Column(bd.String(10), nullable=False, default="A1")
    orden = bd.Column(bd.Integer, nullable=False, default=1)
    publicado = bd.Column(bd.Boolean, nullable=False, default=False)
    creado_en = bd.Column(bd.DateTime, nullable=False, server_default=bd.func.now())
    actualizado_en = bd.Column(
        bd.DateTime, nullable=False, server_default=bd.func.now(), onupdate=bd.func.now()
    )

    unidades = bd.relationship(
        "Unidad", back_populates="curso", order_by="Unidad.orden",
        cascade="all, delete-orphan",
    )


class Unidad(bd.Model):
    __tablename__ = "unidades"
    __table_args__ = (bd.UniqueConstraint("curso_id", "orden", name="uq_unidad_orden"),)

    id = bd.Column(bd.Integer, primary_key=True)
    curso_id = bd.Column(bd.Integer, bd.ForeignKey("cursos.id"), nullable=False)
    titulo = bd.Column(bd.String(120), nullable=False)
    descripcion = bd.Column(bd.String(255))
    orden = bd.Column(bd.Integer, nullable=False)
    publicado = bd.Column(bd.Boolean, nullable=False, default=False)
    creado_en = bd.Column(bd.DateTime, nullable=False, server_default=bd.func.now())
    actualizado_en = bd.Column(
        bd.DateTime, nullable=False, server_default=bd.func.now(), onupdate=bd.func.now()
    )

    curso = bd.relationship("Curso", back_populates="unidades")
    lecciones = bd.relationship(
        "Leccion", back_populates="unidad", order_by="Leccion.orden",
        cascade="all, delete-orphan",
    )


class Leccion(bd.Model):
    __tablename__ = "lecciones"
    __table_args__ = (bd.UniqueConstraint("unidad_id", "orden", name="uq_leccion_orden"),)

    id = bd.Column(bd.Integer, primary_key=True)
    unidad_id = bd.Column(bd.Integer, bd.ForeignKey("unidades.id"), nullable=False)
    titulo = bd.Column(bd.String(120), nullable=False)
    descripcion = bd.Column(bd.String(255))
    orden = bd.Column(bd.Integer, nullable=False)
    xp_base = bd.Column(bd.Integer, nullable=False, default=10)
    publicada = bd.Column(bd.Boolean, nullable=False, default=False)
    creado_en = bd.Column(bd.DateTime, nullable=False, server_default=bd.func.now())
    actualizado_en = bd.Column(
        bd.DateTime, nullable=False, server_default=bd.func.now(), onupdate=bd.func.now()
    )

    unidad = bd.relationship("Unidad", back_populates="lecciones")
    preguntas = bd.relationship(
        "Pregunta", back_populates="leccion", order_by="Pregunta.orden",
        cascade="all, delete-orphan",
    )


class Pregunta(bd.Model):
    """Un ejercicio. El campo `tipo` decide cómo se muestra y se valida:

    seleccion         -> opciones; una con es_correcta=True.
    completar_opcion  -> opciones; una con es_correcta=True.
    traducir_es_en    -> opciones = respuestas aceptadas (todas es_correcta=True).
    traducir_en_es    -> opciones = respuestas aceptadas (todas es_correcta=True).
    completar_texto   -> opciones = respuestas aceptadas (todas es_correcta=True).
    ordenar_palabras  -> opciones = fichas; `orden` es su posición correcta.
    Para añadir un tipo nuevo basta con un validador y un renderizador nuevos.
    """

    __tablename__ = "preguntas"
    __table_args__ = (bd.UniqueConstraint("leccion_id", "orden", name="uq_pregunta_orden"),)

    id = bd.Column(bd.Integer, primary_key=True)
    leccion_id = bd.Column(bd.Integer, bd.ForeignKey("lecciones.id"), nullable=False)
    tipo = bd.Column(bd.String(30), nullable=False)
    instrucciones = bd.Column(bd.String(255))
    texto = bd.Column(bd.Text, nullable=False)
    explicacion = bd.Column(bd.Text)
    orden = bd.Column(bd.Integer, nullable=False)
    publicada = bd.Column(bd.Boolean, nullable=False, default=True)

    leccion = bd.relationship("Leccion", back_populates="preguntas")
    opciones = bd.relationship(
        "OpcionRespuesta", back_populates="pregunta", order_by="OpcionRespuesta.orden",
        cascade="all, delete-orphan",
    )


class OpcionRespuesta(bd.Model):
    __tablename__ = "opciones_respuesta"
    __table_args__ = (bd.UniqueConstraint("pregunta_id", "orden", name="uq_opcion_orden"),)

    id = bd.Column(bd.Integer, primary_key=True)
    pregunta_id = bd.Column(bd.Integer, bd.ForeignKey("preguntas.id"), nullable=False)
    texto = bd.Column(bd.String(255), nullable=False)
    es_correcta = bd.Column(bd.Boolean, nullable=False, default=False)
    orden = bd.Column(bd.Integer, nullable=False)

    pregunta = bd.relationship("Pregunta", back_populates="opciones")