from flask import Blueprint, jsonify, request, session

from app.repos.pqr import (
    actualizar_estado_pqr,
    consultar_pqr,
    guardar_historial,
    guardar_investigacion,
    marcar_notificacion_comercial_enviada,
)
from app.seguridad import (
    ADMIN,
    LIDER_CALIDAD,
    ROLES_COMERCIAL,
    ROLES_INVESTIGACION,
    ROLES_SEGUIMIENTO,
    rol_requerido,
)
from app.servicios.correo import enviar_notificacion_comercial
from app.validaciones import campos_faltantes, campos_modificados, correos_comerciales, preparar_herramientas

bp = Blueprint("seguimiento", __name__)


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




# ==========================================================
# GUARDAR SEGUIMIENTO
# ==========================================================

def _guardar_seguimiento(datos, seccion=None):

    datos = dict(datos or {})
    radicado = str(datos.get("radicado", "") or "").strip()

    if not radicado:
        return jsonify({
            "ok": False,
            "mensaje": "Debe indicar el radicado del PQR."
        }), 400

    _, error_herramientas = preparar_herramientas(datos)
    if error_herramientas:
        return jsonify({
            "ok": False,
            "mensaje": error_herramientas
        }), 400

    pqr = consultar_pqr(radicado)
    if not pqr:
        return jsonify({
            "ok": False,
            "mensaje": "El PQR no existe."
        }), 404

    investigacion = pqr.get("investigacion", {}) or {}
    rol_actual = session.get("rol")
    calidad_estado_anterior = str(
        investigacion.get("calidad_estado", "pendiente") or "pendiente"
    ).strip().lower()
    comercial_estado_anterior = str(
        investigacion.get("comercial_estado", "pendiente") or "pendiente"
    ).strip().lower()
    aviso_enviado = bool(investigacion.get("notificacion_comercial_enviada", False))

    if seccion == "calidad":
        bloque_no_autorizado = CAMPOS_COMERCIALES
        bloque_nombre = "Gestión comercial"
    elif seccion == "comercial":
        bloque_no_autorizado = CAMPOS_CALIDAD_EDITABLES
        bloque_nombre = "Calidad"
    elif rol_actual == LIDER_CALIDAD:
        bloque_no_autorizado = CAMPOS_COMERCIALES
        bloque_nombre = "Gestión comercial"
    elif rol_actual in ROLES_COMERCIAL:
        bloque_no_autorizado = CAMPOS_CALIDAD_EDITABLES
        bloque_nombre = "Calidad"
    else:
        bloque_no_autorizado = ()
        bloque_nombre = ""

    campos_no_autorizados = campos_modificados(
        datos,
        investigacion,
        bloque_no_autorizado
    )
    if campos_no_autorizados:
        return jsonify({
            "ok": False,
            "mensaje": f"No tiene permisos para modificar la sección {bloque_nombre}.",
            "campos": campos_no_autorizados
        }), 403

    datos_guardar = dict(datos)
    for clave, _ in CAMPOS_CALIDAD_EDITABLES + CAMPOS_COMERCIALES:
        if clave not in datos_guardar:
            datos_guardar[clave] = investigacion.get(clave, "")

    if rol_actual == LIDER_CALIDAD:
        for clave, _ in CAMPOS_COMERCIALES:
            datos_guardar[clave] = investigacion.get(clave, "")
    elif rol_actual in ROLES_COMERCIAL:
        for clave, _ in CAMPOS_CALIDAD_EDITABLES:
            datos_guardar[clave] = investigacion.get(clave, "")

    faltantes_calidad = campos_faltantes(datos, CAMPOS_CALIDAD)
    faltantes_comercial = campos_faltantes(datos, CAMPOS_COMERCIALES)

    if seccion == "calidad":
        if faltantes_calidad:
            return jsonify({
                "ok": False,
                "mensaje": "Complete todos los campos de Calidad.",
                "faltantes": faltantes_calidad
            }), 400
        calidad_estado_nuevo = "completada"
        comercial_estado_nuevo = comercial_estado_anterior
    elif seccion == "comercial":
        if calidad_estado_anterior != "completada":
            return jsonify({
                "ok": False,
                "mensaje": "Calidad debe completar su sección antes de la gestión comercial."
            }), 400
        if faltantes_comercial:
            return jsonify({
                "ok": False,
                "mensaje": "Complete todos los campos de Gestión comercial.",
                "faltantes": faltantes_comercial
            }), 400
        calidad_estado_nuevo = calidad_estado_anterior
        comercial_estado_nuevo = "completada"
    elif rol_actual in ROLES_COMERCIAL:
        if calidad_estado_anterior != "completada":
            return jsonify({
                "ok": False,
                "mensaje": "Calidad debe completar su sección antes de la gestión comercial."
            }), 400
        if faltantes_comercial:
            return jsonify({
                "ok": False,
                "mensaje": "Complete todos los campos de Gestión comercial.",
                "faltantes": faltantes_comercial
            }), 400
        calidad_estado_nuevo = "completada"
        comercial_estado_nuevo = "completada"
    else:
        if faltantes_calidad:
            return jsonify({
                "ok": False,
                "mensaje": "Complete todos los campos de Calidad.",
                "faltantes": faltantes_calidad
            }), 400
        calidad_estado_nuevo = "completada"
        if rol_actual == ADMIN:
            comercial_estado_nuevo = (
                "completada" if not faltantes_comercial else "pendiente"
            )
        else:
            comercial_estado_nuevo = comercial_estado_anterior

    transicion_calidad = (
        calidad_estado_anterior != "completada"
        and calidad_estado_nuevo == "completada"
        and not aviso_enviado
    )

    resultado_guardado = guardar_investigacion(
        datos_guardar,
        calidad_estado=calidad_estado_nuevo,
        comercial_estado=comercial_estado_nuevo,
        notificacion_comercial_enviada=aviso_enviado
    )

    notificacion_enviada = aviso_enviado
    notificacion_mensaje = ""

    if transicion_calidad:
        destinatarios = correos_comerciales()
        notificacion_enviada, notificacion_mensaje = enviar_notificacion_comercial(
            radicado,
            pqr,
            destinatarios,
            [etiqueta for _, etiqueta in CAMPOS_COMERCIALES],
            request.host_url
        )

        if notificacion_enviada:
            marcar_notificacion_comercial_enviada(radicado)

    resultado_guardado["notificacion_comercial_enviada"] = notificacion_enviada

    return jsonify({
        "ok": True,
        **resultado_guardado,
        "notificacion_mensaje": notificacion_mensaje
    })


