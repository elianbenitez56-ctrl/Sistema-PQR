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


def test_admin_edita_y_elimina_usuario_de_forma_persistente(admin):
    r = admin.post("/api/usuarios", json={
        "nombre": "Edicion Prueba", "usuario": "edit_prueba", "contrasena": "Clave-Uno-1", "rol": "VENDEDOR",
        "documento": "77777777", "linea_producto": "INAPEL", "empresa": "INAPEL",
    })
    assert r.status_code == 201, r.get_json()
    uid = r.get_json()["id"]
    try:
        r = admin.put(f"/api/usuarios/{uid}", json={"nombre": "Nombre Nuevo", "telefono": "3001112233"})
        assert r.status_code == 200, r.get_json()
        r = admin.put(f"/api/usuarios/{uid}/credenciales", json={"usuario": "edit_prueba", "contrasena": "Clave-Dos-2"})
        assert r.status_code == 200, r.get_json()

        with get_db_cursor() as c:
            c.execute("SELECT nombre, telefono FROM usuarios WHERE id = %s", (uid,))
            assert c.fetchone() == {"nombre": "Nombre Nuevo", "telefono": "3001112233"}

        otro = admin.application.test_client()
        assert otro.post("/api/login", json={"usuario": "edit_prueba", "contrasena": "Clave-Uno-1"}).status_code == 401
        assert otro.post("/api/login", json={"usuario": "edit_prueba", "contrasena": "Clave-Dos-2"}).status_code == 200

        assert admin.put(f"/api/usuarios/{uid}", json={"activo": False}).status_code == 200
        assert admin.application.test_client().post(
            "/api/login", json={"usuario": "edit_prueba", "contrasena": "Clave-Dos-2"}).status_code == 401
    finally:
        assert admin.delete(f"/api/usuarios/{uid}").status_code == 200
    with get_db_cursor() as c:
        c.execute("SELECT id FROM usuarios WHERE id = %s", (uid,))
        assert c.fetchone() is None
