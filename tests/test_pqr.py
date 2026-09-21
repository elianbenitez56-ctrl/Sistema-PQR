def test_flujo_pqr_crear_consultar_estado_eliminar(admin):
    r = admin.post("/api/pqr", json={
        "cliente": "TEST-FLUJO", "nit": "9", "tipoSol": "Reclamo", "desc": "x", "email": "", "productos": [],
    })
    assert r.status_code == 200
    radicado = r.get_json()["radicado"]
    assert radicado.startswith("PQR-")

    try:
        pqr = admin.get(f"/api/consultar/{radicado}").get_json()
        assert pqr["radicado"] == radicado
        assert pqr["estado"] == "Recibido"
        assert any(p["radicado"] == radicado for p in admin.get("/api/pqr/todos").get_json())

        r = admin.post("/api/cambiar_estado", json={"radicado": radicado, "estado": "En revisión"})
        assert r.get_json()["ok"] is True
        pqr = admin.get(f"/api/consultar/{radicado}").get_json()
        assert pqr["estado"] == "En revisión"
        assert len(pqr["historial"]) >= 2
    finally:
        assert admin.delete(f"/api/pqr/{radicado}").status_code == 200

    assert admin.delete(f"/api/pqr/{radicado}").status_code == 404


def test_dashboard_cuenta_pqr(admin, pqr):
    r = admin.get("/api/dashboard")
    assert r.status_code == 200
    assert r.get_json()


def test_seguimiento_calidad(admin, pqr):
    r = admin.post("/api/seguimiento/calidad", json={
        "radicado": pqr, "resp": "Ana", "cargo": "Calidad", "causa": "Materia prima",
        "herramientas": ["5 ¿Por qué?"], "deptos": "Producción",
    })
    assert r.status_code == 200, r.get_json()
    inv = admin.get(f"/api/consultar/{pqr}").get_json()["investigacion"]
    assert inv["resp"] == "Ana"


def test_seguimiento_rechaza_herramienta_invalida(admin, pqr):
    r = admin.post("/api/seguimiento/calidad", json={"radicado": pqr, "herramientas": ["inventada"]})
    assert r.status_code == 400


def test_seguimiento_pqr_inexistente(admin):
    r = admin.post("/api/seguimiento/calidad", json={"radicado": "PQR-1999-0001"})
    assert r.status_code == 404


def test_seguimiento_se_puede_actualizar(admin, pqr):
    base = {"radicado": pqr, "resp": "Ana", "cargo": "Calidad", "causa": "A", "herramientas": ["5 ¿Por qué?"],
            "deptos": "Producción", "fResp": "", "fCierre": ""}
    assert admin.post("/api/seguimiento/calidad", json=base).status_code == 200
    assert admin.post("/api/seguimiento/calidad", json={**base, "causa": "B", "resp": "Luis"}).status_code == 200
    inv = admin.get(f"/api/consultar/{pqr}").get_json()["investigacion"]
    assert (inv["resp"], inv["causa"]) == ("Luis", "B")
