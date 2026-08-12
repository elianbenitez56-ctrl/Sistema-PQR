from flask import Flask, render_template
from excel_db import crear_excel, actualizar_estructura_excel
from routes import routes
import os

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

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# =====================================================
# BASE DE DATOS
# =====================================================

crear_excel()
actualizar_estructura_excel()

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