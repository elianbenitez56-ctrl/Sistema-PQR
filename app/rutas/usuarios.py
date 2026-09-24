from flask import Blueprint, jsonify, request, session

from app.repos.usuarios import listar_usuarios
from app.seguridad import ADMIN, LIDER_CALIDAD, rol_requerido
from app.servicios import usuarios as servicio

bp = Blueprint("usuarios", __name__)

# ADMIN: gestión completa. LIDER_CALIDAD: listar, crear y cambiar credenciales.


def _cuerpo():
    return request.get_json(silent=True) or request.form or {}


@bp.route("/api/usuarios", methods=["GET"])
@rol_requerido(ADMIN, LIDER_CALIDAD)
def api_usuarios_listar():
    return jsonify({"ok": True, "usuarios": listar_usuarios()})


@bp.route("/api/usuarios", methods=["POST"])
@rol_requerido(ADMIN, LIDER_CALIDAD)
def api_usuarios_crear():
    return jsonify(servicio.crear(_cuerpo(), session.get("rol"))), 201


@bp.route("/api/usuarios/<int:uid>", methods=["PUT"])
@rol_requerido(ADMIN)
def api_usuarios_actualizar(uid):
    return jsonify(servicio.actualizar(uid, _cuerpo()))


@bp.route("/api/usuarios/<int:uid>", methods=["DELETE"])
@rol_requerido(ADMIN)
def api_usuarios_eliminar(uid):
    return jsonify(servicio.eliminar(uid, session.get("usuario_id")))


@bp.route("/api/usuarios/<int:uid>/credenciales", methods=["PUT"])
@rol_requerido(ADMIN, LIDER_CALIDAD)
def api_usuarios_credenciales(uid):
    return jsonify(servicio.cambiar_credenciales(uid, _cuerpo(), session.get("rol")))
