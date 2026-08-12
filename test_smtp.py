"""
Prueba independiente de conexión SMTP — Sistema PQR INAPEL.

NO crea PQR. Verifica por etapas:
  1. Estado de las variables de entorno
  2. Conexión al servidor
  3. STARTTLS / SSL
  4. Autenticación
  5. Envío de un correo de prueba

Uso:
    python test_smtp.py                      # solo diagnóstico + conexión/auth opcional
    python test_smtp.py --enviar destinatario@correo.com   # además envía un correo de prueba

NUNCA imprime SMTP_PASSWORD.
"""

import sys
import smtplib
from email.mime.text import MIMEText

from email_service import _var, variables_smtp_faltantes, smtp_configurado


def _ocultar(correo):
    correo = str(correo or "")
    if "@" in correo:
        return correo[:3] + "***" + correo[correo.index("@"):]
    return "***"


def revisar_variables():
    print("=== 1. VARIABLES DE ENTORNO ===")
    for nombre in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_FROM", "SMTP_USE_TLS", "SMTP_USE_SSL"):
        valor = _var(nombre, "")
        if nombre == "SMTP_HOST" and valor:
            print(f"  {nombre} = {valor}")
        elif nombre == "SMTP_USER" and valor:
            print(f"  {nombre} = {_ocultar(valor)}")
        elif nombre == "SMTP_FROM" and valor:
            print(f"  {nombre} = {_ocultar(valor)}")
        elif nombre == "SMTP_PASSWORD":
            print(f"  {nombre} = *** (no se muestra)")
        else:
            print(f"  {nombre} = {valor!r}")

    faltantes = variables_smtp_faltantes()
    if faltantes:
        print(f"  FALTAN: {', '.join(faltantes)}")
    else:
        print("  Todas las variables obligatorias están presentes.")


def probar_conexion():
    print("\n=== 2. CONEXION AL SERVIDOR SMTP ===")
    if not smtp_configurado():
        print("  ABORTADO: configure SMTP_HOST, SMTP_USER y SMTP_PASSWORD primero.")
        return False, "sin_configuracion"

    host = _var("SMTP_HOST", "").strip()
    puerto = int(_var("SMTP_PORT", "587"))
    usar_tls = _var("SMTP_USE_TLS", "true").strip().lower() in ("1", "true", "yes", "sí")
    usar_ssl = _var("SMTP_USE_SSL", "").strip().lower() in ("1", "true", "yes", "sí")
    modo = "SSL directo (465)" if usar_ssl else ("STARTTLS" if usar_tls else "SIN TLS")

    print(f"  Host: {host}")
    print(f"  Puerto: {puerto}  |  Modo: {modo}")

    try:
        if usar_ssl:
            servidor = smtplib.SMTP_SSL(host, puerto, timeout=20)
        else:
            servidor = smtplib.SMTP(host, puerto, timeout=20)
            servidor.ehlo()
            if usar_tls:
                servidor.starttls()
                servidor.ehlo()
    except Exception as e:
        tipo = "SSL" if usar_ssl else ("TLS/STARTTLS" if usar_tls else "plano")
        print(f"  ERROR en conexión {tipo}: {e}")
        return False, f"conexion: {e}"

    print("  CONEXION EXITOSA.")

    print("\n=== 3. AUTENTICACION ===")
    try:
        servidor.login(_var("SMTP_USER", ""), _var("SMTP_PASSWORD", ""))
        print("  AUTENTICACION EXITOSA (SMTP_USER/SMTP_PASSWORD correctos).")
    except Exception as e:
        print(f"  ERROR DE AUTENTICACION: {e}")
        print("  Causas probables: credenciales incorrectas, o necesita una "
              "contraseña de aplicación (Gmail con verificación en 2 pasos).")
        servidor.quit()
        return False, f"autenticacion: {e}"

    servidor.quit()
    return True, "ok"


def enviar_prueba(destinatario):
    print("\n=== 4. ENVIO DE CORREO DE PRUEBA ===")
    if not smtp_configurado():
        print("  ABORTADO: configure SMTP antes de enviar.")
        return False, "sin_configuracion"

    remitente = _var("SMTP_FROM", _var("SMTP_USER", "")).strip()
    asunto = "Prueba SMTP - Sistema PQR INAPEL"
    cuerpo = "Este es un correo de prueba del Sistema PQR."

    mensaje = MIMEText(cuerpo, "plain", "utf-8")
    mensaje["Subject"] = asunto
    mensaje["From"] = remitente
    mensaje["To"] = destinatario

    host = _var("SMTP_HOST", "").strip()
    puerto = int(_var("SMTP_PORT", "587"))
    usar_tls = _var("SMTP_USE_TLS", "true").strip().lower() in ("1", "true", "yes", "sí")
    usar_ssl = _var("SMTP_USE_SSL", "").strip().lower() in ("1", "true", "yes", "sí")

    try:
        if usar_ssl:
            servidor = smtplib.SMTP_SSL(host, puerto, timeout=20)
        else:
            servidor = smtplib.SMTP(host, puerto, timeout=20)
            servidor.ehlo()
            if usar_tls:
                servidor.starttls()
                servidor.ehlo()
        servidor.login(_var("SMTP_USER", ""), _var("SMTP_PASSWORD", ""))
        servidor.sendmail(remitente, [destinatario], mensaje.as_string())
        servidor.quit()
        print(f"  ENVIO EXITOSO de {_ocultar(remitente)} a {_ocultar(destinatario)}.")
        return True, "ok"
    except Exception as e:
        print(f"  ERROR AL ENVIAR: {e}")
        return False, f"envio: {e}"


if __name__ == "__main__":

    enviar = False
    destinatario = ""
    for arg in sys.argv[1:]:
        if arg == "--enviar":
            enviar = True
        elif arg.startswith("--"):
            print(f"Argumento desconocido: {arg}")
            sys.exit(2)
        else:
            destinatario = arg

    revisar_variables()

    ok_conexion, motivo = probar_conexion()
    if not ok_conexion:
        print(f"\nRESULTADO: FALLO en etapa '{motivo}'.")
        sys.exit(1)

    if enviar:
        if not destinatario:
            print("Debe indicar el destinatario: python test_smtp.py --enviar correo@destino.com")
            sys.exit(2)
        ok_envio, motivo2 = enviar_prueba(destinatario)
        if not ok_envio:
            print(f"\nRESULTADO: FALLO en etapa '{motivo2}'.")
            sys.exit(1)
        print("\nRESULTADO: SMTP OK (conexión, autenticación y envío correctos).")
    else:
        print("\nRESULTADO: conexión y autenticación SMTP correctas.")
        print("Para probar el envío real: python test_smtp.py --enviar correo@destino.com")