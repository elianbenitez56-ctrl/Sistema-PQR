import time
from collections import defaultdict

from flask import Blueprint, jsonify, request, session

from app.repos.usuarios import autenticar_usuario, obtener_usuario_por_id
from app.seguridad import VENDEDOR

bp = Blueprint("sesion", __name__)


def usuario_para_sesion(usuario):
    """Expone los datos necesarios para el formulario sin confiar en el navegador."""

    rol = str(usuario.get("rol", "") or "").strip().upper()

    return {
        "id": usuario.get("id"),
        "usuario": usuario.get("usuario", ""),
        "nombre": usuario.get("nombre", ""),
        "rol": usuario.get("rol", ""),
        "linea_producto": usuario.get("linea_producto", ""),
        "empresa": usuario.get("empresa", "INAPEL"),
        "documento": usuario.get("documento", ""),
        "correo": usuario.get("correo", ""),
        "telefono": usuario.get("telefono", ""),
        # El cargo se deriva del rol almacenado; no se fija en el frontend.
        "cargo": rol if rol == VENDEDOR else "",
        # TOROFIL permanece como línea de producto, no como empresa.
        "area": usuario.get("linea_producto", "") or ""
    }




# ==========================================================
# AUTENTICACIÓN
# ==========================================================

# ponytail: contador en memoria por worker; usar Redis/Flask-Limiter si se escala a varias instancias.
_FALLOS_LOGIN = defaultdict(list)
_MAX_FALLOS = 5
_VENTANA_SEG = 300


def _login_bloqueado(clave):
    ahora = time.monotonic()
    recientes = [t for t in _FALLOS_LOGIN[clave] if ahora - t < _VENTANA_SEG]
    _FALLOS_LOGIN[clave] = recientes
    return len(recientes) >= _MAX_FALLOS


@bp.route("/api/login", methods=["POST"])
def api_login():

    datos = request.get_json(silent=True) or request.form or {}

    usuario = str(datos.get("usuario", "")).strip()
    contrasena = str(datos.get("contrasena", ""))

    if not usuario or not contrasena:
        return jsonify({
            "ok": False,
            "mensaje": "Ingrese usuario y contraseña."
        }), 400

    clave_intentos = (request.remote_addr, usuario.lower())
    if _login_bloqueado(clave_intentos):
        return jsonify({
            "ok": False,
            "mensaje": "Demasiados intentos fallidos. Intente de nuevo en unos minutos."
        }), 429

    resultado = autenticar_usuario(usuario, contrasena)

    if "error" in resultado:
        _FALLOS_LOGIN[clave_intentos].append(time.monotonic())
        return jsonify({
            "ok": False,
            "mensaje": resultado["error"]
        }), 401

    _FALLOS_LOGIN.pop(clave_intentos, None)
    session.clear()
    session.permanent = True
    session["usuario_id"] = resultado["id"]
    session["usuario"] = resultado["usuario"]
    session["nombre"] = resultado["nombre"]
    session["rol"] = resultado["rol"]
    session["linea_producto"] = resultado["linea_producto"]
    session["empresa"] = resultado["empresa"]

    return jsonify({
        "ok": True,
        "usuario": usuario_para_sesion(resultado)
    })


@bp.route("/api/logout", methods=["POST"])
def api_logout():

    session.clear()

    return jsonify({"ok": True})


@bp.route("/api/sesion", methods=["GET"])
def api_sesion():

    if not session.get("usuario_id"):
        return jsonify({"ok": False}), 401

    usuario_actual = obtener_usuario_por_id(session["usuario_id"])

    if not usuario_actual or not usuario_actual.get("activo", True):
        session.clear()
        return jsonify({"ok": False}), 401

    return jsonify({
        "ok": True,
        "usuario": usuario_para_sesion(usuario_actual)
    })
