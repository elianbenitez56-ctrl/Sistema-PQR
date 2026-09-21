"""Casos de uso del PQR: registrar, consultar, cambiar estado y eliminar."""
import logging

from app.errores import ErrorNegocio
from app.repos.pqr import (
    actualizar_estado_pqr,
    consultar_pqr,
    correo_confirmacion_enviado,
    crear_pqr,
    eliminar_pqr,
    guardar_historial,
    marcar_correo_confirmacion,
)
from app.repos.usuarios import obtener_usuario_por_id
from app.seguridad import VENDEDOR
from app.servicios.catalogo import LINEAS_PRODUCTO, buscar_productos
from app.servicios.correo import enviar_confirmacion_pqr
from app.validaciones import validar_correo

logger = logging.getLogger(__name__)

TIPO_DOC_PRODUCTO = "Factura de venta"


# ---------------------------------------------------------- productos del catálogo

def _texto(valor):
    return str(valor or "").strip()


def _coincide_con_catalogo(producto, catalogo):
    if any(_texto(producto.get(c)) != _texto(catalogo.get(c)) for c in ("detalle_presentacion", "producto")):
        return False
    unidad_catalogo = _texto(catalogo.get("unidad"))
    return not unidad_catalogo or _texto(producto.get("unidad")) == unidad_catalogo


def _normalizar_producto(producto):
    """Producto validado contra el catálogo maestro (o tal cual si viene de un cliente antiguo sin catálogo)."""
    producto = dict(producto)
    producto["tipoDoc"] = TIPO_DOC_PRODUCTO

    linea = _texto(producto.get("linea")).upper()
    referencia = _texto(producto.get("referencia_siesa"))

    # Conserva productos de clientes antiguos que no usaban catálogo.
    if not linea:
        return producto

    if linea not in LINEAS_PRODUCTO:
        raise ErrorNegocio("La línea de producto no es válida.")
    if not referencia:
        raise ErrorNegocio("Debe indicar una REFERENCIA SIESA del catálogo.")

    coincidencias = buscar_productos(linea, referencia)
    if not coincidencias:
        raise ErrorNegocio("Referencia no encontrada en el catálogo.")

    maestro = next((c for c in coincidencias if _coincide_con_catalogo(producto, c)), None)
    if not maestro:
        raise ErrorNegocio("Seleccione una coincidencia válida del catálogo.")

    normalizado = {
        "linea": maestro["linea"],
        "referencia_siesa": maestro["referencia_siesa"],
        "detalle_presentacion": maestro["detalle_presentacion"],
        "producto": maestro["producto"],
        "unidad": maestro["unidad"] or _texto(producto.get("unidad")),
    }
    for campo in ("lote", "fechaEmp", "cant", "numDoc"):
        normalizado[campo] = producto.get(campo, "")
    normalizado["tipoDoc"] = TIPO_DOC_PRODUCTO
    return normalizado


def _preparar_productos(productos):
    if not isinstance(productos, list):
        raise ErrorNegocio("La información de productos no es válida.")
    try:
        return [_normalizar_producto(p) if isinstance(p, dict) else p for p in productos]
    except FileNotFoundError as error:
        raise ErrorNegocio(f"No fue posible consultar el catálogo maestro: {error}", 503) from error
    except ValueError as error:
        raise ErrorNegocio(str(error)) from error


# ---------------------------------------------------------- registrar

def _usuario_activo(usuario_id):
    usuario = obtener_usuario_por_id(usuario_id)
    if not usuario or not usuario.get("activo", True):
        raise ErrorNegocio(
            "La sesión del usuario ya no es válida. Inicie sesión nuevamente.", 401, cerrar_sesion=True
        )
    return usuario


def _asignar_receptor(datos, usuario):
    """Los datos del receptor salen siempre del usuario autenticado; el navegador no puede alterarlos."""
    rol = _texto(usuario.get("rol")).upper()
    datos["usuario_id"] = usuario["id"]
    datos["vendedor"] = usuario.get("nombre", "")
    datos["linea"] = usuario.get("linea_producto", "")
    datos["empresa"] = usuario.get("empresa", "INAPEL")
    datos["documento_receptor"] = usuario.get("documento", "")
    datos["correo_receptor"] = usuario.get("correo", "")
    datos["telefono_receptor"] = usuario.get("telefono", "")
    datos["cargo_receptor"] = rol if rol == VENDEDOR else ""
    datos["area_receptor"] = usuario.get("linea_producto", "") or ""


