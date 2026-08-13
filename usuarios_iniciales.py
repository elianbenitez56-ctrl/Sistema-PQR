# =============================================================
# USUARIOS INICIALES — SISTEMA DE GESTIÓN PQR · INAPEL
# =============================================================
#
# Estructura comercial de INAPEL (empresa única):
#
#   INAPEL (Industria Nacional Papelera S.A.S.)
#   ├── Línea de productos INAPEL   → 13 vendedores (YA CARGADOS)
#   └── Línea de productos TOROFIL  →  1 vendedor (PENDIENTE)
#
# Además:
#   - 1 Líder de Calidad     (PENDIENTE)
#   - 2 Líderes de Comercial (PENDIENTE)
#
# =============================================================
# ⚠ CREDENCIALES TEMPORALES — PENDIENTES DE DEFINICIÓN OFICIAL
# =============================================================
#
# FORMATO DE USUARIO (TEMPORAL): el usuario de acceso de cada vendedor
# es su número de DOCUMENTO (cédula).
#
#   Ejemplo: MARTA SANCHEZ → usuario: 60342139
#
# CONTRASEÑA (TEMPORAL): "Inapel2026" para todos los vendedores.
#
# ESTAS CREDENCIALES SON TEMPORALES Y DEBEN SER REEMPLAZADAS cuando la
# empresa defina oficialmente el formato de usuario y contraseña.
# Para cambiarlas: edite este archivo y vuelva a desplegar, o use
# PUT /api/usuarios/<id> como administrador.
#
# =============================================================
# ESTRUCTURA POR USUARIO:
#   {
#       "nombre": "Nombre completo",
#       "documento": "Número de documento",
#       "usuario": "usuario de acceso",
#       "contrasena": "clave (se almacena con hash seguro)",
#       "rol": "VENDEDOR | LIDER_CALIDAD | LIDER_COMERCIAL",
#       "linea_producto": "INAPEL | TOROFIL (solo vendedores)",
#       "empresa": "INAPEL"   ← SIEMPRE INAPEL para todos
#   }
# =============================================================

USUARIOS_INICIALES = [
    # ------------------------------------------------------------------
    # VENDEDORES — LÍNEA INAPEL (13) · Empresa: INAPEL · Rol: VENDEDOR
    # ------------------------------------------------------------------
    {
        "nombre": "MARTA SANCHEZ",
        "documento": "60342139",
        "usuario": "60342139",
        "contrasena": "Inapel2026",
        "rol": "VENDEDOR",
        "linea_producto": "INAPEL",
        "empresa": "INAPEL"
    },
    {
        "nombre": "ANTONIO TORREGROSA",
        "documento": "8726817",
        "usuario": "8726817",
        "contrasena": "Inapel2026",
        "rol": "VENDEDOR",
        "linea_producto": "INAPEL",
        "empresa": "INAPEL"
    },
    {
        "nombre": "STEFANI PEREZ",
        "documento": "1143148133",
        "usuario": "1143148133",
        "contrasena": "Inapel2026",
        "rol": "VENDEDOR",
        "linea_producto": "INAPEL",
        "empresa": "INAPEL"
    },
    {
        "nombre": "GISELA RAMOS",
        "documento": "1045760347",
        "usuario": "1045760347",
        "contrasena": "Inapel2026",
        "rol": "VENDEDOR",
        "linea_producto": "INAPEL",
        "empresa": "INAPEL"
    },
    {
        "nombre": "LEYDI JOHANA ARIAS",
        "documento": "1019036169",
        "usuario": "1019036169",
        "contrasena": "Inapel2026",
        "rol": "VENDEDOR",
        "linea_producto": "INAPEL",
        "empresa": "INAPEL"
    },
    {
        "nombre": "JANETH JIMENEZ RODRIGUEZ",
        "documento": "39766266",
        "usuario": "39766266",
        "contrasena": "Inapel2026",
        "rol": "VENDEDOR",
        "linea_producto": "INAPEL",
        "empresa": "INAPEL"
    },
    {
        "nombre": "DIEGO MEJIA",
        "documento": "70601935",
        "usuario": "70601935",
        "contrasena": "Inapel2026",
        "rol": "VENDEDOR",
        "linea_producto": "INAPEL",
        "empresa": "INAPEL"
    },
    {
        "nombre": "DARLISON QUINTERO",
        "documento": "1146442302",
        "usuario": "1146442302",
        "contrasena": "Inapel2026",
        "rol": "VENDEDOR",
        "linea_producto": "INAPEL",
        "empresa": "INAPEL"
    },
    {
        "nombre": "TATIANA GONZALEZ",
        "documento": "52275924",
        "usuario": "52275924",
        "contrasena": "Inapel2026",
        "rol": "VENDEDOR",
        "linea_producto": "INAPEL",
        "empresa": "INAPEL"
    },
    {
        "nombre": "ANTONIO TABORDA",
        "documento": "8723921",
        "usuario": "8723921",
        "contrasena": "Inapel2026",
        "rol": "VENDEDOR",
        "linea_producto": "INAPEL",
        "empresa": "INAPEL"
    },
    {
        "nombre": "RICARDO RUIZ",
        "documento": "87305332",
        "usuario": "87305332",
        "contrasena": "Inapel2026",
        "rol": "VENDEDOR",
        "linea_producto": "INAPEL",
        "empresa": "INAPEL"
    },
    {
        "nombre": "JUDANIS SARMIENTO",
        "documento": "22478148",
        "usuario": "22478148",
        "contrasena": "Inapel2026",
        "rol": "VENDEDOR",
        "linea_producto": "INAPEL",
        "empresa": "INAPEL"
    },
    {
        "nombre": "YUNITH DIAZ",
        "documento": "1232888219",
        "usuario": "1232888219",
        "contrasena": "Inapel2026",
        "rol": "VENDEDOR",
        "linea_producto": "INAPEL",
        "empresa": "INAPEL"
    },
    # ------------------------------------------------------------------
    # VENDEDOR — LÍNEA TOROFIL (1) · PENDIENTE
    # { "nombre": "", "documento": "", "usuario": "", "contrasena": "", "rol": "VENDEDOR", "linea_producto": "TOROFIL", "empresa": "INAPEL" },
    # ------------------------------------------------------------------
    # LÍDER DE CALIDAD (1) · PENDIENTE
    # { "nombre": "", "documento": "", "usuario": "", "contrasena": "", "rol": "LIDER_CALIDAD", "linea_producto": "", "empresa": "INAPEL" },
    # ------------------------------------------------------------------
    # LÍDERES DE COMERCIAL (2) · PENDIENTES
    # { "nombre": "", "documento": "", "usuario": "", "contrasena": "", "rol": "LIDER_COMERCIAL", "linea_producto": "", "empresa": "INAPEL" },
    # { "nombre": "", "documento": "", "usuario": "", "contrasena": "", "rol": "LIDER_COMERCIAL", "linea_producto": "", "empresa": "INAPEL" },
    # ------------------------------------------------------------------
]
