import os

import pytest

from wsgi import app as flask_app


@pytest.fixture(autouse=True)
def sin_correos(monkeypatch):
    """Los tests nunca envían correo real."""
    for modulo, nombre in (
        ("app.rutas.pqr", "enviar_confirmacion_pqr"),
        ("app.rutas.seguimiento", "enviar_notificacion_comercial"),
    ):
        monkeypatch.setattr(f"{modulo}.{nombre}", lambda *a, **k: {"ok": True, "estado": "simulado"}, raising=False)


@pytest.fixture
def client():
    return flask_app.test_client()


@pytest.fixture
def admin(client):
    r = client.post("/api/login", json={"usuario": "admin", "contrasena": os.environ["ADMIN_PASS"]})
    assert r.status_code == 200
    return client


@pytest.fixture
def pqr(admin):
    """PQR de prueba; se elimina al terminar."""
    r = admin.post("/api/pqr", json={
        "cliente": "TEST-CLIENTE", "nit": "1", "tipoSol": "Queja", "desc": "descripcion de prueba",
        "email": "", "productos": [],
    })
    assert r.status_code == 200, r.get_json()
    radicado = r.get_json()["radicado"]
    yield radicado
    admin.delete(f"/api/pqr/{radicado}")