@bp.route("/api/seguimiento/calidad", methods=["POST"])
@rol_requerido(ADMIN, LIDER_CALIDAD)
def api_seguimiento_calidad():
    return _guardar_seguimiento(request.get_json() or {}, "calidad")


@bp.route("/api/seguimiento/comercial", methods=["POST"])
@rol_requerido(ADMIN, *ROLES_COMERCIAL)
def api_seguimiento_comercial():
    return _guardar_seguimiento(request.get_json() or {}, "comercial")


# Compatibilidad con clientes anteriores que todavía usan el endpoint general.
@bp.route("/api/seguimiento", methods=["POST"])
@rol_requerido(*ROLES_SEGUIMIENTO)
def api_seguimiento():
    return _guardar_seguimiento(request.get_json() or {})


# ==========================================================
# CAMBIAR ESTADO
# ==========================================================

@bp.route("/api/cambiar_estado", methods=["POST"])
@rol_requerido(*ROLES_INVESTIGACION)
def api_estado():

    datos = request.get_json()

    if not datos or "radicado" not in datos or "estado" not in datos:
        return jsonify({"ok": False, "mensaje": "Faltan datos"}), 400

    actualizar_estado_pqr(
        datos["radicado"],
        datos["estado"]
    )

    guardar_historial(
        datos["radicado"],
        datos["estado"],
        session.get("nombre", "Sistema"),
        "Estado actualizado"
    )

    return jsonify({
        "ok": True
    })
