import os

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.utils import secure_filename

from app.repos.pqr import RADICADO_RE, consultar_pqr, guardar_adjunto
from app.seguridad import VENDEDOR, sesion_requerida

bp = Blueprint("evidencias", __name__)


# ==========================================================
# SUBIR EVIDENCIAS
# ==========================================================

EXTENSIONES_EVIDENCIA = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".mp4", ".mov", ".txt", ".csv",
}


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

    # Un vendedor solo puede subir evidencias a sus propios PQR.
    if session.get("rol") == VENDEDOR:
        pqr = consultar_pqr(radicado)
        if not pqr or str(pqr.get("usuario_id", "")) != str(session.get("usuario_id", "")):
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

    carpeta = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        radicado
    )

    os.makedirs(carpeta, exist_ok=True)

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

        ruta = os.path.join(carpeta, nombre)

        archivo.save(ruta)

        guardar_adjunto(
            radicado=radicado,
            tipo=tipo,
            archivo_original=nombre,
            ruta_archivo=ruta,
            observacion="",
            usuario=session.get("nombre", "Cliente")
        )

    return jsonify({
        "ok": True,
        "mensaje": "Evidencias guardadas correctamente."
    })
