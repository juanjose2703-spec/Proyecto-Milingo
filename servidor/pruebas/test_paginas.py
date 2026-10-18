def test_pagina_logros_se_sirve(cliente):
    r = cliente.get("/logros")
    assert r.status_code == 200
    assert "text/html" in r.content_type



def test_pagina_admin_se_sirve(cliente):
    r = cliente.get("/admin")
    assert r.status_code == 200
    assert "text/html" in r.content_type