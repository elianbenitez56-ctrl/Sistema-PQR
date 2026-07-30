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
# PÁGINA PRINCIPAL
# =====================================================

@app.route("/")
def inicio():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)