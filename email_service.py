"""
Servicio de correo electrónico — Sistema PQR INAPEL.

Envía la confirmación de recepción de PQR al cliente.

Usa una API HTTPS en lugar de SMTP. Las credencialas se leen exclusivamente
de variables de entorno del sistema. Nunca se escribe una contraseña en el
código ni se expone en JSON/logs.

Variables de entorno obligatorias:
    EMAIL_API_URL: Endpoint HTTPS del servicio de correo (ej:
                   https://api.email-service.com/v1/send)
    EMAIL_API_KEY:  Clave de autorización para el servicio de correo

Variables de entorno opcionales:
    EMAIL_USE_TLS:  "1"/"true" para modo TLS (predeterminado: true)
    PQR_URL_BASE  -> URL pública del sistema para el enlace de consulta

También soporta un archivo .env local (solo desarrollo; está en .gitignore).

Nunca se escribe una contraseña en el código ni se expone en JSON/logs.
"""

import os
import re
import sys
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from html import escape
from urllib.parse import quote

import smtplib

NOMBRE_SISTEMA = "INAPEL · Industria Nacional Papelera S.A.S."

EMAIL_REGEX = r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"


def _leer_env_local():
    """Carga variables de un archivo .env local si existe (solo desarrollo)."""

    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

    if not os.path.exists(ruta):
        return

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith("#") or "=" not in linea:
                    continue
                clave, valor = linea.split("=", 1)
                clave = clave.strip()
                valor = valor.strip().strip('"').strip("'")
                os.environ.setdefault(clave, valor)
    except Exception as e:
        print(f"[correo] No fue posible leer .env: {e}")


_leer_env_local()


def _var(nombre, defecto=None):
    return os.environ.get(nombre, defecto)


def _convertir_a_bool(valor):
    """Convierte un valor de entorno a boolean de forma segura.

    true / 1 / yes / si / sí → True
    false / 0 / no → False
    """
    if valor is None:
        return False
    valor_lower = valor.strip().lower()
    return valor_lower in ("true", "1", "yes", "sí", "si")


def _correo_valido(correo):
    return bool(correo) and re.match(EMAIL_REGEX, correo.strip()) is not None


def smtp_configurado():
    """Indica si existen las variables obligatorias para SMTP."""
    requeridos = ["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"]
    faltantes = [nombre for nombre in requeridos if not _var(nombre, "")]
    return len(faltantes) == 0


def variables_smtp_faltantes():
    """Devuelve la lista de variables SMTP obligatorias que están vacías."""
    requeridos = ["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"]
    faltantes = [nombre for nombre in requeridos if not _var(nombre, "")]
    return faltantes

def variables_api_faltantes():
    """Devuelve la lista de variables API obligatorias que están vacías."""

    faltantes = []
    for nombre in ("EMAIL_API_URL", "EMAIL_API_KEY"):
        if not _var(nombre, ""):
            faltantes.append(nombre)
    return faltantes


def _enviar_smtp(destinatarios, mensaje):
    """
    Envía un correo usando SMTP.

    Acepta destinatario individual o lista.
    Retorna (True, "") si fue exitoso, o (False, motivo) si falló.
    Nunca lanza excepciones.

    - Utiliza SMTP_USER para autenticación
    - Utiliza SMTP_PASSWORD para autenticación
    - Utiliza SMTP_FROM como remitente (o SMTP_USER por defecto)
    - Usa SMTP_HOST y SMTP_PORT
    - Interpreta SMTP_USE_TLS y SMTP_USE_SSL correctamente
    - Timeout de 20 segundos
    - Cierra la conexión correctamente aunque exista un error
    """
    host = _var("SMTP_HOST", "").strip()
    try:
        puerto = int(_var("SMTP_PORT", "587"))
    except (ValueError, TypeError):
        puerto = 587

    usuario = _var("SMTP_USER", "").strip()
    password = _var("SMTP_PASSWORD", "").strip()
    remitente = _var("SMTP_FROM", usuario).strip()
    usar_tls = _convertir_a_bool(_var("SMTP_USE_TLS", "true"))
    usar_ssl = _convertir_a_bool(_var("SMTP_USE_SSL", "false"))

    if not host or not usuario or not password:
        return False, "variables_smtp_faltantes"

    servidor = None
    try:
        if usar_ssl:
            servidor = smtplib.SMTP_SSL(host, puerto, timeout=20)
        else:
            servidor = smtplib.SMTP(host, puerto, timeout=20)
            servidor.ehlo()
            if usar_tls:
                servidor.starttls()
                servidor.ehlo()

        servidor.login(usuario, password)

        if not remitente:
            remitente = usuario

        servidor.sendmail(remitente, destinatarios, mensaje.as_string())
        return True, ""
    except Exception:
        return False, "Error de envío SMTP"
    finally:
        if servidor is not None:
            try:
                servidor.quit()
            except Exception:
                pass


