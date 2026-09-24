import os

from flask import Blueprint, current_app, jsonify, redirect, request, send_file, session
from werkzeug.utils import secure_filename

from app.repos.pqr import RADICADO_RE, consultar_pqr, guardar_adjunto, obtener_adjunto
from app.seguridad import VENDEDOR, sesion_requerida
from app.servicios import almacenamiento

bp = Blueprint("evidencias", __name__)


# ==========================================================
# SUBIR EVIDENCIAS
# ==========================================================

EXTENSIONES_EVIDENCIA = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".mp4", ".mov", ".txt", ".csv",
}


def _puede_ver(radicado):
    """Un vendedor solo puede ver/subir evidencias de sus propios PQR."""
    if session.get("rol") != VENDEDOR:
        return True
    pqr = consultar_pqr(radicado)
    return bool(pqr) and str(pqr.get("usuario_id", "")) == str(session.get("usuario_id", ""))


@bp.route("/api/evidencias", methods=["POST"])
@sesion_requerida
def api_evidencias():

    radicado = (request.form.get("radicado") or "").strip()
    tipo = request.form.get("tipo", "")

    if not RADICADO_RE.fullmatch(radicado):
        return jsonify({
            "ok": False,
            "mensaje": "Radicado inválido."
        }), 400

    if not _puede_ver(radicado):
        return jsonify({
            "ok": False,
            "mensaje": "No tiene permisos para subir evidencias a este PQR."
        }), 403

    archivos = request.files.getlist("archivos")

    if not archivos:
        return jsonify({
            "ok": False,
            "mensaje": "No se recibieron archivos."
        }), 400

    for archivo in archivos:

        if archivo.filename == "":
            continue

        nombre = secure_filename(archivo.filename)
        extension = os.path.splitext(nombre)[1].lower()

        if not nombre or extension not in EXTENSIONES_EVIDENCIA:
            return jsonify({
                "ok": False,
                "mensaje": f"Tipo de archivo no permitido: {archivo.filename}"
            }), 400

        clave = f"{radicado}/{nombre}"
        try:
            almacenamiento.guardar(clave, archivo.read(), archivo.mimetype)
        except RuntimeError as error:
            current_app.logger.exception("Error al guardar evidencia %s", clave)
            return jsonify({
                "ok": False,
                "mensaje": f"No fue posible guardar el archivo {archivo.filename}: {error}"
            }), 502

        guardar_adjunto(
            radicado=radicado,
            tipo=tipo,
            archivo_original=nombre,
            ruta_archivo=clave,
            observacion="",
            usuario=session.get("nombre", "Cliente")
        )

    return jsonify({
        "ok": True,
        "mensaje": "Evidencias guardadas correctamente."
    })


# ==========================================================
# DESCARGAR EVIDENCIA
# ==========================================================

@bp.route("/api/evidencias/<int:id_adjunto>", methods=["GET"])
@sesion_requerida
def api_evidencia_descargar(id_adjunto):
    adjunto = obtener_adjunto(id_adjunto)
    if not adjunto:
        return jsonify({"ok": False, "mensaje": "Evidencia no encontrada."}), 404

    if not _puede_ver(adjunto["radicado"]):
        return jsonify({"ok": False, "mensaje": "No tiene permisos para ver esta evidencia."}), 403

    url = almacenamiento.url_descarga(adjunto["ruta_archivo"])
    if url:
        return redirect(url)

    ruta_local = os.path.join(current_app.config["UPLOAD_FOLDER"], adjunto["ruta_archivo"])
    if not os.path.isfile(ruta_local):
        return jsonify({"ok": False, "mensaje": "El archivo ya no está disponible."}), 404
    return send_file(ruta_local, download_name=adjunto["archivo_original"])
