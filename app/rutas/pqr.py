from flask import Blueprint, jsonify, render_template, request, session

from app.errores import ErrorNegocio
from app.repos.pqr import listar_pqrs, obtener_dashboard
from app.seguridad import ROLES_INVESTIGACION, ROLES_VER_TODO, rol_requerido, sesion_requerida
from app.servicios import pqr as servicio

bp = Blueprint("pqr", __name__)


@bp.route("/consulta-pqr/<radicado>", methods=["GET"])
def consulta_publica(radicado):
    """Página pública (sin sesión) que abre el botón del correo de confirmación."""
    token = request.args.get("token", "")
    try:
        pqr = servicio.consultar_publico(radicado, token)
        return render_template("consulta_publica.html", pqr=pqr, error=None)
    except ErrorNegocio as e:
        return render_template("consulta_publica.html", pqr=None, error=e.mensaje), e.status


@bp.route("/api/pqr", methods=["POST"])
@sesion_requerida
def api_guardar_pqr():
    return jsonify(servicio.registrar_pqr(request.get_json(), session["usuario_id"]))


@bp.route("/api/pqr/todos", methods=["GET"])
@rol_requerido(*ROLES_VER_TODO)
def api_pqr_todos():
    return jsonify(listar_pqrs())


@bp.route("/api/pqr/<radicado>", methods=["DELETE"])
@rol_requerido(*ROLES_INVESTIGACION)
def api_eliminar_pqr(radicado):
    servicio.eliminar(radicado)
    return jsonify({"ok": True, "mensaje": "Registro eliminado correctamente."})


@bp.route("/api/consultar/<valor>", methods=["GET"])
@sesion_requerida
def api_consultar(valor):
    return jsonify(servicio.consultar(valor, session.get("rol"), session.get("usuario_id")))


@bp.route("/api/cambiar_estado", methods=["POST"])
@rol_requerido(*ROLES_INVESTIGACION)
def api_estado():
    servicio.cambiar_estado(request.get_json(), session.get("nombre"))
    return jsonify({"ok": True})


@bp.route("/api/dashboard", methods=["GET"])
@rol_requerido(*ROLES_VER_TODO)
def api_dashboard():
    return jsonify(obtener_dashboard())
