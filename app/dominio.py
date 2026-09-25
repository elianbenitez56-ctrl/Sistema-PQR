"""Reglas de negocio puras (sin base de datos ni Flask): herramientas de análisis y flujo de seguimiento."""
import json

from app.errores import ErrorNegocio
from app.seguridad import ADMIN, LIDER_CALIDAD, ROLES_COMERCIAL

HERRAMIENTAS_ANALISIS = (
    "5 ¿Por qué?",
    "Diagrama Ishikawa",
    "Análisis Pareto",
    "Inspección visual",
    "Ensayos de laboratorio",
    "Comparación muestra patrón",
    "Checklist de inspección"
)

CAMPOS_CALIDAD = (
    ("resp", "Responsable de investigación"),
    ("cargo", "Cargo"),
    ("causa", "Asignación de causa"),
    ("herramientas", "Herramienta utilizada"),
    ("deptos", "Departamentos involucrados")
)

CAMPOS_COMERCIALES = (
    ("acc", "Acciones tomadas"),
    ("notif", "Notificación al cliente"),
    ("fResp", "Fecha de respuesta"),
    ("cierre", "Cierre del PQR"),
    ("fCierre", "Fecha de cierre"),
    ("respuesta_comercial", "Respuesta detallada al cliente")
)

CAMPOS_CALIDAD_EDITABLES = CAMPOS_CALIDAD + (
    ("respuesta_calidad", "Respuesta detallada de Calidad"),
)

# Estados que se pueden asignar manualmente (panel "Base de datos" -> Cambiar
# estado). Debe reflejar las opciones de app/static/js/nucleo.js::mEstado.
ESTADOS_PQR = (
    "Recibido", "Radicado", "En revisión", "En investigación",
    "Pendiente de información", "Pendiente de decisión",
    "Acción en proceso", "Respuesta enviada", "Cerrado", "No procede",
)


# ---------------------------------------------------------- herramientas

def normalizar_herramientas(valor):
    if isinstance(valor, list):
        valores = valor
    else:
        texto = str(valor or "").strip()
        if not texto:
            return []
        try:
            valores = json.loads(texto) if texto.startswith("[") else [texto]
        except (TypeError, ValueError):
            valores = [texto]
    return [str(item).strip() for item in valores if str(item or "").strip()]


def serializar_herramientas(herramientas):
    valores = normalizar_herramientas(herramientas)
    if len(valores) <= 1:
        return valores[0] if valores else ""
    return json.dumps(valores, ensure_ascii=False)


def preparar_herramientas(datos):
    """Valida `herramientas` del cuerpo y las deja normalizadas en `datos`. Lanza ErrorNegocio si no son válidas."""
    if "herramientas" not in datos and "herr" not in datos:
        return []

    herramientas = normalizar_herramientas(datos.get("herramientas", datos.get("herr", [])))

    if len(herramientas) != len(set(herramientas)):
        raise ErrorNegocio("No puede seleccionar la misma herramienta más de una vez.")
    if any(h not in HERRAMIENTAS_ANALISIS for h in herramientas):
        raise ErrorNegocio("La herramienta seleccionada no es válida.")

    datos["herramientas"] = herramientas
    return herramientas


# ---------------------------------------------------------- campos

def campos_faltantes(datos, campos):
    faltantes = []
    for clave, etiqueta in campos:
        valor = datos.get(clave, "")
        if clave == "herramientas":
            if not isinstance(valor, list) or not valor:
                faltantes.append(etiqueta)
        elif not str(valor or "").strip():
            faltantes.append(etiqueta)
    return faltantes


def campos_modificados(datos, actual, campos):
    return [
        etiqueta
        for clave, etiqueta in campos
        if clave in datos
        and str(datos.get(clave, "") or "").strip()
        != str(actual.get(clave, "") or "").strip()
    ]


# ---------------------------------------------------------- flujo de seguimiento

def bloque_no_autorizado(seccion, rol):
    """(campos, nombre) que el rol NO puede modificar al guardar esa sección."""
    if seccion == "calidad" or (seccion is None and rol == LIDER_CALIDAD):
        return CAMPOS_COMERCIALES, "Gestión comercial"
    if seccion == "comercial" or (seccion is None and rol in ROLES_COMERCIAL):
        return CAMPOS_CALIDAD_EDITABLES, "Calidad"
    return (), ""


def _exigir(faltantes, mensaje):
    if faltantes:
        raise ErrorNegocio(mensaje, extra={"faltantes": faltantes})


def _exigir_calidad_completa(calidad_anterior):
    if calidad_anterior != "completada":
        raise ErrorNegocio("Calidad debe completar su sección antes de la gestión comercial.")


def estados_seguimiento(seccion, rol, calidad_anterior, comercial_anterior, faltantes_calidad, faltantes_comercial):
    """Estados (calidad, comercial) resultantes de guardar el seguimiento; valida los campos obligatorios."""
    if seccion == "calidad":
        _exigir(faltantes_calidad, "Complete todos los campos de Calidad.")
        return "completada", comercial_anterior

    if seccion == "comercial":
        _exigir_calidad_completa(calidad_anterior)
        _exigir(faltantes_comercial, "Complete todos los campos de Gestión comercial.")
        return calidad_anterior, "completada"

    if rol in ROLES_COMERCIAL:
        _exigir_calidad_completa(calidad_anterior)
        _exigir(faltantes_comercial, "Complete todos los campos de Gestión comercial.")
        return "completada", "completada"

    _exigir(faltantes_calidad, "Complete todos los campos de Calidad.")
    if rol == ADMIN:
        return "completada", "pendiente" if faltantes_comercial else "completada"
    return "completada", comercial_anterior


def estado_pqr_tras_seguimiento(cierre):
    return "Cerrado" if cierre == "Sí" else "En investigación"
