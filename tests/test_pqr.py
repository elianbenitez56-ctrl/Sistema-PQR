import pytest

from app.repos.pqr import eliminar_pqr


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


def test_investigacion_nueva_no_trae_valores_inventados(admin, pqr):
    inv = admin.get(f"/api/consultar/{pqr}").get_json()["investigacion"]
    assert inv["causa"] == ""
    assert inv["acc"] == ""
    assert inv["notif"] == ""
    assert inv["cierre"] == ""


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


def test_correos_notificacion_radicado_incluye_calidad_y_directora_comercial(monkeypatch):
    from app.servicios.pqr import _correos_notificacion_radicado

    usuarios_falsos = [
        {"rol": "LIDER_CALIDAD", "correo": "calidad@inapel.com", "activo": True},
        {"rol": "DIRECTORA COMERCIAL", "correo": "directora@inapel.com", "activo": True},
        {"rol": "VENDEDOR", "correo": "vendedor@inapel.com", "activo": True},
    ]
    monkeypatch.setattr("app.servicios.pqr.listar_usuarios", lambda: usuarios_falsos)

    assert set(_correos_notificacion_radicado()) == {"calidad@inapel.com", "directora@inapel.com"}


def test_notificacion_calidad_no_falla_completa_si_un_destinatario_falla(monkeypatch):
    """Un destinatario rechazado no debe impedir que los demás reciban el aviso."""
    from app.servicios import correo

    monkeypatch.setattr(correo, "correo_configurado", lambda: True)

    intentos = []

    def _enviar_falso(destinatarios, asunto, html):
        intentos.append(destinatarios[0])
        return (False, "rechazado") if destinatarios[0] == "malo@inapel.com" else (True, "")

    monkeypatch.setattr(correo, "_enviar", _enviar_falso)

    ok, motivo = correo.enviar_notificacion_calidad(
        "PQR-TEST", {}, ["bueno@inapel.com", "malo@inapel.com"]
    )
    assert ok is True
    assert "malo@inapel.com" in motivo
    assert intentos == ["bueno@inapel.com", "malo@inapel.com"]


# ---------------------------------------------------------- descripción y valorización del producto

def _radicar_con_productos(admin, productos):
    return admin.post("/api/pqr", json={
        "cliente": "TEST-PRODUCTO", "nit": "1", "tipoSol": "Queja", "desc": "x", "email": "", "productos": productos,
    })


def test_producto_guarda_descripcion_y_valorizacion(admin):
    productos = [
        {"producto": "Rollo", "lote": "L1", "descripcion": "Bobina con humedad", "valorizacion": "150000"},
        {"producto": "Caja", "lote": "L2", "descripcion": "", "valorizacion": " no aplica "},
        {"producto": "Tapa", "lote": "L3"},
    ]
    r = _radicar_con_productos(admin, productos)
    assert r.status_code == 200, r.get_json()
    radicado = r.get_json()["radicado"]
    try:
        guardados = admin.get(f"/api/consultar/{radicado}").get_json()["productos"]
        assert [(p["descripcion"], p["valorizacion"]) for p in guardados[:2]] == [
            ("Bobina con humedad", "150000"), ("", "No aplica"),
        ]
        assert not guardados[2].get("valorizacion")
    finally:
        eliminar_pqr(radicado)


def test_producto_del_catalogo_conserva_descripcion_y_valorizacion(admin):
    from app.servicios import catalogo

    catalogo.cargar_catalogo()
    p = catalogo._CACHE_PRODUCTOS[0]
    r = _radicar_con_productos(admin, [{**p, "descripcion": "Llegó golpeado", "valorizacion": "2500"}])
    assert r.status_code == 200, r.get_json()
    radicado = r.get_json()["radicado"]
    try:
        guardado = admin.get(f"/api/consultar/{radicado}").get_json()["productos"][0]
        assert (guardado["descripcion"], guardado["valorizacion"]) == ("Llegó golpeado", "2500")
    finally:
        eliminar_pqr(radicado)


@pytest.mark.parametrize("valor", ["abc", "-10", "NaN"])
def test_producto_rechaza_valorizacion_invalida(admin, valor):
    r = _radicar_con_productos(admin, [{"producto": "Rollo", "valorizacion": valor}])
    assert r.status_code == 400
    assert "valorización" in r.get_json()["mensaje"].lower()


