import os
import json
import shutil
from datetime import datetime
from collections import Counter
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

print(">>> USANDO excel_db.py <<<")

ARCHIVO = "BaseDatos_PQR.xlsx"


# ==========================================================
# CREAR ARCHIVO Y HOJAS
# ==========================================================

def crear_excel():

    if os.path.exists(ARCHIVO):
        return

    wb = Workbook()

    # ---------------- PQR ----------------

    ws = wb.active
    ws.title = "PQR"

    ws.append([
        "Radicado",
        "Fecha",
        "Hora",
        "Tipo",
        "Cliente",
        "Nit",
        "Contacto",
        "Telefono",
        "Correo",
        "Estado",
        "Prioridad",
        "Descripcion",
        "Expectativa",
        "ProductosJSON",
        "Empresa",
        "Vendedor",
        "Linea",
        "UsuarioID",
        "CorreoConfirmacionEnviado",
        "DocumentoReceptor",
        "CorreoReceptor",
        "TelefonoReceptor",
        "CargoReceptor",
        "AreaReceptor",
        "CiudadRecepcion",
        "DepartamentoRecepcion",
        "MedioRecepcion",
        "OtroMedioRecepcion"
    ])

    # ---------------- Historial ----------------

    ws = wb.create_sheet("Historial")

    ws.append([
        "Radicado",
        "Estado",
        "Usuario",
        "Fecha",
        "Hora",
        "Observacion"
    ])

    # ---------------- Investigaciones ----------------

    ws = wb.create_sheet("Investigaciones")

    ws.append([
        "Radicado",
        "Responsable",
        "Cargo",
        "Herramienta",
        "Causa",
        "Accion",
        "Notificar",
        "FechaRespuesta",
        "FechaCierre",
        "Cierre",
        "Respuesta",
        "Departamentos"
    ])

    # ---------------- Adjuntos ----------------

    ws = wb.create_sheet("Adjuntos")

    ws.append([
        "Radicado",
        "Tipo",
        "Archivo",
        "Ruta",
        "Fecha",
        "Hora",
        "Usuario",
        "Observacion"
    ])

    wb.save(ARCHIVO)
    wb.close()


# ==========================================================
# VERIFICAR ESTRUCTURA
# ==========================================================

def actualizar_estructura_excel():

    if not os.path.exists(ARCHIVO):
        crear_excel()
        return

    wb = load_workbook(ARCHIVO)

    hojas = wb.sheetnames

    if "PQR" not in hojas:
        ws = wb.create_sheet("PQR")
        ws.append([
            "Radicado",
            "Fecha",
            "Hora",
            "Tipo",
            "Cliente",
            "Nit",
            "Contacto",
            "Telefono",
            "Correo",
            "Estado",
            "Prioridad",
            "Descripcion",
            "Expectativa",
            "ProductosJSON",
            "Empresa",
            "Vendedor",
            "Linea",
            "UsuarioID",
            "CorreoConfirmacionEnviado",
            "DocumentoReceptor",
            "CorreoReceptor",
            "TelefonoReceptor",
            "CargoReceptor",
            "AreaReceptor",
            "CiudadRecepcion",
            "DepartamentoRecepcion",
            "MedioRecepcion",
            "OtroMedioRecepcion"
        ])
    else:
        ws = wb["PQR"]
        if ws.max_column < 14:
            ws.cell(1, 14).value = "ProductosJSON"
        if ws.max_column < 15:
            ws.cell(1, 15).value = "Empresa"
        if ws.max_column < 16:
            ws.cell(1, 16).value = "Vendedor"
        if ws.max_column < 17:
            ws.cell(1, 17).value = "Linea"
        if ws.max_column < 18:
            ws.cell(1, 18).value = "UsuarioID"
        if ws.max_column < 19:
            ws.cell(1, 19).value = "CorreoConfirmacionEnviado"
        if ws.max_column < 20:
            ws.cell(1, 20).value = "DocumentoReceptor"
        if ws.max_column < 21:
            ws.cell(1, 21).value = "CorreoReceptor"
        if ws.max_column < 22:
            ws.cell(1, 22).value = "TelefonoReceptor"
        if ws.max_column < 23:
            ws.cell(1, 23).value = "CargoReceptor"
        if ws.max_column < 24:
            ws.cell(1, 24).value = "AreaReceptor"
        if ws.max_column < 25:
            ws.cell(1, 25).value = "CiudadRecepcion"
        if ws.max_column < 26:
            ws.cell(1, 26).value = "DepartamentoRecepcion"
        if ws.max_column < 27:
            ws.cell(1, 27).value = "MedioRecepcion"
        if ws.max_column < 28:
            ws.cell(1, 28).value = "OtroMedioRecepcion"

    if "Historial" not in hojas:
        ws = wb.create_sheet("Historial")
        ws.append([
            "Radicado",
            "Estado",
            "Usuario",
            "Fecha",
            "Hora",
            "Observacion"
        ])

    if "Investigaciones" not in hojas:
        ws = wb.create_sheet("Investigaciones")
        ws.append([
            "Radicado",
            "Responsable",
            "Cargo",
            "Herramienta",
            "Causa",
            "Accion",
            "Notificar",
            "FechaRespuesta",
            "FechaCierre",
            "Cierre",
            "Respuesta",
            "Departamentos"
        ])

    if "Adjuntos" not in hojas:
        ws = wb.create_sheet("Adjuntos")
        ws.append([
            "Radicado",
            "Tipo",
            "Archivo",
            "Ruta",
            "Fecha",
            "Hora",
            "Usuario",
            "Observacion"
        ])
    wb.save(ARCHIVO)
    wb.close()


