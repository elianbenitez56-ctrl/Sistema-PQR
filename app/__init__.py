import logging
import os

from flask import Flask, jsonify, render_template, request, session
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import Config
from app.errores import ErrorNegocio


def create_app():
    logging.basicConfig(level=logging.INFO)

    app = Flask(__name__)
    app.config.from_object(Config)

    if app.config["TRUST_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    from app.db import asegurar_tablas, get_db_cursor
    from app.repos.usuarios import sembrar_usuarios
    from app.rutas import blueprints
    from app.servicios import catalogo

    asegurar_tablas()
    sembrar_usuarios()

    try:
        catalogo.cargar_catalogo()
        app.logger.info("Catálogo de productos cargado: %s", catalogo.CATALOGO_PATH)
    except Exception as error:
        # El sistema puede iniciar aunque el catálogo requiera atención.
        app.logger.warning("Catálogo de productos no disponible: %s", error)

    for bp in blueprints:
        app.register_blueprint(bp)

    @app.errorhandler(ErrorNegocio)
    def error_de_negocio(error):
        if error.cerrar_sesion:
            session.clear()
        return jsonify(error.cuerpo()), error.status

    @app.errorhandler(Exception)
    def error_inesperado(error):
        # Sin esto, un error no previsto en /api/* devuelve la página HTML de
        # error de Flask y el fetch() del frontend revienta al hacer .json().
        if isinstance(error, HTTPException):
            return error
        if request.path.startswith("/api/"):
            app.logger.exception("Error no controlado en %s", request.path)
            return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500
        raise error

    @app.after_request
    def no_cache(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.route("/")
    def inicio():
        return render_template("index.html")

    @app.route("/healthz")
    def healthz():
        try:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return jsonify({"ok": False}), 503
        return jsonify({"ok": True})

    return app