# ---------------------------------------------------------- avisos de Comercial (mano a mano) y de cierre

MANO_A_MANO = "Cambio mano a mano"


@pytest.fixture
def avisos(monkeypatch):
    """Captura los avisos de mano a mano y de cierre en vez de enviarlos; fija sus destinatarios."""
    enviados = {"mano": [], "cierre": []}
    monkeypatch.setenv("CORREOS_CAMBIO_MANO_A_MANO", "alejandro@inapel.com; liliana@inapel.com ,logistica@inapel.com")
    monkeypatch.setenv("CORREO_CARTERA", "ines@inapel.com")
    for clave, funcion in (("mano", "enviar_aviso_mano_a_mano"), ("cierre", "enviar_aviso_cierre")):
        monkeypatch.setattr(f"app.servicios.seguimiento.{funcion}",
                            lambda *a, _l=enviados[clave], **k: _l.append(a) or (True, ""))
    return enviados


def _calidad_completa(admin, radicado):
    r = admin.post("/api/seguimiento/calidad", json={
        "radicado": radicado, "resp": "Ana", "cargo": "Calidad", "causa": "A",
        "herramientas": ["5 ¿Por qué?"], "deptos": "Producción"})
    assert r.status_code == 200, r.get_json()


def _comercial(admin, radicado, **cambios):
    datos = {"radicado": radicado, "acc": "Reposición", "notif": "Sí", "fResp": "2026-09-22", "cierre": "No",
             "fCierre": "2026-09-22", "respuesta_comercial": "Respuesta de Comercial", **cambios}
    r = admin.post("/api/seguimiento/comercial", json=datos)
    assert r.status_code == 200, r.get_json()
    return r.get_json()


def test_cambio_mano_a_mano_avisa_a_los_responsables_una_sola_vez(admin, pqr, avisos):
    _calidad_completa(admin, pqr)
    resultado = _comercial(admin, pqr, acc=MANO_A_MANO, observaciones="Entregar en bodega")

    assert resultado["aviso_mano_a_mano"] == {"intentado": True, "enviado": True, "mensaje": ""}
    assert len(avisos["mano"]) == 1 and avisos["cierre"] == []
    radicado, pqr_enviado, inv_enviada, destinatarios = avisos["mano"][0][:4]
    assert radicado == pqr
    assert pqr_enviado["cliente"] == "TEST-CLIENTE"
    assert (inv_enviada["acc"], inv_enviada["observaciones"]) == (MANO_A_MANO, "Entregar en bodega")
    assert destinatarios == ["alejandro@inapel.com", "liliana@inapel.com", "logistica@inapel.com"]
    assert admin.get(f"/api/consultar/{pqr}").get_json()["investigacion"]["observaciones"] == "Entregar en bodega"

    # Guardar de nuevo no repite el aviso.
    resultado = _comercial(admin, pqr, acc=MANO_A_MANO, respuesta_comercial="Ajuste")
    assert resultado["aviso_mano_a_mano"]["intentado"] is False
    assert len(avisos["mano"]) == 1


def test_otra_accion_comercial_no_avisa_mano_a_mano(admin, pqr, avisos):
    _calidad_completa(admin, pqr)
    resultado = _comercial(admin, pqr, acc="Reposición")
    assert resultado["aviso_mano_a_mano"]["intentado"] is False
    assert avisos["mano"] == []


def test_aviso_mano_a_mano_se_reintenta_si_fallo(admin, pqr, avisos, monkeypatch):
    _calidad_completa(admin, pqr)
    monkeypatch.setattr("app.servicios.seguimiento.enviar_aviso_mano_a_mano", lambda *a, **k: (False, "SMTP caído"))
    resultado = _comercial(admin, pqr, acc=MANO_A_MANO)
    assert resultado["aviso_mano_a_mano"] == {"intentado": True, "enviado": False, "mensaje": "SMTP caído"}

    monkeypatch.setattr("app.servicios.seguimiento.enviar_aviso_mano_a_mano", lambda *a, **k: (True, ""))
    assert _comercial(admin, pqr, acc=MANO_A_MANO)["aviso_mano_a_mano"]["enviado"] is True


