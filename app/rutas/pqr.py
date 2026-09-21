from flask import Blueprint, current_app, jsonify, request, session

from app.repos.pqr import (
    consultar_pqr,
    correo_confirmacion_enviado,
    eliminar_pqr,
    guardar_pqr,
    listar_pqrs,
    marcar_correo_confirmacion,
    obtener_dashboard,
)
from app.repos.usuarios import obtener_usuario_por_id
from app.seguridad import ROLES_INVESTIGACION, ROLES_VER_TODO, VENDEDOR, rol_requerido, sesion_requerida
from app.servicios.correo import enviar_confirmacion_pqr
from app.validaciones import preparar_productos_catalogo, validar_correo

bp = Blueprint("pqr", __name__)


# ==========================================================
# GUARDAR PQR
# ==========================================================

@bp.route("/api/pqr", methods=["POST"])
@sesion_requerida
def api_guardar_pqr():

    datos = request.get_json()

    if not datos:
        return jsonify({
            "ok": False,
            "mensaje": "No se recibieron datos."
        }), 400

    productos = datos.get("productos", []) or []
    if not isinstance(productos, list):
        return jsonify({
            "ok": False,
            "mensaje": "La información de productos no es válida."
        }), 400

    try:
        productos, error_catalogo = preparar_productos_catalogo(productos)
    except FileNotFoundError as error:
        return jsonify({
            "ok": False,
            "mensaje": f"No fue posible consultar el catálogo maestro: {error}"
        }), 503
    except ValueError as error:
        return jsonify({
            "ok": False,
            "mensaje": str(error)
        }), 400

    if error_catalogo:
        return jsonify({
            "ok": False,
            "mensaje": error_catalogo
        }), 400

    datos["productos"] = productos

    usuario_actual = obtener_usuario_por_id(session["usuario_id"])

    if not usuario_actual or not usuario_actual.get("activo", True):
        session.clear()
        return jsonify({
            "ok": False,
            "mensaje": "La sesión del usuario ya no es válida. Inicie sesión nuevamente."
        }), 401

    radicado = None

    # Los datos del receptor se toman siempre del usuario autenticado.
    # Los valores enviados por el navegador no pueden alterarlos.
    rol_usuario = str(usuario_actual.get("rol", "") or "").strip().upper()
    datos["usuario_id"] = usuario_actual["id"]
    datos["vendedor"] = usuario_actual.get("nombre", "")
    datos["linea"] = usuario_actual.get("linea_producto", "")
    datos["empresa"] = usuario_actual.get("empresa", "INAPEL")
    datos["documento_receptor"] = usuario_actual.get("documento", "")
    datos["correo_receptor"] = usuario_actual.get("correo", "")
    datos["telefono_receptor"] = usuario_actual.get("telefono", "")
    datos["cargo_receptor"] = rol_usuario if rol_usuario == VENDEDOR else ""
    datos["area_receptor"] = usuario_actual.get("linea_producto", "") or ""

    # 1) SIEMPRE se guarda la PQR primero. El correo nunca bloquea el registro.
    try:
        guardar_pqr(datos)
        radicado = datos["radicado"]
    except Exception:
        current_app.logger.exception(
            "Error al guardar la PQR %s",
            radicado or "sin-radicado"
        )
        return jsonify({
            "ok": False,
            "mensaje": "No fue posible guardar la PQR. El registro no fue confirmado."
        }), 500

    try:
        pqr_verificada = consultar_pqr(radicado)
    except Exception:
        current_app.logger.exception(
            "Error al verificar la persistencia de la PQR %s",
            radicado
        )
        return jsonify({
            "ok": False,
            "mensaje": "La PQR fue procesada, pero no pudo verificarse en la base de datos."
        }), 500

    if not pqr_verificada or str(pqr_verificada.get("radicado", "")).strip().upper() != str(radicado).strip().upper():
        current_app.logger.error(
            "La PQR %s no fue encontrada después de guardarla",
            radicado
        )
        return jsonify({
            "ok": False,
            "mensaje": "La PQR no pudo verificarse después de guardarla. No se confirmó el registro."
        }), 500

    email_enviado = False
    email_estado = "no_intentado"
    email_mensaje = ""

    correo_cliente = str(datos.get("email", "") or "").strip()

    if not correo_cliente:
        email_estado = "sin_correo"
        email_mensaje = "La PQR no tiene un correo electrónico registrado para enviar la confirmación."

    elif not validar_correo(correo_cliente):
        email_estado = "correo_invalido"
        email_mensaje = "La PQR se guardó, pero el correo del cliente no es válido y no se envió confirmación."

    elif correo_confirmacion_enviado(radicado):
        # Evita duplicados: la confirmación ya se envió para este radicado.
        email_estado = "ya_enviado"
        email_enviado = True
        email_mensaje = "La confirmación ya había sido enviada para este radicado."

    else:
        try:
            ok, motivo = enviar_confirmacion_pqr(radicado, correo_cliente, datos)
            if ok:
                marcar_correo_confirmacion(radicado, True)
                email_enviado = True
                email_estado = "enviado"
                email_mensaje = "Se envió la confirmación al correo registrado."
            else:
                marcar_correo_confirmacion(radicado, False)
                email_estado = "no_enviado"
                email_mensaje = (
                    "PQR registrada correctamente, pero no fue posible enviar "
                    f"el correo de confirmación ({motivo})."
                )
                print(f"[correo] {email_mensaje}")
        except Exception as e:
            # Red de seguridad: ningún error al enviar puede romper el registro.
            marcar_correo_confirmacion(radicado, False)
            email_estado = "no_enviado"
            email_mensaje = "PQR registrada correctamente, pero no fue posible enviar el correo de confirmación."
            print(f"[correo] Error inesperado al enviar para {radicado}: {e}")

    return jsonify({
        "ok": True,
        "radicado": radicado,
        "mensaje": "PQR guardado correctamente",
        "email_enviado": email_enviado,
        "email_estado": email_estado,
        "email_mensaje": email_mensaje
    })


