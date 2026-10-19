"""Reglas de negocio puras: no necesitan base de datos."""
import pytest

from app.dominio import (
    CAMPOS_CALIDAD,
    CAMPOS_COMERCIALES,
    bloque_no_autorizado,
    campos_faltantes,
    campos_modificados,
    estado_pqr_tras_seguimiento,
    estados_seguimiento,
    normalizar_herramientas,
    normalizar_valorizacion,
    preparar_herramientas,
    serializar_herramientas,
)
from app.errores import ErrorNegocio


def test_herramientas_normalizan_y_serializan():
    assert normalizar_herramientas('["A", "B"]') == ["A", "B"]
    assert normalizar_herramientas("A") == ["A"]
    assert normalizar_herramientas("") == []
    assert serializar_herramientas(["A"]) == "A"
    assert serializar_herramientas(["A", "B"]) == '["A", "B"]'


def test_preparar_herramientas_rechaza_repetidas_e_invalidas():
    with pytest.raises(ErrorNegocio):
        preparar_herramientas({"herramientas": ["Diagrama Ishikawa", "Diagrama Ishikawa"]})
    with pytest.raises(ErrorNegocio):
        preparar_herramientas({"herramientas": ["inventada"]})
    assert preparar_herramientas({}) == []


def test_campos_faltantes_y_modificados():
    assert "Cargo" in campos_faltantes({"resp": "x"}, CAMPOS_CALIDAD)
    assert campos_faltantes({"herramientas": []}, [("herramientas", "H")]) == ["H"]
    assert campos_modificados({"acc": "nuevo"}, {"acc": "viejo"}, CAMPOS_COMERCIALES) == ["Acciones tomadas"]
    assert campos_modificados({"acc": " igual "}, {"acc": "igual"}, CAMPOS_COMERCIALES) == []


def test_bloque_no_autorizado_por_seccion_y_rol():
    assert bloque_no_autorizado("calidad", "ADMIN")[1] == "Gestión comercial"
    assert bloque_no_autorizado("comercial", "ADMIN")[1] == "Calidad"
    assert bloque_no_autorizado(None, "LIDER_CALIDAD")[1] == "Gestión comercial"
    assert bloque_no_autorizado(None, "COMERCIAL")[1] == "Calidad"
    assert bloque_no_autorizado(None, "ADMIN") == ((), "")


def test_estados_calidad_completa_su_seccion():
    assert estados_seguimiento("calidad", "LIDER_CALIDAD", "pendiente", "pendiente", [], ["x"]) == ("completada", "pendiente")
    with pytest.raises(ErrorNegocio) as e:
        estados_seguimiento("calidad", "LIDER_CALIDAD", "pendiente", "pendiente", ["Cargo"], [])
    assert e.value.extra == {"faltantes": ["Cargo"]}


def test_comercial_exige_calidad_completada():
    with pytest.raises(ErrorNegocio) as e:
        estados_seguimiento("comercial", "COMERCIAL", "pendiente", "pendiente", [], [])
    assert "Calidad debe completar" in e.value.mensaje
    assert estados_seguimiento("comercial", "COMERCIAL", "completada", "pendiente", [], []) == ("completada", "completada")
    with pytest.raises(ErrorNegocio):
        estados_seguimiento("comercial", "COMERCIAL", "completada", "pendiente", [], ["falta"])


def test_admin_en_ruta_general_completa_comercial_solo_si_hay_todo():
    assert estados_seguimiento(None, "ADMIN", "pendiente", "pendiente", [], []) == ("completada", "completada")
    assert estados_seguimiento(None, "ADMIN", "pendiente", "pendiente", [], ["x"]) == ("completada", "pendiente")


def test_estado_del_pqr_tras_seguimiento():
    assert estado_pqr_tras_seguimiento("Sí") == "Cerrado"
    assert estado_pqr_tras_seguimiento("No") == "En investigación"


def test_valorizacion_acepta_vacio_no_aplica_y_numeros():
    assert normalizar_valorizacion("") == ""
    assert normalizar_valorizacion(None) == ""
    assert normalizar_valorizacion(" no aplica ") == "No aplica"
    assert normalizar_valorizacion("1500000") == "1500000"
    assert normalizar_valorizacion(1500000.5) == "1500000.5"
    assert normalizar_valorizacion("0") == "0"


@pytest.mark.parametrize("malo", ["abc", "-5", "NaN", "Infinity", "1.500.000,00"])
def test_valorizacion_rechaza_texto_negativos_y_no_finitos(malo):
    with pytest.raises(ErrorNegocio):
        normalizar_valorizacion(malo)


def test_observaciones_son_de_comercial_y_calidad_no_puede_modificarlas():
    campos, _ = bloque_no_autorizado("calidad", "LIDER_CALIDAD")
    assert campos_modificados({"observaciones": "nueva"}, {"observaciones": ""}, campos) == ["Observaciones"]
    # Es opcional: no cuenta como campo obligatorio de Comercial.
    assert campos_faltantes({}, CAMPOS_COMERCIALES) == [etiqueta for _, etiqueta in CAMPOS_COMERCIALES]
    assert all(clave != "observaciones" for clave, _ in CAMPOS_COMERCIALES)
