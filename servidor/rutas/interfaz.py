from pathlib import Path

from flask import Blueprint, send_from_directory

# .../milingo/interfaz
RAIZ_INTERFAZ = Path(__file__).resolve().parents[2] / "interfaz"

interfaz_bp = Blueprint("interfaz", __name__)


def _pagina(nombre):
    return send_from_directory(RAIZ_INTERFAZ / "paginas", nombre)


@interfaz_bp.get("/")
def inicio():
    return _pagina("inicio.html")


@interfaz_bp.get("/acceso")
def acceso():
    return _pagina("acceso.html")


@interfaz_bp.get("/panel")
def panel():
    return _pagina("panel.html")


@interfaz_bp.get("/admin")
def admin():
    # Provisional hasta construir el panel de administración.
    return _pagina("admin.html")


# send_from_directory impide salirse de la carpeta (../).
@interfaz_bp.get("/estilos/<path:nombre>")
def estilos(nombre):
    return send_from_directory(RAIZ_INTERFAZ / "estilos", nombre)


@interfaz_bp.get("/scripts/<path:nombre>")
def scripts(nombre):
    return send_from_directory(RAIZ_INTERFAZ / "scripts", nombre)


@interfaz_bp.get("/recursos/<path:nombre>")
def recursos(nombre):
    return send_from_directory(RAIZ_INTERFAZ / "recursos", nombre)


@interfaz_bp.get("/recorrido")
def recorrido():
    return _pagina("recorrido.html")


@interfaz_bp.get("/leccion/<int:leccion_id>")
def leccion(leccion_id):
    return _pagina("leccion.html")