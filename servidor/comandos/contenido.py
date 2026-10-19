import click
from flask.cli import with_appcontext

from servidor.extensiones import bd
from servidor.modelos import Curso, Unidad, Leccion, Pregunta, OpcionRespuesta, Logro
from servidor.servicios.carga_contenido import sincronizar_todo


@click.command("cargar-contenido")
@with_appcontext
def cargar_contenido():
    """Carga o actualiza el contenido A1 y A2 y los logros. Se puede repetir sin duplicar."""
    try:
        sincronizar_todo()
        bd.session.commit()
    except Exception:
        bd.session.rollback()
        raise

    for nombre, modelo in (
        ("Cursos", Curso), ("Unidades", Unidad), ("Lecciones", Leccion),
        ("Preguntas", Pregunta), ("Opciones", OpcionRespuesta), ("Logros", Logro),
    ):
        total = bd.session.execute(bd.select(bd.func.count()).select_from(modelo)).scalar_one()
        click.echo(f"{nombre}: {total}")