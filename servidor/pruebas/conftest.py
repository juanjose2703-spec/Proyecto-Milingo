import pytest

from servidor.aplicacion import crear_app
from servidor.configuracion import ConfiguracionPruebas
from servidor.extensiones import bd
from servidor.modelos import Usuario, EstadisticaUsuario
from servidor.seguridad import hashear

CLAVE = "ClaveDePrueba123"


@pytest.fixture()
def app():
    app = crear_app(ConfiguracionPruebas)
    with app.app_context():
        # Seguridad: nunca borrar tablas de una base que no sea de pruebas.
        assert bd.engine.url.database.endswith("_pruebas"), "Base de pruebas incorrecta"
        bd.drop_all()
        bd.create_all()

        admin = Usuario(nombre_usuario="admin", correo="admin@ejemplo.test",
                        nombre_mostrar="Admin", hash_contrasena=hashear(CLAVE), rol="admin")
        alumna = Usuario(nombre_usuario="alumna", correo="alumna@ejemplo.test",
                         nombre_mostrar="Alumna", hash_contrasena=hashear(CLAVE),
                         rol="estudiante")
        bd.session.add_all([admin, alumna])
        bd.session.flush()
        bd.session.add(EstadisticaUsuario(usuario_id=alumna.id, corazones=5))
        bd.session.commit()
        yield app
        bd.session.remove()
        bd.drop_all()


@pytest.fixture()
def cliente(app):
    return app.test_client()


@pytest.fixture()
def acceder(cliente):
    """Inicia sesión y devuelve (respuesta, token_csrf_nuevo)."""
    def _acceder(usuario, contrasena=CLAVE):
        token = cliente.get("/api/v1/auth/csrf").get_json()["datos"]["csrf_token"]
        r = cliente.post("/api/v1/auth/login",
                         json={"usuario": usuario, "contrasena": contrasena},
                         headers={"X-CSRF-Token": token})
        nuevo = r.get_json()["datos"]["csrf_token"] if r.status_code == 200 else None
        return r, nuevo
    return _acceder