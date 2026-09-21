"""Caso de uso: guardar el seguimiento (Calidad / Comercial) de un PQR."""
import logging

from app.dominio import (
    CAMPOS_CALIDAD,
    CAMPOS_CALIDAD_EDITABLES,
    CAMPOS_COMERCIALES,
    bloque_no_autorizado,
    campos_faltantes,
    campos_modificados,
    estado_pqr_tras_seguimiento,
    estados_seguimiento,
    preparar_herramientas,
)
from app.errores import ErrorNegocio
from app.repos.pqr import (
    actualizar_estado_pqr,
    consultar_pqr,
    guardar_historial,
    guardar_investigacion,
    marcar_notificacion_comercial_enviada,
)
from app.repos.usuarios import listar_usuarios
from app.seguridad import LIDER_CALIDAD, ROLES_COMERCIAL
from app.servicios.correo import enviar_notificacion_comercial

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
    for clave, _ in CAMPOS_CALIDAD_EDITABLES + CAMPOS_COMERCIALES:
        guardar.setdefault(clave, investigacion.get(clave, ""))

    if rol == LIDER_CALIDAD:
        ajenos = CAMPOS_COMERCIALES
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
    avisar = calidad_anterior != "completada" and calidad_nuevo == "completada" and not aviso_enviado

    a_guardar = _datos_a_guardar(datos, investigacion, rol)
    guardar_investigacion(radicado, a_guardar, calidad_nuevo, comercial_nuevo, aviso_enviado)

    nuevo_estado = estado_pqr_tras_seguimiento(a_guardar.get("cierre", "No"))
    actualizar_estado_pqr(radicado, nuevo_estado)
    guardar_historial(radicado, nuevo_estado, "Sistema", "Seguimiento actualizado")

    notificacion_mensaje = ""
    if avisar:
        aviso_enviado, notificacion_mensaje = _avisar_a_comercial(radicado, pqr, url_base)

    return {
        "ok": True,
        "calidad_estado": calidad_nuevo,
        "comercial_estado": comercial_nuevo,
        "notificacion_comercial_enviada": aviso_enviado,
        "notificacion_mensaje": notificacion_mensaje,
    }
