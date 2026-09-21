"""Smoke tests: requieren MySQL accesible (ej. `docker compose run --rm web pytest`)."""
import io
import os

import pytest

from wsgi import app


@pytest.fixture
def client():
    return app.test_client()


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


def test_evidencias_rechaza_radicado_con_traversal(client):
    login = client.post("/api/login", json={"usuario": "admin", "contrasena": os.environ["ADMIN_PASS"]})
    assert login.status_code == 200
    r = client.post(
        "/api/evidencias",
        data={"radicado": "../../tmp/x", "archivos": (io.BytesIO(b"x"), "a.txt")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 400
