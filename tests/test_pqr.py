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


def test_cambiar_estado_de_pqr_inexistente(admin):
    r = admin.post("/api/cambiar_estado", json={"radicado": "PQR-1999-0001", "estado": "Cerrado"})
    assert r.status_code == 404
    assert admin.post("/api/cambiar_estado", json={"radicado": "x"}).status_code == 400


def test_fecha_y_hora_de_recepcion_tienen_formato_valido(admin, pqr):
    import re
    from datetime import datetime

    p = admin.get(f"/api/consultar/{pqr}").get_json()
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", p["fechaRec"])
    datetime.fromisoformat(p["savedAt"])  # no lanza si el formato es válido


def test_aviso_comercial_se_reintenta_si_fallo_antes(admin, pqr, monkeypatch):
    """Si el correo a Comercial falló la primera vez, el siguiente guardado de Calidad lo reintenta."""
    base = {"radicado": pqr, "resp": "Ana", "cargo": "Calidad", "causa": "A",
            "herramientas": ["5 ¿Por qué?"], "deptos": "Producción"}

    monkeypatch.setattr("app.servicios.seguimiento.enviar_notificacion_comercial",
                         lambda *a, **k: (False, "SMTP no configurado"))
    r = admin.post("/api/seguimiento/calidad", json=base)
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["notificacion_comercial_enviada"] is False

    monkeypatch.setattr("app.servicios.seguimiento.enviar_notificacion_comercial",
                         lambda *a, **k: (True, ""))
    r = admin.post("/api/seguimiento/calidad", json={**base, "causa": "B"})
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["notificacion_comercial_enviada"] is True
