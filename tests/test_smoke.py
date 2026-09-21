"""Smoke tests: requieren MySQL accesible (ej. `docker compose run --rm web pytest`)."""
import io


def test_healthz(client):
    assert client.get("/healthz").get_json() == {"ok": True}


def test_login_invalido(client):
    r = client.post("/api/login", json={"usuario": "nadie", "contrasena": "mal"})
    assert r.status_code == 401


def test_login_bloquea_tras_fallos(client):
    for _ in range(5):
        client.post("/api/login", json={"usuario": "bloqueado", "contrasena": "mal"})
    r = client.post("/api/login", json={"usuario": "bloqueado", "contrasena": "mal"})
    assert r.status_code == 429


def test_evidencias_rechaza_radicado_con_traversal(admin):
    r = admin.post(
        "/api/evidencias",
        data={"radicado": "../../tmp/x", "archivos": (io.BytesIO(b"x"), "a.txt")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 400


def test_pagina_principal_y_todos_sus_assets_estaticos(client):
    import re

    r = client.get("/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assets = re.findall(r'(?:href|src)="(/static/(?:css|js)/[^"]+)"', html)
    assert len(assets) >= 15
    for url in assets:
        assert client.get(url).status_code == 200, url
