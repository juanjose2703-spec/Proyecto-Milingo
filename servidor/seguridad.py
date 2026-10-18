import hmac
import secrets
from functools import wraps

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from flask import request, session

from servidor.errores import ErrorAPI
from servidor.extensiones import bd
from servidor.modelos import Usuario

_hasher = PasswordHasher()
# Hash falso: se verifica cuando el usuario no existe, para que el tiempo de
# respuesta no delate si la cuenta existe.
_HASH_FALSO = _hasher.hash("contrasena-falsa-para-igualar-tiempos")


def hashear(contrasena):
    return _hasher.hash(contrasena)


def verificar(hash_guardado, contrasena):
    try:
        return _hasher.verify(hash_guardado, contrasena)
    except (VerificationError, InvalidHashError):
        return False


def verificar_falso(contrasena):
    verificar(_HASH_FALSO, contrasena)


def necesita_rehash(hash_guardado):
    return _hasher.check_needs_rehash(hash_guardado)


def token_csrf():
    """Devuelve el token CSRF de la sesión, creándolo si no existe."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def verificar_csrf():
    """Se ejecuta antes de cada petición que modifica datos."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.path.startswith("/api/"):
        esperado = session.get("csrf_token")
        recibido = request.headers.get("X-CSRF-Token", "")
        if not esperado or not hmac.compare_digest(esperado, recibido):
            raise ErrorAPI(403, "csrf_invalido", "Token de seguridad inválido. Recarga la página.")


_SIN_CACHE = object()


def usuario_actual():
    """Usuario de la sesión, leído de la base (nunca del navegador).

    Se guarda en el objeto request, que es nuevo en cada petición, para no
    leer la base varias veces dentro de la misma.
    """
    usuario = getattr(request, "_usuario_actual", _SIN_CACHE)
    if usuario is _SIN_CACHE:
        uid = session.get("usuario_id")
        usuario = bd.session.get(Usuario, uid) if uid else None
        if usuario is not None and not usuario.activo:
            usuario = None
        request._usuario_actual = usuario
    return usuario


def login_requerido(funcion):
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        if usuario_actual() is None:
            raise ErrorAPI(401, "no_autenticado", "Debes iniciar sesión.")
        return funcion(*args, **kwargs)
    return envoltura


def rol_requerido(rol):
    def decorador(funcion):
        @wraps(funcion)
        @login_requerido
        def envoltura(*args, **kwargs):
            if usuario_actual().rol != rol:
                raise ErrorAPI(403, "prohibido", "No tienes permiso para esta acción.")
            return funcion(*args, **kwargs)
        return envoltura
    return decorador