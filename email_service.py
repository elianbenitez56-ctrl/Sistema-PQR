"""
Servicio de correo electrónico — Sistema PQR INAPEL.

Envía la confirmación de recepción de PQR al correo del cliente.

Credenciales SMTP SOLO por variables de entorno:
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
Opcionales:
    PQR_URL_BASE  -> URL pública del sistema para el enlace de consulta
    SMTP_USE_TLS  -> "1"/"true" para STARTTLS (defecto: true)
    SMTP_USE_SSL  -> "1"/"true" para SSL directo (port 465; defecto: false)

También soporta un archivo .env local (solo desarrollo; está en .gitignore).
Nunca se escribe una contraseña en el código ni se expone en JSON/logs.
"""

import os
import re
import smtplib
import sys
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

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


def _correo_valido(correo):
    return bool(correo) and re.match(EMAIL_REGEX, correo.strip()) is not None


def smtp_configurado():
    """Indica si existen variables SMTP suficientes para intentar el envío."""

    host = _var("SMTP_HOST", "").strip()
    usuario = _var("SMTP_USER", "")
    contrasena = _var("SMTP_PASSWORD", "")

    return bool(host and usuario and contrasena)


def variables_smtp_faltantes():
    """Devuelve la lista de variables SMTP obligatorias que están vacías."""

    faltantes = []
    for nombre in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
        if not _var(nombre, ""):
            faltantes.append(nombre)
    return faltantes


def enviar_confirmacion_pqr(radicado, correo_cliente, datos):
    """
    Envía el correo de confirmación de PQR al cliente.

    Retorna (True, "") si se envió, o (False, motivo) si no.
    Nunca lanza excepciones: cualquier error se registra en logs
    y se devuelve como (False, motivo) para no bloquear la PQR.
    """

    try:
        if not smtp_configurado():
            faltan = ", ".join(variables_smtp_faltantes())
            print(f"[correo] SMTP no configurado: faltan las variables {faltan}. "
                  "El correo de confirmación NO se envió.")
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

        host = _var("SMTP_HOST", "").strip()
        puerto = int(_var("SMTP_PORT", "587"))
        usuario = _var("SMTP_USER", "")
        contrasena = _var("SMTP_PASSWORD", "")
        usar_tls = _var("SMTP_USE_TLS", "true").strip().lower() in ("1", "true", "yes", "sí")
        usar_ssl = _var("SMTP_USE_SSL", "").strip().lower() in ("1", "true", "yes", "sí")

        # Log de diagnóstico SIN credenciales.
        from_addr = str(mensaje["From"] or "")
        from_oculto = from_addr[:3] + "***" if "@" in from_addr else "***"
        dest_oculto = correo_cliente[:3] + "***" if "@" in correo_cliente else "***"
        modo = "SSL directo" if usar_ssl else ("STARTTLS" if usar_tls else "SIN TLS")
        print(f"[correo] Intento de envío: host={host}:{puerto} modo={modo} "
              f"from={from_oculto} to={dest_oculto}")

        if usar_ssl:
            servidor = smtplib.SMTP_SSL(host, puerto, timeout=20)
        else:
            servidor = smtplib.SMTP(host, puerto, timeout=20)
            servidor.ehlo()
            if usar_tls:
                servidor.starttls()
                servidor.ehlo()

        try:
            servidor.login(usuario, contrasena)
            servidor.sendmail(mensaje["From"], [mensaje["To"]], mensaje.as_string())
        finally:
            try:
                servidor.quit()
            except Exception:
                pass

        print(f"[correo] Confirmación enviada para {radicado} -> {correo_cliente}")
        return True, ""

    except Exception as e:
        print(f"[correo] ERROR al enviar confirmación para {radicado}: {e}")
        traceback.print_exc(file=sys.stderr)
        return False, f"Error SMTP: {e}"


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
            f'style="background:#00325e;color:#ffffff;text-decoration:none;'
            f'padding:10px 22px;border-radius:6px;display:inline-block;font-weight:bold">'
            "Consultar estado de mi PQR</a></p>"
        )
    else:
        bloque_consulta = (
            '<p style="margin:0 0 18px">Con este número de radicado podrá consultar '
            "posteriormente el estado y seguimiento de su solicitud.</p>"
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
              de su solicitud y le mantendrá informado sobre su avance.
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