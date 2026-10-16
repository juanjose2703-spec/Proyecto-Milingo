from flask import Flask

from servidor.configuracion import Configuracion
from servidor.errores import registrar_errores
from servidor.extensiones import bd, migrar, limitador
from servidor.seguridad import verificar_csrf

POLITICA_CONTENIDO = (
    "default-src 'self'; "
    "img-src 'self' data:; "
    "style-src 'self'; "
    "script-src 'self'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)


def crear_app(configuracion=Configuracion):
    """Fábrica de la aplicación: crea y configura Flask."""
    app = Flask(__name__)
    app.config.from_object(configuracion)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Falta SECRET_KEY en el archivo .env")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("Falta la URL de la base de datos en el archivo .env")

    bd.init_app(app)
    migrar.init_app(app, bd, directory="migraciones")
    limitador.init_app(app)

    import servidor.modelos  # noqa: F401  (registra las tablas para las migraciones)

    registrar_errores(app)
    app.before_request(verificar_csrf)

    @app.after_request
    def cabeceras_seguridad(respuesta):
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["X-Frame-Options"] = "DENY"
        respuesta.headers["Referrer-Policy"] = "same-origin"
        respuesta.headers["Content-Security-Policy"] = POLITICA_CONTENIDO
        return respuesta

    from servidor.rutas.salud import salud_bp
    from servidor.rutas.autenticacion import autenticacion_bp
    from servidor.rutas.admin import admin_bp
    from servidor.rutas.interfaz import interfaz_bp
    app.register_blueprint(salud_bp)
    app.register_blueprint(autenticacion_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(interfaz_bp)

    from servidor.comandos.usuarios import crear_usuario
    app.cli.add_command(crear_usuario)

    return app