# ==========================================================
# RADICADO
# ==========================================================

def generar_radicado():

    actualizar_estructura_excel()

    wb = load_workbook(ARCHIVO)

    ws = wb["PQR"]

    fila = ws.max_row

    if fila <= 1:
        consecutivo = 1

    else:

        ultimo = ws.cell(row=fila, column=1).value

        try:

            consecutivo = int(str(ultimo).split("-")[-1]) + 1

        except:

            consecutivo = fila

    wb.close()

    return f"PQR-{datetime.now().year}-{consecutivo:04d}"


# ==========================================================
# HISTORIAL
# ==========================================================

def guardar_historial(
    radicado,
    estado,
    usuario="Sistema",
    observacion=""
):

    wb = load_workbook(ARCHIVO)

    ws = wb["Historial"]

    ahora = datetime.now()

    ws.append([
        radicado,
        estado,
        usuario,
        ahora.strftime("%Y-%m-%d"),
        ahora.strftime("%H:%M:%S"),
        observacion
    ])

    wb.save(ARCHIVO)
    wb.close()


# ==========================================================
# GUARDAR PQR
# ==========================================================

def guardar_pqr(datos):

    actualizar_estructura_excel()

    wb = load_workbook(ARCHIVO)

    ws = wb["PQR"]

    productos_json = json.dumps(datos.get("productos", []), ensure_ascii=False)

    ws.append([

        datos.get("radicado",""),
        datos.get("fechaRec",""),
        datos.get("horaRec",""),
        datos.get("tipoSol",""),
        datos.get("cliente",""),
        datos.get("nit",""),
        datos.get("contacto",""),
        datos.get("tel",""),
        datos.get("email",""),
        datos.get("estado","Recibido"),
        datos.get("prioridad",""),
        datos.get("desc",""),
        datos.get("expectativa",""),
        productos_json,
        datos.get("empresa","INAPEL"),
        datos.get("vendedor",""),
        datos.get("linea",""),
        datos.get("usuario_id",""),
        "NO",
        datos.get("documento_receptor", ""),
        datos.get("correo_receptor", ""),
        datos.get("telefono_receptor", ""),
        datos.get("cargo_receptor", ""),
        datos.get("area_receptor", ""),
        datos.get("ciudadRec", ""),
        datos.get("dptoRec", ""),
        datos.get("medio", ""),
        datos.get("otroMedio", "")

    ])

    wb.save(ARCHIVO)
    wb.close()

    guardar_historial(

        datos["radicado"],
        datos.get("estado","Recibido"),
        "Sistema",
        "PQR registrado"

    )

    return True


# ==========================================================
# CORREO DE CONFIRMACIÓN
# ==========================================================

def correo_confirmacion_enviado(radicado):
    """Devuelve True si el correo de confirmación ya fue enviado para el radicado."""

    wb = load_workbook(ARCHIVO)
    ws = wb["PQR"]

    for fila in ws.iter_rows(min_row=2):
        if fila[0].value is not None and str(fila[0].value).strip() == str(radicado).strip():
            valor = fila[18].value if len(fila) > 18 else None
            wb.close()
            return str(valor or "").strip().upper() == "SI"

    wb.close()
    return False


def marcar_correo_confirmacion(radicado, enviado):
    """Actualiza la columna CorreoConfirmacionEnviado (SI/NO) del radicado."""

    wb = load_workbook(ARCHIVO)
    ws = wb["PQR"]

    for fila in ws.iter_rows(min_row=2):
        if fila[0].value is not None and str(fila[0].value).strip() == str(radicado).strip():
            fila[18].value = "SI" if enviado else "NO"
            break

    wb.save(ARCHIVO)
    wb.close()

