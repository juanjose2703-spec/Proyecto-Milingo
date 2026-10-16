from servidor.extensiones import bd


class Usuario(bd.Model):
    """Persona que puede iniciar sesión. Nunca se guarda la contraseña en claro."""

    __tablename__ = "usuarios"

    id = bd.Column(bd.Integer, primary_key=True)
    nombre_usuario = bd.Column(bd.String(50), nullable=False, unique=True)
    correo = bd.Column(bd.String(120), nullable=False, unique=True)
    nombre_mostrar = bd.Column(bd.String(80), nullable=False)
    hash_contrasena = bd.Column(bd.String(255), nullable=False)
    rol = bd.Column(bd.String(20), nullable=False, default="estudiante")
    activo = bd.Column(bd.Boolean, nullable=False, default=True)
    creado_en = bd.Column(bd.DateTime, nullable=False, server_default=bd.func.now())

    def a_dict(self):
        """Datos públicos. Nunca incluye el hash."""
        return {
            "id": self.id,
            "nombre_usuario": self.nombre_usuario,
            "correo": self.correo,
            "nombre_mostrar": self.nombre_mostrar,
            "rol": self.rol,
        }