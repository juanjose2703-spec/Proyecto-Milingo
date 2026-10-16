from flask import jsonify, request
from werkzeug.exceptions import HTTPException


class ErrorAPI(Exception):
    """Error controlado que se convierte en JSON uniforme."""

    def __init__(self, estado, codigo, mensaje):
        super().__init__(mensaje)
        self.estado = estado
        self.codigo = codigo
        self.mensaje = mensaje


def respuesta_error(estado, codigo, mensaje):
    return jsonify({"ok": False, "error": {"codigo": codigo, "mensaje": mensaje}}), estado


def registrar_errores(app):
    @app.errorhandler(ErrorAPI)
    def manejar_error_api(e):
        return respuesta_error(e.estado, e.codigo, e.mensaje)

    @app.errorhandler(HTTPException)
    def manejar_http(e):
        if not request.path.startswith("/api/"):
            return e
        mensajes = {
            400: "Petición inválida.",
            404: "Recurso no encontrado.",
            405: "Método no permitido.",
            429: "Demasiados intentos. Espera un momento e inténtalo de nuevo.",
        }
        return respuesta_error(
            e.code, f"http_{e.code}", mensajes.get(e.code, "Error en la petición.")
        )

    @app.errorhandler(Exception)
    def manejar_inesperado(e):
        app.logger.exception("Error no controlado")
        return respuesta_error(500, "error_interno", "Ocurrió un error inesperado.")