def enviar_confirmacion_pqr(radicado, correo_cliente, datos):
    """
    Envía el correo de confirmación de PQR al cliente.

    Retorna (True, "") si se envió, o (False, motivo) si no.
    Nunca lanza excepciones: cualquier error se registra en logs
    y se devuelve como (False, motivo) para no bloquear la PQR.
    """

    if not smtp_configurado():
        faltan = ", ".join(variables_smtp_faltantes())
        print(
            f"[correo] SMTP no configurado: faltan las variables {faltan}. "
            "El correo de confirmación NO se envió."
        )
        return False, f"SMTP no configurado (faltan las variables: {faltan})."

    if not _correo_valido(correo_cliente):
        return False, "El correo del cliente no es válido."

    asunto = f"Confirmación de PQR - {radicado}"

    html = _plantilla_html(radicado, correo_cliente.strip(), datos)

    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = _var("SMTP_FROM", _var("SMTP_USER", "")).strip()
    mensaje["To"] = correo_cliente.strip()
    mensaje.attach(MIMEText(html, "html", "utf-8"))

    ok, motivo = _enviar_smtp([correo_cliente.strip()], mensaje)

    if ok:
        print(
            f"[correo] Confirmación enviada para {radicado} -> {correo_cliente}"
        )
    else:
        print(
            f"[correo] No fue posible enviar confirmación para {radicado}: {motivo}"
        )

    return ok, motivo


# ==========================================================
# NOTIFICACIÓN COMERCIAL
# ==========================================================

def enviar_notificacion_comercial(
    radicado,
    datos,
    destinatarios,
    campos_pendientes,
    url_base=None
):
    """Notifica a Comercial usando SMTP."""

    if not smtp_configurado():
        faltan = ", ".join(variables_smtp_faltantes())
        mensaje = f"SMTP no configurado (faltan las variables: {faltan})."
        print(f"[correo] Notificación comercial NO enviada: {mensaje}")
        return False, mensaje

    correos = []
    vistos = set()
    for correo in destinatarios or []:
        correo = str(correo or "").strip()
        if _correo_valido(correo) and correo.lower() not in vistos:
            correos.append(correo)
            vistos.add(correo.lower())

    if not correos:
        return False, "No hay destinatarios comerciales activos con correo válido."

    base = (_var("PQR_URL_BASE", "") or str(url_base or "")).strip().rstrip("/")
    enlace = ""
    if base:
        separador = "&" if "?" in base else "?"
        enlace = f"{base}{separador}seguimiento={quote(str(radicado))}"

    asunto = f"PQR {radicado} pendiente de gestión comercial"
    html = _plantilla_notificacion_comercial(
        radicado,
        datos,
        campos_pendientes,
        enlace
    )

    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = _var("SMTP_FROM", _var("SMTP_USER", "")).strip()
    mensaje["To"] = ", ".join(correos)
    mensaje.attach(MIMEText(html, "html", "utf-8"))

    ok, motivo = _enviar_smtp(correos, mensaje)

    if ok:
        print(
            f"[correo] Notificación comercial enviada para {radicado} -> "
            f"{len(correos)} destinatarios"
        )
    else:
        print(
            f"[correo] No fue posible enviar notificación comercial para "
            f"{radicado}: {motivo}"
        )

    return ok, motivo


