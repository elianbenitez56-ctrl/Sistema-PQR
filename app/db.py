import logging
import os
import time
from contextlib import contextmanager

from mysql.connector import Error, pooling

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Configuración de conexión MySQL (variables de entorno)
# -------------------------------------------------------------------------

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "sistema_pqr")


# -------------------------------------------------------------------------
# Context managers para conexiones y cursores
# -------------------------------------------------------------------------

_POOL = None


def _pool():
    global _POOL
    if _POOL is None:
        _POOL = pooling.MySQLConnectionPool(
            pool_name="pqr",
            pool_size=int(os.getenv("MYSQL_POOL_SIZE", "16")),
            pool_reset_session=True,
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
            connection_timeout=10,
        )
    return _POOL


@contextmanager
def get_db_connection():
    try:
        conn = _pool().get_connection()
    except Error:
        logger.exception("Error de conexión MySQL")
        raise
    try:
        yield conn
    finally:
        conn.close()  # devuelve la conexión al pool


@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor(dictionary=True)
            yield cursor
            if commit:
                conn.commit()
        except Error:
            if conn.is_connected():
                conn.rollback()
            raise
        finally:
            cursor.close()


# -------------------------------------------------------------------------
# Esquema de tablas (ejecutar una sola vez al iniciar)
# -------------------------------------------------------------------------

SCHEMA_SQL = [
    # Tabla usuarios
    """CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(150) NOT NULL,
        usuario VARCHAR(80) UNIQUE NOT NULL,
        contrasena_hash VARCHAR(255) NOT NULL,
        rol VARCHAR(50) NOT NULL,
        linea_producto VARCHAR(50) DEFAULT '',
        empresa VARCHAR(100) DEFAULT 'INAPEL',
        activo TINYINT(1) DEFAULT 1,
        fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        documento VARCHAR(20) DEFAULT '',
        correo VARCHAR(120) DEFAULT '',
        telefono VARCHAR(20) DEFAULT ''
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
    # Tabla PQR
    """CREATE TABLE IF NOT EXISTS pqr (
        radicado VARCHAR(25) PRIMARY KEY,
        fecha DATETIME NOT NULL,
        hora TIME NOT NULL,
        tipo VARCHAR(50) DEFAULT '',
        cliente VARCHAR(150) DEFAULT '',
        nit VARCHAR(20) DEFAULT '',
        contacto VARCHAR(150) DEFAULT '',
        telefono VARCHAR(20) DEFAULT '',
        correo VARCHAR(120) DEFAULT '',
        estado VARCHAR(50) DEFAULT 'Recibido',
        prioridad VARCHAR(50) DEFAULT '',
        descripcion TEXT DEFAULT (''),
        expectativa TEXT DEFAULT (''),
        productos JSON DEFAULT ('[]'),
        empresa VARCHAR(100) DEFAULT 'INAPEL',
        vendedor VARCHAR(150) DEFAULT '',
        linea VARCHAR(50) DEFAULT '',
        usuario_id INT DEFAULT 0,
        correo_confirmacion_enviado TINYINT(1) DEFAULT 0,
        documento_receptor VARCHAR(20) DEFAULT '',
        correo_receptor VARCHAR(120) DEFAULT '',
        telefono_receptor VARCHAR(20) DEFAULT '',
        cargo_receptor VARCHAR(50) DEFAULT '',
        area_receptor VARCHAR(50) DEFAULT '',
        ciudad_recepcion VARCHAR(100) DEFAULT '',
        departamento_recepcion VARCHAR(100) DEFAULT '',
        medio_recepcion VARCHAR(50) DEFAULT '',
        otro_medio_recepcion VARCHAR(100) DEFAULT ''
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
    # Tabla Historial
    """CREATE TABLE IF NOT EXISTS historial (
        id INT AUTO_INCREMENT PRIMARY KEY,
        radicado VARCHAR(25) NOT NULL,
        estado VARCHAR(50) NOT NULL,
        usuario VARCHAR(150) NOT NULL,
        fecha DATE NOT NULL,
        hora TIME NOT NULL,
        observacion TEXT DEFAULT (''),
        INDEX idx_radicado (radicado)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
    # Tabla Investigaciones
    """CREATE TABLE IF NOT EXISTS investigaciones (
        radicado VARCHAR(25) PRIMARY KEY,
        responsable VARCHAR(150) DEFAULT '',
        cargo VARCHAR(100) DEFAULT '',
        herramienta TEXT DEFAULT (''),
        causa TEXT DEFAULT (''),
        accion TEXT DEFAULT (''),
        notificar TINYINT(1) DEFAULT 0,
        fecha_respuesta DATE,
        fecha_cierre DATE,
        cierre VARCHAR(10) DEFAULT 'No',
        respuesta TEXT DEFAULT (''),
        departamentos TEXT DEFAULT (''),
        calidad_estado VARCHAR(50) DEFAULT 'pendiente',
        comercial_estado VARCHAR(50) DEFAULT 'pendiente',
        notificacion_comercial_enviada TINYINT(1) DEFAULT 0,
        respuesta_calidad TEXT DEFAULT (''),
        respuesta_comercial TEXT DEFAULT (''),
        INDEX idx_radicado (radicado)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
    # Tabla Adjuntos
    """CREATE TABLE IF NOT EXISTS adjuntos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        radicado VARCHAR(25) NOT NULL,
        tipo VARCHAR(50) DEFAULT '',
        archivo_original VARCHAR(255) NOT NULL,
        ruta_archivo VARCHAR(500) NOT NULL,
        fecha DATE,
        hora TIME,
        usuario VARCHAR(150) DEFAULT '',
        observacion TEXT DEFAULT (''),
        INDEX idx_radicado (radicado)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"""
]


# -------------------------------------------------------------------------
# Inicializar tablas al importar
# -------------------------------------------------------------------------

def asegurar_tablas(intentos=30, espera=2):
    """Crea las tablas; espera a que MySQL acepte conexiones (arranque en docker)."""
    for intento in range(1, intentos + 1):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            break
        except Error:
            if intento == intentos:
                raise
            logger.warning("MySQL no disponible (%s/%s), reintentando...", intento, intentos)
            time.sleep(espera)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        for sql in SCHEMA_SQL:
            cursor.execute(sql)
        conn.commit()
    logger.info("Tablas MySQL aseguradas correctamente.")