def _guardar_y_verificar(datos):
    """Guarda el PQR y comprueba que quedó persistido. Devuelve el radicado."""
    try:
        crear_pqr(datos)
    except Exception as error:
        logger.exception("Error al guardar la PQR")
        raise ErrorNegocio("No fue posible guardar la PQR. El registro no fue confirmado.", 500) from error
    radicado = datos["radicado"]

    try:
        verificada = consultar_pqr(radicado)
    except Exception as error:
        logger.exception("Error al verificar la persistencia de la PQR %s", radicado)
        raise ErrorNegocio(
            "La PQR fue procesada, pero no pudo verificarse en la base de datos.", 500
        ) from error

    if not verificada or _texto(verificada.get("radicado")).upper() != _texto(radicado).upper():
        logger.error("La PQR %s no fue encontrada después de guardarla", radicado)
        raise ErrorNegocio(
            "La PQR no pudo verificarse después de guardarla. No se confirmó el registro.", 500
        )
    return radicado


def _enviar_confirmacion(radicado, datos):
    """Correo de confirmación al cliente. Nunca falla: el resultado se informa en la respuesta."""
    correo = _texto(datos.get("email"))

    if not correo:
        return _resultado_correo(False, "sin_correo",
                                 "La PQR no tiene un correo electrónico registrado para enviar la confirmación.")
    if not validar_correo(correo):
        return _resultado_correo(False, "correo_invalido",
                                 "La PQR se guardó, pero el correo del cliente no es válido y no se envió confirmación.")
    if correo_confirmacion_enviado(radicado):
        return _resultado_correo(True, "ya_enviado", "La confirmación ya había sido enviada para este radicado.")

    try:
        enviado, motivo = enviar_confirmacion_pqr(radicado, correo, datos)
    except Exception:
        logger.exception("Error inesperado al enviar la confirmación de %s", radicado)
        enviado, motivo = False, ""

    marcar_correo_confirmacion(radicado, enviado)
    if enviado:
        return _resultado_correo(True, "enviado", "Se envió la confirmación al correo registrado.")

    logger.warning("No se envió la confirmación de %s: %s", radicado, motivo)
    detalle = f" ({motivo})" if motivo else ""
    return _resultado_correo(False, "no_enviado",
                             f"PQR registrada correctamente, pero no fue posible enviar el correo de confirmación{detalle}.")


def _resultado_correo(enviado, estado, mensaje):
    return {"email_enviado": enviado, "email_estado": estado, "email_mensaje": mensaje}


def registrar_pqr(datos, usuario_id):
    if not datos:
        raise ErrorNegocio("No se recibieron datos.")

    datos["productos"] = _preparar_productos(datos.get("productos", []) or [])
    _asignar_receptor(datos, _usuario_activo(usuario_id))

    # El PQR siempre se guarda primero: el correo nunca bloquea el registro.
    radicado = _guardar_y_verificar(datos)

    return {
        "ok": True,
        "radicado": radicado,
        "mensaje": "PQR guardado correctamente",
        **_enviar_confirmacion(radicado, datos),
    }


# ---------------------------------------------------------- consultar / estado / eliminar

def consultar(valor, rol, usuario_id):
    pqr = consultar_pqr(valor)
    if not pqr:
        raise ErrorNegocio("PQR no encontrado", 404, clave="error")

    # Un vendedor solo puede consultar los PQR que él mismo registró.
    if rol == VENDEDOR and str(pqr.get("usuario_id", "")) != str(usuario_id or ""):
        raise ErrorNegocio("No tiene permisos para consultar este PQR.", 403, clave="error")
    return pqr


def cambiar_estado(datos, nombre_usuario):
    if not datos or "radicado" not in datos or "estado" not in datos:
        raise ErrorNegocio("Faltan datos")

    if not actualizar_estado_pqr(datos["radicado"], datos["estado"]):
        raise ErrorNegocio("El PQR no existe.", 404)
    guardar_historial(datos["radicado"], datos["estado"], nombre_usuario or "Sistema", "Estado actualizado")


def eliminar(radicado):
    resultado = eliminar_pqr(radicado)
    if resultado == "not_found":
        raise ErrorNegocio("El registro ya fue eliminado o no existe.", 404)
    if resultado is not True:
        raise ErrorNegocio("No fue posible eliminar el registro.", 500)
