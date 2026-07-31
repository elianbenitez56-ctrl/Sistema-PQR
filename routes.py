from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename

from excel_db import (
    guardar_pqr,
    consultar_pqr,
    guardar_investigacion,
    actualizar_estado_pqr,
    guardar_historial,
    obtener_dashboard,
    guardar_adjunto,
    generar_radicado,
    listar_pqrs
)

routes = Blueprint("routes", __name__)


# ==========================================================
# GUARDAR PQR
# ==========================================================

@routes.route("/api/pqr", methods=["POST"])
def api_guardar_pqr():

    datos = request.get_json()

    radicado = generar_radicado()
    datos["radicado"] = radicado

    guardar_pqr(datos)

    return jsonify({
        "ok": True,
        "radicado": radicado,
        "mensaje": "PQR guardado correctamente"
    })


# ==========================================================
# LISTAR TODOS LOS PQR
# ==========================================================

@routes.route("/api/pqr/todos", methods=["GET"])
def api_pqr_todos():

    return jsonify(listar_pqrs())


# ==========================================================
# CONSULTAR PQR
# ==========================================================

@routes.route("/api/consultar/<valor>", methods=["GET"])
def api_consultar(valor):

    pqr = consultar_pqr(valor)

    if pqr:
        return jsonify(pqr)

    return jsonify({
        "error": "PQR no encontrado"
    }), 404


# ==========================================================
# GUARDAR SEGUIMIENTO
# ==========================================================

@routes.route("/api/seguimiento", methods=["POST"])
def api_seguimiento():

    datos = request.get_json()

    guardar_investigacion(datos)

    return jsonify({
        "ok": True
    })


# ==========================================================
# CAMBIAR ESTADO
# ==========================================================

@routes.route("/api/cambiar_estado", methods=["POST"])
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
        "Sistema",
        "Estado actualizado"
    )

    return jsonify({
        "ok": True
    })


# ==========================================================
# DASHBOARD
# ==========================================================

@routes.route("/api/dashboard", methods=["GET"])
def api_dashboard():

    return jsonify(obtener_dashboard())

# ==========================================================
# SUBIR EVIDENCIAS
# ==========================================================

@routes.route("/api/evidencias", methods=["POST"])
def api_evidencias():

    radicado = request.form.get("radicado")
    tipo = request.form.get("tipo", "")

    if not radicado:
        return jsonify({
            "ok": False,
            "mensaje": "No se recibió el radicado."
        }), 400

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

        ruta = os.path.join(carpeta, nombre)

        archivo.save(ruta)

        guardar_adjunto(
            radicado=radicado,
            tipo=tipo,
            archivo_original=nombre,
            ruta_archivo=ruta,
            observacion="",
            usuario="Cliente"
        )

    return jsonify({
        "ok": True,
        "mensaje": "Evidencias guardadas correctamente."
    })