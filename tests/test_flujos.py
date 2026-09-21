import io
import os

from app.config import Config
from app.repos.pqr import eliminar_pqr
from app.servicios import catalogo


def _producto():
    catalogo.cargar_catalogo()
    return catalogo._CACHE_PRODUCTOS[0]


def test_catalogo_busca_por_referencia(admin):
    p = _producto()
    r = admin.get("/api/catalogo/productos", query_string={"linea": p["linea"], "referencia_siesa": p["referencia_siesa"]})
    assert r.status_code == 200
    assert r.get_json()["productos"][0]["referencia_siesa"] == p["referencia_siesa"]
    assert admin.get("/api/catalogo/productos", query_string={"linea": "NOEXISTE", "referencia_siesa": "x"}).status_code == 400


def test_pqr_con_producto_del_catalogo_y_rechazo_de_producto_inventado(admin):
    p = _producto()
    base = {"cliente": "TEST-CATALOGO", "nit": "1", "tipoSol": "Queja", "desc": "x", "email": ""}
    r = admin.post("/api/pqr", json={**base, "productos": [p]})
    assert r.status_code == 200, r.get_json()
    radicado = r.get_json()["radicado"]
    try:
        assert admin.get(f"/api/consultar/{radicado}").get_json()["productos"][0]["referencia_siesa"] == p["referencia_siesa"]
    finally:
        eliminar_pqr(radicado)
    falso = {**p, "referencia_siesa": "REF-INEXISTENTE"}
    assert admin.post("/api/pqr", json={**base, "productos": [falso]}).status_code == 400


def test_evidencias_subida_valida_rechazo_y_borrado_de_carpeta(admin, pqr):
    r = admin.post("/api/evidencias", data={"radicado": pqr, "tipo": "Foto", "archivos": (io.BytesIO(b"\x89PNG"), "foto.png")},
                   content_type="multipart/form-data")
    assert r.status_code == 200, r.get_json()
    carpeta = os.path.join(Config.UPLOAD_FOLDER, pqr)
    assert os.path.exists(os.path.join(carpeta, "foto.png"))

    malo = admin.post("/api/evidencias", data={"radicado": pqr, "archivos": (io.BytesIO(b"x"), "virus.exe")},
                      content_type="multipart/form-data")
    assert malo.status_code == 400

    assert admin.delete(f"/api/pqr/{pqr}").status_code == 200
    assert not os.path.exists(carpeta)


def test_cierre_comercial_deja_el_pqr_cerrado(admin, pqr):
    calidad = {"radicado": pqr, "resp": "Ana", "cargo": "Calidad", "causa": "X", "herramientas": ["5 ¿Por qué?"], "deptos": "P"}
    assert admin.post("/api/seguimiento/calidad", json=calidad).status_code == 200
    comercial = {"radicado": pqr, "acc": "Se repuso el producto", "notif": "Sí", "fResp": "2026-09-22",
                 "cierre": "Sí", "fCierre": "2026-09-22", "respuesta_comercial": "Resuelto"}
    r = admin.post("/api/seguimiento/comercial", json=comercial)
    assert r.status_code == 200, r.get_json()
    pqr_final = admin.get(f"/api/consultar/{pqr}").get_json()
    assert pqr_final["estado"] == "Cerrado"
    assert pqr_final["investigacion"]["cierre"] == "Sí"


def test_vendedor_registra_y_consulta_su_pqr(client):
    from app.db import get_db_cursor
    from app.repos.usuarios import crear_usuario, eliminar_usuario

    crear_usuario(nombre="Vend Flujo", usuario="vend_flujo", contrasena="Clave-Flujo-1", rol="VENDEDOR",
                  documento="66666666", linea_producto="INAPEL", empresa="INAPEL")
    with get_db_cursor() as c:
        c.execute("SELECT id FROM usuarios WHERE usuario = 'vend_flujo'")
        uid = c.fetchone()["id"]
    radicado = None
    try:
        assert client.post("/api/login", json={"usuario": "vend_flujo", "contrasena": "Clave-Flujo-1"}).status_code == 200
        r = client.post("/api/pqr", json={"cliente": "TEST-VENDEDOR", "nit": "1", "tipoSol": "Queja", "desc": "x",
                                          "email": "", "productos": [], "vendedor": "SUPLANTADO"})
        assert r.status_code == 200, r.get_json()
        radicado = r.get_json()["radicado"]
        propio = client.get(f"/api/consultar/{radicado}").get_json()
        assert propio["vendedor"] == "Vend Flujo"
    finally:
        if radicado:
            eliminar_pqr(radicado)
        eliminar_usuario(uid)