# ==========================================================
# LISTAR TODOS LOS PQR
# ==========================================================

@bp.route("/api/pqr/todos", methods=["GET"])
@rol_requerido(*ROLES_VER_TODO)
def api_pqr_todos():

    return jsonify(listar_pqrs())


# ==========================================================
# ELIMINAR PQR
# ==========================================================

@bp.route("/api/pqr/<radicado>", methods=["DELETE"])
@rol_requerido(*ROLES_INVESTIGACION)
def api_eliminar_pqr(radicado):

    resultado = eliminar_pqr(radicado)

    if resultado == "not_found":
        return jsonify({
            "ok": False,
            "mensaje": "El registro ya fue eliminado o no existe."
        }), 404

    if resultado is not True:
        return jsonify({
            "ok": False,
            "mensaje": "No fue posible eliminar el registro."
        }), 500

    return jsonify({
        "ok": True,
        "mensaje": "Registro eliminado correctamente."
    })


# ==========================================================
# CONSULTAR PQR
# ==========================================================

@bp.route("/api/consultar/<valor>", methods=["GET"])
@sesion_requerida
def api_consultar(valor):

    pqr = consultar_pqr(valor)

    if not pqr:
        return jsonify({
            "error": "PQR no encontrado"
        }), 404

    # Un vendedor solo puede consultar los PQR que él mismo registró.
    if session.get("rol") == VENDEDOR:
        if str(pqr.get("usuario_id", "")) != str(session.get("usuario_id", "")):
            return jsonify({
                "error": "No tiene permisos para consultar este PQR."
            }), 403

    return jsonify(pqr)




# ==========================================================
# DASHBOARD
# ==========================================================

@bp.route("/api/dashboard", methods=["GET"])
@rol_requerido(*ROLES_VER_TODO)
def api_dashboard():

    return jsonify(obtener_dashboard())
