from servidor.pruebas.conftest import CLAVE


def test_login_correcto(acceder):
    r, token = acceder("alumna")
    assert r.status_code == 200
    datos = r.get_json()["datos"]
    assert datos["usuario"]["rol"] == "estudiante"
    assert "hash_contrasena" not in datos["usuario"]
    assert token


def test_login_por_correo(acceder):
    r, _ = acceder("alumna@ejemplo.test")
    assert r.status_code == 200


def test_contrasena_incorrecta(acceder, cliente):
    r, _ = acceder("alumna", "incorrecta-123")
    assert r.status_code == 401
    assert cliente.get("/api/v1/auth/me").status_code == 401


def test_usuario_inexistente_mismo_mensaje(acceder):
    r1, _ = acceder("alumna", "incorrecta-123")
    r2, _ = acceder("nadie", "incorrecta-123")
    assert r1.status_code == r2.status_code == 401
    assert r1.get_json()["error"]["mensaje"] == r2.get_json()["error"]["mensaje"]


def test_login_sin_csrf_es_rechazado(cliente):
    r = cliente.post("/api/v1/auth/login", json={"usuario": "alumna", "contrasena": CLAVE})
    assert r.status_code == 403


def test_me_sin_sesion(cliente):
    assert cliente.get("/api/v1/auth/me").status_code == 401


def test_me_con_sesion(acceder, cliente):
    acceder("alumna")
    r = cliente.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.get_json()["datos"]["usuario"]["nombre_usuario"] == "alumna"


def test_logout(acceder, cliente):
    _, token = acceder("alumna")
    r = cliente.post("/api/v1/auth/logout", headers={"X-CSRF-Token": token})
    assert r.status_code == 200
    assert cliente.get("/api/v1/auth/me").status_code == 401


def test_logout_sin_csrf_es_rechazado(acceder, cliente):
    acceder("alumna")
    assert cliente.post("/api/v1/auth/logout").status_code == 403


def test_estudiante_no_accede_a_admin(acceder, cliente):
    acceder("alumna")
    assert cliente.get("/api/v1/admin/ping").status_code == 403


def test_admin_accede_a_admin(acceder, cliente):
    acceder("admin")
    assert cliente.get("/api/v1/admin/ping").status_code == 200


def test_admin_sin_sesion(cliente):
    assert cliente.get("/api/v1/admin/ping").status_code == 401


def test_cambiar_contrasena(acceder, cliente):
    _, token = acceder("alumna")
    r = cliente.post("/api/v1/auth/change-password", headers={"X-CSRF-Token": token},
                     json={"contrasena_actual": CLAVE, "contrasena_nueva": "OtraClave12345"})
    assert r.status_code == 200
    cliente.post("/api/v1/auth/logout", headers={"X-CSRF-Token": token})
    r2, _ = acceder("alumna", "OtraClave12345")
    assert r2.status_code == 200


def test_cambiar_contrasena_debil(acceder, cliente):
    _, token = acceder("alumna")
    r = cliente.post("/api/v1/auth/change-password", headers={"X-CSRF-Token": token},
                     json={"contrasena_actual": CLAVE, "contrasena_nueva": "corta"})
    assert r.status_code == 400