def test_cierre_avisa_a_cartera_solo_cuando_se_confirma_y_una_vez(admin, pqr, avisos):
    _calidad_completa(admin, pqr)
    abierto = _comercial(admin, pqr, cierre="No")
    assert abierto["aviso_cierre"]["intentado"] is False and avisos["cierre"] == []

    cerrado = _comercial(admin, pqr, cierre="Sí", fCierre="2026-09-30", observaciones="Todo resuelto")
    assert cerrado["aviso_cierre"] == {"intentado": True, "enviado": True, "mensaje": ""}
    radicado, _, inv_enviada, destinatarios = avisos["cierre"][0][:4]
    assert (radicado, destinatarios) == (pqr, ["ines@inapel.com"])
    assert (inv_enviada["cierre"], inv_enviada["fCierre"]) == ("Sí", "2026-09-30")

    assert _comercial(admin, pqr, cierre="Sí")["aviso_cierre"]["intentado"] is False
    assert len(avisos["cierre"]) == 1


def test_calidad_no_dispara_avisos_de_comercial(admin, pqr, avisos):
    _calidad_completa(admin, pqr)
    assert avisos == {"mano": [], "cierre": []}


# ---------------------------------------------------------- contenido de los correos

PQR_CORREO = {
    "cliente": "ACME", "tipoSol": "Reclamo", "desc": "Producto llegó dañado",
    "productos": [{"producto": "Rollo", "detalle_presentacion": "x 12", "descripcion": "Bobina rota",
                   "valorizacion": "150000", "cant": "3", "unidad": "UND"}],
}
INV_CORREO = {"acc": MANO_A_MANO, "respuesta_comercial": "Se cambia <b>hoy</b>", "observaciones": "Retira Logística",
              "fCierre": "2026-09-30"}


def _correo_capturado(monkeypatch):
    from app.servicios import correo

    enviados = []
    monkeypatch.setattr(correo, "correo_configurado", lambda: True)
    monkeypatch.setattr(correo, "_enviar", lambda destinatarios, asunto, html: enviados.append((destinatarios, asunto, html)) or (True, ""))
    return correo, enviados


def test_correo_mano_a_mano_trae_los_datos_del_caso_y_escapa_html(monkeypatch):
    correo, enviados = _correo_capturado(monkeypatch)
    ok, _ = correo.enviar_aviso_mano_a_mano("PQR-2026-0001", PQR_CORREO, INV_CORREO, ["a@inapel.com", "b@inapel.com"])
    assert ok is True
    assert [d for d, _, _ in enviados] == [["a@inapel.com"], ["b@inapel.com"]]
    _, asunto, html = enviados[0]
    assert "PQR-2026-0001" in asunto
    for esperado in ("PQR-2026-0001", "Rollo", "Bobina rota", "150.000", "Cambio mano a mano", "Retira Logística"):
        assert esperado in html, esperado
    assert "Se cambia &lt;b&gt;hoy&lt;/b&gt;" in html and "<b>hoy</b>" not in html


def test_correo_cierre_trae_motivo_solucion_respuesta_y_fecha(monkeypatch):
    correo, enviados = _correo_capturado(monkeypatch)
    ok, _ = correo.enviar_aviso_cierre("PQR-2026-0001", PQR_CORREO, INV_CORREO, ["ines@inapel.com"])
    assert ok is True
    html = enviados[0][2]
    for esperado in ("PQR-2026-0001", "Reclamo", "Producto llegó dañado", "Cambio mano a mano",
                     "Retira Logística", "2026-09-30"):
        assert esperado in html, esperado
    assert "Se cambia &lt;b&gt;hoy&lt;/b&gt;" in html


def test_correo_de_aviso_sin_destinatarios_informa_el_motivo(monkeypatch):
    correo, enviados = _correo_capturado(monkeypatch)
    ok, motivo = correo.enviar_aviso_cierre("PQR-2026-0001", PQR_CORREO, INV_CORREO, [])
    assert ok is False and "destinatarios" in motivo
    assert enviados == []


def test_correos_de_entorno_separa_por_coma_o_punto_y_coma(monkeypatch):
    from app.servicios import correo

    monkeypatch.setenv("X_CORREOS", " a@x.com;b@x.com , ,c@x.com ")
    assert correo.correos_de_entorno("X_CORREOS") == ["a@x.com", "b@x.com", "c@x.com"]
    monkeypatch.delenv("X_CORREOS")
    assert correo.correos_de_entorno("X_CORREOS") == []
