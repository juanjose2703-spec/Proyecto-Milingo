from flask import Blueprint, jsonify, request, session
from sqlalchemy import or_

from servidor.errores import ErrorAPI
from servidor.extensiones import bd, limitador
from servidor.modelos import Usuario
from servidor.seguridad import (
    hashear, verificar, verificar_falso, necesita_rehash,
    token_csrf, usuario_actual, login_requerido,
)

autenticacion_bp = Blueprint("autenticacion", __name__, url_prefix="/api/v1/auth")

LARGO_MINIMO_CONTRASENA = 10


def _json():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ErrorAPI(400, "json_invalido", "El cuerpo debe ser JSON.")
    return datos


@autenticacion_bp.get("/csrf")
def obtener_csrf():
    """Entrega un token CSRF (también a visitantes, para poder iniciar sesión)."""
    return jsonify({"ok": True, "datos": {"csrf_token": token_csrf()}})


@autenticacion_bp.post("/login")
@limitador.limit("10 per minute")
def login():
    datos = _json()
    identificador = str(datos.get("usuario", "")).strip()
    contrasena = str(datos.get("contrasena", ""))

    if not identificador or not contrasena or len(identificador) > 120 or len(contrasena) > 256:
        raise ErrorAPI(400, "datos_invalidos", "Escribe tu usuario y tu contraseña.")

    usuario = bd.session.execute(
        bd.select(Usuario).where(
            or_(Usuario.nombre_usuario == identificador, Usuario.correo == identificador)
        )
    ).scalar_one_or_none()

    if usuario is None:
        verificar_falso(contrasena)
        valido = False
    else:
        valido = usuario.activo and verificar(usuario.hash_contrasena, contrasena)

    if not valido:
        raise ErrorAPI(401, "credenciales_invalidas", "Usuario o contraseña incorrectos.")

    if necesita_rehash(usuario.hash_contrasena):
        usuario.hash_contrasena = hashear(contrasena)
        bd.session.commit()

    session.clear()  # evita fijación de sesión
    session["usuario_id"] = usuario.id
    session.permanent = True
    return jsonify({
        "ok": True,
        "datos": {"usuario": usuario.a_dict(), "csrf_token": token_csrf()},
    })


@autenticacion_bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True, "datos": {}})


@autenticacion_bp.get("/me")
@login_requerido
def yo():
    return jsonify({
        "ok": True,
        "datos": {"usuario": usuario_actual().a_dict(), "csrf_token": token_csrf()},
    })


@autenticacion_bp.post("/change-password")
@login_requerido
def cambiar_contrasena():
    datos = _json()
    actual = str(datos.get("contrasena_actual", ""))
    nueva = str(datos.get("contrasena_nueva", ""))
    usuario = usuario_actual()

    if not verificar(usuario.hash_contrasena, actual):
        raise ErrorAPI(400, "contrasena_actual_incorrecta", "La contraseña actual no es correcta.")
    if len(nueva) < LARGO_MINIMO_CONTRASENA or len(nueva) > 256:
        raise ErrorAPI(
            400, "contrasena_debil",
            f"La nueva contraseña debe tener al menos {LARGO_MINIMO_CONTRASENA} caracteres.",
        )
    if nueva == actual:
        raise ErrorAPI(400, "contrasena_igual", "La nueva contraseña debe ser distinta.")

    usuario.hash_contrasena = hashear(nueva)
    bd.session.commit()
    return jsonify({"ok": True, "datos": {}})