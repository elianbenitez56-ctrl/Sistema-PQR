import logging
import os
from datetime import timedelta

from flask import Flask, jsonify, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

from mysql_db import asegurar_tablas, get_db_cursor, sembrar_usuarios
from catalogo_productos import CATALOGO_PATH, cargar_catalogo
from routes import routes

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# =====================================================
# CONFIGURACIÓN
# =====================================================

DEBUG = os.getenv("FLASK_DEBUG") == "1"

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    if not DEBUG:
        raise RuntimeError("SECRET_KEY es obligatoria fuera de modo desarrollo.")
    secret_key = "solo-desarrollo"
app.secret_key = secret_key

app.config["UPLOAD_FOLDER"] = os.path.abspath(
    os.getenv("PQR_UPLOAD_DIR", os.path.join("Base_Datos", "Evidencias"))
)
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_MB", "25")) * 1024 * 1024
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "0" if DEBUG else "1") == "1"

if os.getenv("TRUST_PROXY") == "1":
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# =====================================================
# BASE DE DATOS MySQL
# =====================================================

asegurar_tablas()
sembrar_usuarios()

try:
    cargar_catalogo()
    print(f">>> CATÁLOGO DE PRODUCTOS CARGADO: {CATALOGO_PATH} <<<")
except Exception as error:
    # El resto del sistema puede iniciar aunque el catálogo requiera atención.
    print(f">>> CATÁLOGO DE PRODUCTOS NO DISPONIBLE: {error} <<<")

# =====================================================
# RUTAS
# =====================================================

app.register_blueprint(routes)

# =====================================================
# ANTI-CACHÉ: evita que el navegador muestre versiones viejas
# =====================================================

@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# =====================================================
# PÁGINA PRINCIPAL
# =====================================================

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
