def test_pagina_logros_se_sirve(cliente):
    r = cliente.get("/logros")
    assert r.status_code == 200
    assert "text/html" in r.content_type