def _plantilla_notificacion_comercial(radicado, datos, campos_pendientes, enlace):
    cliente = escape(str(datos.get("cliente", "") or "").strip() or "No informado")
    tipo = escape(str(datos.get("tipoSol", "") or "").strip() or "PQR")
    fecha = escape(str(datos.get("fechaRec", "") or "").strip() or "No informada")
    radicado_html = escape(str(radicado))
    pendientes_html = "".join(
        f"<li style=\"margin-bottom:5px\">{escape(str(campo))}</li>"
        for campo in campos_pendientes or []
    )
    enlace_html = (
        f'<p style="margin:20px 0"><a href="{escape(enlace, quote=True)}" '
        'style="background:#00325e;color:#ffffff;text-decoration:none;padding:10px 18px;'
        'border-radius:6px;display:inline-block;font-weight:bold">Abrir seguimiento del PQR</a></p>'
        if enlace else
        '<p style="margin:20px 0;color:#555555">Ingrese al aplicativo y busque el radicado '
        f"<strong>{radicado_html}</strong> en la sección Seguimiento.</p>"
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background-color:#f0f4f8;font-family:Arial,Helvetica,sans-serif">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f4f8;padding:24px 12px">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border:1px solid #dde5ee;border-radius:10px;overflow:hidden">
        <tr><td style="background:#00325e;padding:24px 30px;color:#ffffff;font-size:22px;font-weight:bold">INAPEL</td></tr>
        <tr><td style="padding:28px 30px;color:#555555;font-size:14px;line-height:1.6">
          <h2 style="margin:0 0 16px;color:#00325e;font-size:19px">Gestión comercial pendiente</h2>
          <p>Calidad terminó la investigación del PQR y Comercial debe continuar con la gestión.</p>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #e5e5e5;border-bottom:1px solid #e5e5e5;margin:18px 0">
            <tr><td style="padding:7px 0;color:#888888">Radicado</td><td style="padding:7px 0;text-align:right;font-weight:bold;color:#00325e">{radicado_html}</td></tr>
            <tr><td style="padding:7px 0;color:#888888">Cliente</td><td style="padding:7px 0;text-align:right">{cliente}</td></tr>
            <tr><td style="padding:7px 0;color:#888888">Tipo de solicitud</td><td style="padding:7px 0;text-align:right">{tipo}</td></tr>
            <tr><td style="padding:7px 0;color:#888888">Fecha del PQR</td><td style="padding:7px 0;text-align:right">{fecha}</td></tr>
          </table>
          <p>Complete los siguientes campos de la sección Gestión comercial:</p>
          <ul>{pendientes_html}</ul>
          {enlace_html}
          <p style="font-size:11px;color:#8a97a5">Correo generado automáticamente por el Sistema de Gestión PQR.</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ==========================================================
# PLANTILLA HTML
# ==========================================================

def _plantilla_html(radicado, correo_cliente, datos):

    nombre_cliente = str(datos.get("cliente", "") or "").strip() or correo_cliente
    fecha = str(datos.get("fechaRec", "") or "").strip()
    tipo = str(datos.get("tipoSol", "") or "").strip() or "PQR"
    estado = str(datos.get("estado", "") or "Recibido").strip()
    descripcion = str(datos.get("desc", "") or "").strip()
    anio = datetime.now().year

    url_base = _var("PQR_URL_BASE", "").strip().rstrip("/")

    bloque_consulta = ""
    if url_base:
        bloque_consulta = (
            '<p style="margin:0 0 8px">Con este número de radicado puede consultar '
            'el estado y seguimiento de su solicitud en nuestro portal:</p>'
            f'<p style="margin:0 0 18px"><a href="{url_base}" '
            'style="background:#00325e;color:#ffffff;text-decoration:none;'
            'padding:10px 22px;border-radius:6px;display:inline-block;font-weight:bold">'
            "Consultar estado de mi PQR</a></p>"
        )
    else:
        bloque_consulta = (
            '<p style="margin:0 0 18px">Con este número de radicado podrá consultar '
            "posteriormente el estado y seguimiento de su solicitud."
        )

    bloque_descripcion = ""
    if descripcion:
        bloque_descripcion = (
            '<tr><td style="padding:6px 0;border-bottom:1px solid #e5e5e5">'
            'Descripción</td>'
            f'<td style="padding:6px 0;border-bottom:1px solid #e5e5e5;color:#333333">{descripcion}</td></tr>'
        )

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background-color:#f0f4f8;font-family:Arial,Helvetica,sans-serif">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f4f8;padding:24px 12px">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background-color:#ffffff;border-radius:10px;overflow:hidden;border:1px solid #dde5ee">
        <!-- Encabezado -->
        <tr>
          <td style="background-color:#00325e;padding:26px 32px;color:#ffffff">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="font-size:22px;font-weight:bold;letter-spacing:1px">INAPEL</td>
                <td align="right" style="font-size:11px;color:#b8cfe3;line-height:1.5">
                  Industria Nacional<br>Papelera S.A.S.
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <!-- Cuerpo -->
        <tr>
          <td style="padding:30px 32px">
            <h2 style="margin:0 0 16px;font-size:18px;color:#00325e">Confirmación de PQR recibida</h2>
            <p style="margin:0 0 14px;font-size:14px;color:#555555;line-height:1.6">
              Estimado/a <strong>{nombre_cliente}</strong>:
            </p>
            <p style="margin:0 0 18px;font-size:14px;color:#555555;line-height:1.6">
              Hemos recibido correctamente su PQR. Nuestro equipo dará inicio a la gestión
              de su solicitud y le mantendremos informado sobre su avance.
            </p>
            <!-- Radicado destacado -->
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#eef4fb;border:1px solid #cfe0f2;border-radius:8px;margin-bottom:20px">
              <tr>
                <td align="center" style="padding:16px 12px">
                  <div style="font-size:11px;color:#5a6b80;letter-spacing:.5px;margin-bottom:4px">
                    NÚMERO DE RADICADO
                  </div>
                  <div style="font-size:22px;font-weight:bold;color:#00325e;font-family:'Courier New',monospace">
                    {radicado}
                  </div>
                </td>
              </tr>
            </table>
            <!-- Detalles -->
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:13px;color:#555555;border-top:1px solid #e5e5e5;margin-bottom:20px">
              <tr>
                <td style="padding:6px 0;border-bottom:1px solid #e5e5e5;color:#888888">Fecha de registro</td>
                <td style="padding:6px 0;border-bottom:1px solid #e5e5e5;text-align:right;color:#333333">{fecha or "—"}</td>
              </tr>
              <tr>
                <td style="padding:6px 0;border-bottom:1px solid #e5e5e5;color:#888888">Estado</td>
                <td style="padding:6px 0;border-bottom:1px solid #e5e5e5;text-align:right;color:#333333">{estado}</td>
              </tr>
              <tr>
                <td style="padding:6px 0;border-bottom:1px solid #e5e5e5;color:#888888">Tipo de solicitud</td>
                <td style="padding:6px 0;border-bottom:1px solid #e5e5e5;text-align:right;color:#333333">{tipo}</td>
              </tr>
              {bloque_descripcion}
            </table>
            {bloque_consulta}
            <p style="margin:0 0 6px;font-size:13px;color:#777777;line-height:1.6">
              <strong>Importante:</strong> conserve el número de radicado, es la referencia
              de su solicitud ante INAPEL.
            </p>
            <p style="margin:0 0 10px;font-size:14px;color:#555555">
              Gracias por comunicarse con INAPEL.
            </p>
          </td>
        </tr>
        <!-- Pie -->
        <tr>
          <td style="background-color:#f7fafc;border-top:1px solid #e5e5e5;padding:16px 32px;font-size:11px;color:#8a97a5;line-height:1.6">
            Este es un correo generado automáticamente por el Sistema de Gestión de PQR.
            No responda este mensaje. © {anio} Industria Nacional Papelera S.A.S.
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
