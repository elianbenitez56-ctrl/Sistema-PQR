import pytest

from app.db import get_db_cursor
from app.repos.usuarios import crear_usuario, eliminar_usuario, obtener_usuario_por_id  # noqa: F401


@pytest.fixture
def vendedor(client):
    crear_usuario(nombre="Vendedor Test", usuario="vend_test", contrasena="Clave-Test-1", rol="VENDEDOR",
                  documento="99999999", linea_producto="INAPEL", empresa="INAPEL")
    with get_db_cursor() as c:
        c.execute("SELECT id FROM usuarios WHERE usuario = 'vend_test'")
        uid = c.fetchone()["id"]
    yield uid
    eliminar_usuario(uid)


def test_sin_sesion_recibe_401(client):
    assert client.get("/api/pqr/todos").status_code == 401
    assert client.get("/api/dashboard").status_code == 401


def test_vendedor_no_accede_a_administracion(client, vendedor):
    r = client.post("/api/login", json={"usuario": "vend_test", "contrasena": "Clave-Test-1"})
    assert r.status_code == 200
    assert client.get("/api/dashboard").status_code == 403
    assert client.get("/api/usuarios").status_code == 403
    assert client.post("/api/cambiar_estado", json={"radicado": "x", "estado": "y"}).status_code == 403


def test_vendedor_no_ve_pqr_ajenos(client, vendedor, pqr):
    client.post("/api/login", json={"usuario": "vend_test", "contrasena": "Clave-Test-1"})
    assert client.get("/api/pqr/todos").status_code == 403
    r = client.get(f"/api/consultar/{pqr}")
    assert r.status_code in (403, 404)