# ==========================================================
# CONSULTAR PQR
# ==========================================================

def consultar_pqr(valor_busqueda):

    actualizar_estructura_excel()
    wb = load_workbook(ARCHIVO)

    ws = wb["PQR"]
    ws_inv = wb["Investigaciones"]
    ws_hist = wb["Historial"]

    valor_busqueda = str(valor_busqueda).strip().upper()

    for fila in ws.iter_rows(min_row=2, values_only=True):

        radicado = str(fila[0]).strip().upper()
        cliente = str(fila[4]).strip().upper()
        nit = str(fila[5]).strip().upper()

        if valor_busqueda in (radicado, cliente, nit):

            investigacion = {}

            for inv in ws_inv.iter_rows(min_row=2, values_only=True):
                if str(inv[0]).strip().upper() == radicado:
                    investigacion = {
                        "resp": inv[1] or "",
                        "cargo": inv[2] or "",
                        "herr": inv[3] or "",
                        "causa": inv[4] or "",
                        "acc": inv[5] or "",
                        "notif": inv[6] or "",
                        "fResp": inv[7] or "",
                        "fCierre": inv[8] or "",
                        "cierre": inv[9] or "",
                        "respTxt": inv[10] or "",
                        "deptos": inv[11] or "" if len(inv) > 11 else ""
                    }
                    break

            historial = []
            for h in ws_hist.iter_rows(min_row=2, values_only=True):
                if str(h[0]).strip().upper() == radicado:
                    historial.append({
                        "estado": h[1],
                        "fecha": str(h[3]),
                        "hora": str(h[4]),
                        "usuario": str(h[2])
                    })

            productos_raw = fila[13] if len(fila) > 13 and fila[13] else "[]"
            try:
                productos = json.loads(productos_raw)
            except:
                productos = []

            wb.close()
            return {
                "radicado": fila[0],
                "fechaRec": str(fila[1]),
                "horaRec": fila[2],
                "tipoSol": fila[3],
                "cliente": fila[4],
                "nit": fila[5],
                "contacto": fila[6],
                "tel": fila[7],
                "email": fila[8],
                "estado": fila[9],
                "prioridad": fila[10],
                "desc": fila[11],
                "expectativa": fila[12] if len(fila) > 12 else "",
                "productos": productos,
                "empresa": fila[14] if len(fila) > 14 and fila[14] else "",
                "vendedor": fila[15] if len(fila) > 15 and fila[15] else "",
                "linea": fila[16] if len(fila) > 16 and fila[16] else "",
                "usuario_id": fila[17] if len(fila) > 17 and fila[17] else "",
                "documento_receptor": fila[19] if len(fila) > 19 and fila[19] else "",
                "correo_receptor": fila[20] if len(fila) > 20 and fila[20] else "",
                "telefono_receptor": fila[21] if len(fila) > 21 and fila[21] else "",
                "cargo_receptor": fila[22] if len(fila) > 22 and fila[22] else "",
                "area_receptor": fila[23] if len(fila) > 23 and fila[23] else "",
                "ciudad_recepcion": fila[24] if len(fila) > 24 and fila[24] else "",
                "departamento_recepcion": fila[25] if len(fila) > 25 and fila[25] else "",
                "medio_recepcion": fila[26] if len(fila) > 26 and fila[26] else "",
                "otro_medio_recepcion": fila[27] if len(fila) > 27 and fila[27] else "",
                "investigacion": investigacion,
                "historial": historial,
                "savedAt": f"{fila[1]}T{fila[2]}"
            }

    wb.close()
    return None

# ==========================================================
# LISTAR TODOS LOS PQR (misma fuente que obtener_dashboard)
# ==========================================================

