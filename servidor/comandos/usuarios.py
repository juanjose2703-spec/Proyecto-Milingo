import click
from flask.cli import with_appcontext

from servidor.extensiones import bd
from servidor.modelos import Usuario, EstadisticaUsuario
from servidor.seguridad import hashear
from servidor.servicios.reglas import ROLES, ROL_ESTUDIANTE, CORAZONES_INICIALES


@click.command("crear-usuario")
@click.option("--usuario", prompt="Nombre de usuario", help="Sin espacios, máx. 50.")
@click.option("--correo", prompt="Correo")
@click.option("--nombre", prompt="Nombre para mostrar")
@click.option("--rol", type=click.Choice(ROLES), prompt="Rol (admin/estudiante)")
@click.password_option("--contrasena", prompt="Contraseña", confirmation_prompt=True,
                       help="Se pide sin mostrarla en pantalla.")
@with_appcontext
def crear_usuario(usuario, correo, nombre, rol, contrasena):
    """Crea un usuario. No existe registro público: se hace solo por aquí."""
    usuario = usuario.strip()
    correo = correo.strip().lower()

    if not usuario or " " in usuario or len(usuario) > 50:
        raise click.ClickException("Usuario inválido (sin espacios, máximo 50).")
    if len(contrasena) < 10:
        raise click.ClickException("La contraseña debe tener al menos 10 caracteres.")

    existe = bd.session.execute(
        bd.select(Usuario).where(
            (Usuario.nombre_usuario == usuario) | (Usuario.correo == correo)
        )
    ).first()
    if existe:
        raise click.ClickException("Ya existe un usuario con ese nombre o correo.")

    nuevo = Usuario(
        nombre_usuario=usuario, correo=correo, nombre_mostrar=nombre.strip(),
        hash_contrasena=hashear(contrasena), rol=rol, activo=True,
    )
    bd.session.add(nuevo)
    bd.session.flush()

    if rol == ROL_ESTUDIANTE:
        bd.session.add(EstadisticaUsuario(
            usuario_id=nuevo.id, corazones=CORAZONES_INICIALES,
        ))
    bd.session.commit()
    click.echo(f"Usuario '{usuario}' creado con rol {rol}.")