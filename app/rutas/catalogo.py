from flask import Blueprint, jsonify, request
from app.seguridad import ADMIN, rol_requerido, sesion_requerida
from app.servicios.catalogo import LINEAS_PRODUCTO, buscar_productos, recargar_catalogo

bp = Blueprint("catalogo", __name__)


# ==========================================================
# CATÁLOGO DE PRODUCTOS
# ==========================================================

@bp.route("/api/catalogo/productos", methods=["GET"])
@sesion_requerida
def api_catalogo_productos():

    linea = str(request.args.get("linea", "") or "").strip().upper()
    referencia_siesa = str(request.args.get("referencia_siesa", "") or "").strip()

    if linea not in LINEAS_PRODUCTO:
        return jsonify({
            "ok": False,
            "mensaje": "La línea de producto no es válida."
        }), 400

    if not referencia_siesa:
        return jsonify({
            "ok": False,
            "mensaje": "Debe indicar una REFERENCIA SIESA."
        }), 400

    try:
        productos = buscar_productos(linea, referencia_siesa)
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

    respuesta = {
        "ok": True,
        "linea": linea,
        "referencia_siesa": referencia_siesa,
        "total": len(productos),
        "productos": productos
    }
    if not productos:
        respuesta["mensaje"] = "Referencia no encontrada en el catálogo."

    return jsonify(respuesta)


@bp.route("/api/catalogo/recargar", methods=["POST"])
@rol_requerido(ADMIN)
def api_catalogo_recargar():

    try:
        productos = recargar_catalogo()
    except Exception as error:
        return jsonify({
            "ok": False,
            "mensaje": f"No fue posible recargar el catálogo: {error}"
        }), 503

    return jsonify({
        "ok": True,
        "total": len(productos),
        "mensaje": "Catálogo recargado correctamente."
    })