def listar_pqrs():

    actualizar_estructura_excel()
    wb = load_workbook(ARCHIVO)

    ws = wb["PQR"]

    lista = []

    for fila in ws.iter_rows(min_row=2, values_only=True):

        if not fila[0]:
            continue

        fecha = str(fila[1])[:10] if fila[1] else ""
        hora = fila[2] or ""

        productos_raw = fila[13] if len(fila) > 13 and fila[13] else "[]"

        try:
            productos = json.loads(productos_raw)
        except:
            productos = []

        lista.append({
            "radicado": fila[0],
            "fechaRec": fecha,
            "horaRec": hora,
            "tipoSol": fila[3] or "",
            "cliente": fila[4] or "",
            "nit": fila[5] or "",
            "contacto": fila[6] or "",
            "tel": fila[7] or "",
            "email": fila[8] or "",
            "estado": fila[9] or "Recibido",
            "prioridad": fila[10] or "",
            "desc": fila[11] or "",
            "expectativa": fila[12] if len(fila) > 12 else "",
            "productos": productos,
            "empresa": fila[14] if len(fila) > 14 and fila[14] else "",
            "vendedor": fila[15] if len(fila) > 15 and fila[15] else "",
            "linea": fila[16] if len(fila) > 16 and fila[16] else "",
            "usuario_id": fila[17] if len(fila) > 17 and fila[17] else "",
            "documento_receptor": fila[19] if len(fila) > 19 and fila[19] else "",
            "correo_receptor": fila[20] if len(fila) > 20 and fila[20] else "",
            "telefono_receptor": fila[21] if len(fila) > 21 and fila[21] else "",
            "cargo_receptor": fila[22] if len(fila) > 22 and fila[22] else "",
            "area_receptor": fila[23] if len(fila) > 23 and fila[23] else "",
            "ciudad_recepcion": fila[24] if len(fila) > 24 and fila[24] else "",
            "departamento_recepcion": fila[25] if len(fila) > 25 and fila[25] else "",
            "medio_recepcion": fila[26] if len(fila) > 26 and fila[26] else "",
            "otro_medio_recepcion": fila[27] if len(fila) > 27 and fila[27] else "",
            "savedAt": f"{fecha}T{hora}" if hora else fecha
        })

    wb.close()
    return lista

# ==========================================================
# ACTUALIZAR ESTADO DEL PQR
# ==========================================================

def actualizar_estado_pqr(radicado, estado):

    actualizar_estructura_excel()

    wb = load_workbook(ARCHIVO)

    ws = wb["PQR"]

    for fila in ws.iter_rows(min_row=2):

        if str(fila[0].value).strip() == radicado:

            fila[9].value = estado
            break

    wb.save(ARCHIVO)
    wb.close()

    return True


# ==========================================================
# GUARDAR / ACTUALIZAR INVESTIGACIÓN
# ==========================================================

def guardar_investigacion(datos):

    actualizar_estructura_excel()

    wb = load_workbook(ARCHIVO)

    ws = wb["Investigaciones"]

    fila_existente = None

    # Buscar si ya existe el radicado

    for fila in range(2, ws.max_row + 1):

        if str(ws.cell(fila, 1).value).strip() == str(datos["radicado"]).strip():

            fila_existente = fila
            break

    # Si existe, actualiza

    if fila_existente:

        ws.cell(fila_existente,1).value = datos.get("radicado","")
        ws.cell(fila_existente,2).value = datos.get("resp","")
        ws.cell(fila_existente,3).value = datos.get("cargo","")
        ws.cell(fila_existente,4).value = datos.get("herr","")
        ws.cell(fila_existente,5).value = datos.get("causa","")
        ws.cell(fila_existente,6).value = datos.get("acc","")
        ws.cell(fila_existente,7).value = datos.get("notif","")
        ws.cell(fila_existente,8).value = datos.get("fResp","")
        ws.cell(fila_existente,9).value = datos.get("fCierre","")
        ws.cell(fila_existente,10).value = datos.get("cierre","")
        ws.cell(fila_existente,11).value = datos.get("respTxt","")
        ws.cell(fila_existente,12).value = datos.get("deptos","")

    else:

        ws.append([

            datos.get("radicado",""),
            datos.get("resp",""),
            datos.get("cargo",""),
            datos.get("herr",""),
            datos.get("causa",""),
            datos.get("acc",""),
            datos.get("notif",""),
            datos.get("fResp",""),
            datos.get("fCierre",""),
            datos.get("cierre",""),
            datos.get("respTxt",""),
            datos.get("deptos","")

        ])

    wb.save(ARCHIVO)
    wb.close()

    # ==============================
    # Estado automático
    # ==============================

    estado = "En investigación"

    if datos.get("cierre") == "Sí":

        estado = "Cerrado"

    actualizar_estado_pqr(

        datos["radicado"],
        estado

    )

    guardar_historial(

        datos["radicado"],
        estado,
        "Sistema",
        "Seguimiento actualizado"

    )

    return True

# ==========================================================
# INICIALIZAR ESTRUCTURA
# ==========================================================

