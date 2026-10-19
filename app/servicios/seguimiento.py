"""Caso de uso: guardar el seguimiento (Calidad / Comercial) de un PQR."""
import logging

from app.dominio import (
    ACCION_MANO_A_MANO,
    CAMPOS_CALIDAD,
    CAMPOS_CALIDAD_EDITABLES,
    CAMPOS_COMERCIALES,
    CAMPOS_COMERCIALES_EDITABLES,
    bloque_no_autorizado,
    campos_faltantes,
    campos_modificados,
    estado_pqr_tras_seguimiento,
    estados_seguimiento,
    etiqueta_historial_seguimiento,
    preparar_herramientas,
)
from app.errores import ErrorNegocio
from app.repos.pqr import (
    actualizar_estado_pqr,
    consultar_pqr,
    guardar_historial,
    guardar_investigacion,
    marcar_aviso_enviado,
    marcar_notificacion_comercial_enviada,
)
from app.repos.usuarios import listar_usuarios
from app.seguridad import LIDER_CALIDAD, ROLES_COMERCIAL
from app.servicios.correo import (
    correos_de_entorno,
    enviar_aviso_cierre,
    enviar_aviso_mano_a_mano,
    enviar_notificacion_comercial,
)

logger = logging.getLogger(__name__)


def _correos_comerciales():
    """Correos únicos de los usuarios comerciales activos."""
    correos = {}
    for usuario in listar_usuarios():
        rol = str(usuario.get("rol", "") or "").strip().upper()
        correo = str(usuario.get("correo", "") or "").strip()
        if rol in ROLES_COMERCIAL and usuario.get("activo", True) and correo:
            correos.setdefault(correo.lower(), correo)
    return list(correos.values())


def _estado(investigacion, clave):
    return str(investigacion.get(clave, "pendiente") or "pendiente").strip().lower()


def _datos_a_guardar(datos, investigacion, rol):
    """Completa lo que no llegó con lo ya guardado y protege la sección ajena al rol."""
    guardar = dict(datos)
    for clave, _ in CAMPOS_CALIDAD_EDITABLES + CAMPOS_COMERCIALES_EDITABLES:
        guardar.setdefault(clave, investigacion.get(clave, ""))

    if rol == LIDER_CALIDAD:
        ajenos = CAMPOS_COMERCIALES_EDITABLES
    elif rol in ROLES_COMERCIAL:
        ajenos = CAMPOS_CALIDAD_EDITABLES
    else:
        ajenos = ()
    for clave, _ in ajenos:
        guardar[clave] = investigacion.get(clave, "")
    return guardar


def _avisar_a_comercial(radicado, pqr, url_base):
    enviado, mensaje = enviar_notificacion_comercial(
        radicado, pqr, _correos_comerciales(), [etiqueta for _, etiqueta in CAMPOS_COMERCIALES], url_base
    )
    if enviado:
        marcar_notificacion_comercial_enviada(radicado)
    return enviado, mensaje


SIN_AVISO = {"intentado": False, "enviado": False, "mensaje": ""}


def _avisar(radicado, aviso, enviar, pqr, investigacion, variable_correos, url_base):
    """Envía un aviso de Comercial a los correos de la variable de entorno y, si salió, lo marca para no repetirlo.
    Nunca falla: el resultado se informa en la respuesta."""
    try:
        enviado, mensaje = enviar(radicado, pqr, investigacion, correos_de_entorno(variable_correos), url_base)
    except Exception:
        logger.exception("Error inesperado en el aviso %s de %s", aviso, radicado)
        enviado, mensaje = False, "Error inesperado al enviar el correo."
    if enviado:
        marcar_aviso_enviado(radicado, aviso)
    else:
        logger.warning("No se envió el aviso %s de %s: %s", aviso, radicado, mensaje)
    return {"intentado": True, "enviado": enviado, "mensaje": mensaje}


def guardar_seguimiento(datos, seccion, rol, url_base):
    """`seccion` es "calidad", "comercial" o None (ruta general: se deduce del rol)."""
    datos = dict(datos or {})
    radicado = str(datos.get("radicado", "") or "").strip()
    if not radicado:
        raise ErrorNegocio("Debe indicar el radicado del PQR.")

    preparar_herramientas(datos)

    pqr = consultar_pqr(radicado)
    if not pqr:
        raise ErrorNegocio("El PQR no existe.", 404)

    investigacion = pqr.get("investigacion") or {}
    calidad_anterior = _estado(investigacion, "calidad_estado")
    comercial_anterior = _estado(investigacion, "comercial_estado")
    aviso_enviado = bool(investigacion.get("notificacion_comercial_enviada", False))

    campos_ajenos, nombre_bloque = bloque_no_autorizado(seccion, rol)
    no_autorizados = campos_modificados(datos, investigacion, campos_ajenos)
    if no_autorizados:
        raise ErrorNegocio(
            f"No tiene permisos para modificar la sección {nombre_bloque}.", 403, extra={"campos": no_autorizados}
        )

    calidad_nuevo, comercial_nuevo = estados_seguimiento(
        seccion, rol, calidad_anterior, comercial_anterior,
        campos_faltantes(datos, CAMPOS_CALIDAD), campos_faltantes(datos, CAMPOS_COMERCIALES),
    )
    # Se reintenta en cada guardado de Calidad mientras el aviso no se haya podido enviar
    # (p. ej. si el servicio de correo falló la primera vez).
    avisar = calidad_nuevo == "completada" and not aviso_enviado

    a_guardar = _datos_a_guardar(datos, investigacion, rol)
    guardar_investigacion(radicado, a_guardar, calidad_nuevo, comercial_nuevo, aviso_enviado)

    cierre = a_guardar.get("cierre", "No")
    nuevo_estado = estado_pqr_tras_seguimiento(cierre)
    actualizar_estado_pqr(radicado, nuevo_estado)
    etiqueta_historial = etiqueta_historial_seguimiento(seccion, cierre)
    guardar_historial(radicado, etiqueta_historial, "Sistema", "Seguimiento actualizado")

    notificacion_mensaje = ""
    if avisar:
        aviso_enviado, notificacion_mensaje = _avisar_a_comercial(radicado, pqr, url_base)

    # Solo con la gestión comercial completa; se reintentan en cada guardado hasta que salgan.
    avisos = {}
    for aviso, aplica, enviar, variable_correos in (
        ("mano_a_mano", a_guardar.get("acc") == ACCION_MANO_A_MANO, enviar_aviso_mano_a_mano, "CORREOS_CAMBIO_MANO_A_MANO"),
        ("cierre", cierre == "Sí", enviar_aviso_cierre, "CORREO_CARTERA"),
    ):
        pendiente = comercial_nuevo == "completada" and aplica and not investigacion.get(f"aviso_{aviso}_enviado")
        avisos[f"aviso_{aviso}"] = (
            _avisar(radicado, aviso, enviar, pqr, a_guardar, variable_correos, url_base) if pendiente else SIN_AVISO
        )

    return {
        "ok": True,
        **avisos,
        "calidad_estado": calidad_nuevo,
        "comercial_estado": comercial_nuevo,
        "notificacion_comercial_enviada": aviso_enviado,
        "notificacion_comercial_intentada": avisar,
        "notificacion_mensaje": notificacion_mensaje,
    }
