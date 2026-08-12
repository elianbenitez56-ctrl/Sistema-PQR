from flask import Flask, render_template
from excel_db import crear_excel, actualizar_estructura_excel
from users_db import sembrar_usuarios
from routes import routes
import os
from datetime import timedelta

app = Flask(__name__)

# =====================================================
# CONFIGURACIÓN
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.config["UPLOAD_FOLDER"] = os.path.join(
    BASE_DIR,
    "Base_Datos",
    "Evidencias"
)

# Clave para firmar las sesiones (cookies).
# En Render debe configurarse siempre SECRET_KEY como variable de entorno.
app.secret_key = os.getenv("SECRET_KEY", "development-only-not-for-production")

# Duración máxima de la sesión (12 horas).
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# =====================================================
# BASE DE DATOS
# =====================================================

crear_excel()
actualizar_estructura_excel()
sembrar_usuarios()

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