def inicializar_excel():
    """
    Crea el archivo y las hojas necesarias si no existen.
    Puede llamarse al iniciar la aplicación.
    """
    actualizar_estructura_excel()

    wb = load_workbook(ARCHIVO)

    hojas_requeridas = {
        "PQR": [
            "Radicado", "Fecha", "Hora", "Tipo", "Cliente", "Nit",
            "Contacto", "Telefono", "Correo", "Estado",
            "Prioridad", "Descripcion", "Expectativa", "ProductosJSON",
            "Empresa", "Vendedor", "Linea", "UsuarioID",
            "CorreoConfirmacionEnviado", "DocumentoReceptor",
            "CorreoReceptor", "TelefonoReceptor", "CargoReceptor",
            "AreaReceptor", "CiudadRecepcion", "DepartamentoRecepcion",
            "MedioRecepcion", "OtroMedioRecepcion"
        ],
        "Historial": [
            "Radicado", "Estado", "Usuario",
            "Fecha", "Hora", "Observacion"
        ],
        "Investigaciones": [
            "Radicado", "Responsable", "Cargo",
            "Herramienta", "Causa", "Accion",
            "Notificar", "FechaRespuesta",
            "FechaCierre", "Cierre", "Respuesta",
            "Departamentos"
        ],
        "Adjuntos": [
            "Radicado", "Tipo", "Archivo",
            "Ruta", "Fecha", "Hora",
            "Usuario", "Observacion"
        ]
    }

    for hoja, encabezados in hojas_requeridas.items():

        if hoja not in wb.sheetnames:
            ws = wb.create_sheet(hoja)
            ws.append(encabezados)

    wb.save(ARCHIVO)
    wb.close()


def obtener_dashboard():

    actualizar_estructura_excel()

    wb = load_workbook(ARCHIVO)

    ws = wb["PQR"]

    estados = Counter()
    tipos = Counter()
    prioridades = Counter()

    total = 0

    for fila in ws.iter_rows(min_row=2, values_only=True):

        total += 1

        estado = fila[9] or "Sin estado"
        tipo = fila[3] or "Sin tipo"
        prioridad = fila[10] or "Sin prioridad"

        estados[estado] += 1
        tipos[tipo] += 1
        prioridades[prioridad] += 1

    wb.close()

    return {
        "total": total,
        "estados": dict(estados),
        "tipos": dict(tipos),
        "prioridades": dict(prioridades)
    }
# ==========================================================
# GUARDAR ADJUNTO
# ==========================================================

def guardar_adjunto(
    radicado,
    tipo,
    archivo_original,
    ruta_archivo,
    observacion="",
    usuario="Cliente"
):

    actualizar_estructura_excel()

    wb = load_workbook(ARCHIVO)

    ws = wb["Adjuntos"]

    ahora = datetime.now()

    fila = ws.max_row + 1

    # Radicado
    ws.cell(fila, 1).value = radicado

    # Tipo
    ws.cell(fila, 2).value = tipo

    # Archivo original
    ws.cell(fila, 3).value = archivo_original

    # Hipervínculo
    celda = ws.cell(fila, 4)
    celda.value = "📎 Abrir evidencia"
    celda.hyperlink = ruta_archivo
    celda.font = Font(underline="single", color="0000FF")

    # Fecha
    ws.cell(fila, 5).value = ahora.strftime("%Y-%m-%d")

    # Hora
    ws.cell(fila, 6).value = ahora.strftime("%H:%M:%S")

    # Usuario
    ws.cell(fila, 7).value = usuario

    # Observacion
    ws.cell(fila, 8).value = observacion

    wb.save(ARCHIVO)
    wb.close()

    return True

# ==========================================================
# ELIMINAR PQR
# ==========================================================

def eliminar_pqr(radicado):

    actualizar_estructura_excel()

    wb = load_workbook(ARCHIVO)

    ws = wb["PQR"]

    encontrado = False

    for fila in range(2, ws.max_row + 1):

        if str(ws.cell(fila, 1).value).strip().upper() == str(radicado).strip().upper():

            ws.delete_rows(fila)
            encontrado = True
            break

    if not encontrado:

        wb.close()
        return "not_found"

    for hoja in ["Historial", "Investigaciones", "Adjuntos"]:

        if hoja not in wb.sheetnames:
            continue

        ws_h = wb[hoja]

        filas_a_eliminar = []

        for fila in range(2, ws_h.max_row + 1):

            if str(ws_h.cell(fila, 1).value).strip().upper() == str(radicado).strip().upper():
                filas_a_eliminar.append(fila)

        for fila in reversed(filas_a_eliminar):
            ws_h.delete_rows(fila)

    try:

        wb.save(ARCHIVO)
        wb.close()

    except Exception:

        return "save_error"

    carpeta = os.path.join("Base_Datos", "Evidencias", str(radicado))

    if os.path.isdir(carpeta):
        shutil.rmtree(carpeta, ignore_errors=True)

    return True
