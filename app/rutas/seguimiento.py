from flask import Blueprint, jsonify, request, session

from app.seguridad import ADMIN, LIDER_CALIDAD, ROLES_COMERCIAL, ROLES_SEGUIMIENTO, rol_requerido
from app.servicios.seguimiento import guardar_seguimiento

bp = Blueprint("seguimiento", __name__)


def _guardar(seccion):
    return jsonify(guardar_seguimiento(request.get_json() or {}, seccion, session.get("rol"), request.host_url))


@bp.route("/api/seguimiento/calidad", methods=["POST"])
@rol_requerido(ADMIN, LIDER_CALIDAD)
def api_seguimiento_calidad():
    return _guardar("calidad")


@bp.route("/api/seguimiento/comercial", methods=["POST"])
@rol_requerido(ADMIN, *ROLES_COMERCIAL)
def api_seguimiento_comercial():
    return _guardar("comercial")


# Compatibilidad con clientes anteriores que todavía usan el endpoint general.
@bp.route("/api/seguimiento", methods=["POST"])
@rol_requerido(*ROLES_SEGUIMIENTO)
def api_seguimiento():
    return _guardar(None)
