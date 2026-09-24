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


@pytest.mark.parametrize("rol", [
    "LIDER_CALIDAD", "LIDER_COMERCIAL", "COORDINADORA COMERCIAL", "DIRECTORA COMERCIAL", "COMERCIAL", "DIRECTOR DE PRODUCCION",
])
def test_admin_puede_crear_usuarios_de_todos_los_roles(admin, rol):
    r = admin.post("/api/usuarios", json={"nombre": "Rol Prueba", "usuario": "rol_prueba", "contrasena": "Clave-Rol-1", "rol": rol})
    assert r.status_code == 201, r.get_json()
    assert admin.delete(f"/api/usuarios/{r.get_json()['id']}").status_code == 200


def test_listado_de_usuarios_no_expone_hashes(admin):
    usuarios = admin.get("/api/usuarios").get_json()["usuarios"]
    assert usuarios and all("contrasena_hash" not in u for u in usuarios)


def test_validaciones_de_usuario(admin):
    base = {"nombre": "V", "usuario": "valida_prueba", "contrasena": "Clave-Val-1", "rol": "VENDEDOR", "linea_producto": "INAPEL"}
    assert admin.post("/api/usuarios", json={**base, "documento": "abc"}).status_code == 400
    assert admin.post("/api/usuarios", json={**base, "telefono": "12"}).status_code == 400
    assert admin.post("/api/usuarios", json={**base, "correo": "no-es-correo"}).status_code == 400
    assert admin.post("/api/usuarios", json={**base, "rol": "INVENTADO"}).status_code == 400
    assert admin.post("/api/usuarios", json={**base, "linea_producto": "OTRA"}).status_code == 400
    assert admin.post("/api/usuarios", json={**base, "usuario": "admin"}).status_code == 400
    assert admin.post("/api/usuarios", json={"usuario": "x"}).status_code == 400


def test_no_se_puede_eliminar_al_admin_principal_ni_a_si_mismo(admin):
    uid = next(u["id"] for u in admin.get("/api/usuarios").get_json()["usuarios"] if u["usuario"] == "admin")
    assert admin.delete(f"/api/usuarios/{uid}").status_code == 400


def test_lider_calidad_no_puede_crear_admin(admin):
    r = admin.post("/api/usuarios", json={
        "nombre": "Calidad Prueba", "usuario": "calidad_prueba", "contrasena": "Clave-Cal-1", "rol": "LIDER_CALIDAD",
    })
    assert r.status_code == 201, r.get_json()
    uid_calidad = r.get_json()["id"]
    try:
        calidad = admin.application.test_client()
        assert calidad.post("/api/login", json={"usuario": "calidad_prueba", "contrasena": "Clave-Cal-1"}).status_code == 200

        r = calidad.post("/api/usuarios", json={
            "nombre": "Hacker", "usuario": "hacker_prueba", "contrasena": "Clave-Hac-1", "rol": "ADMIN",
        })
        assert r.status_code == 403, r.get_json()

        r = calidad.post("/api/usuarios", json={
            "nombre": "Vendedor OK", "usuario": "vendedor_ok_prueba", "contrasena": "Clave-Ok1-1", "rol": "VENDEDOR",
            "linea_producto": "INAPEL",
        })
        assert r.status_code == 201, r.get_json()
        admin.delete(f"/api/usuarios/{r.get_json()['id']}")
    finally:
        admin.delete(f"/api/usuarios/{uid_calidad}")
