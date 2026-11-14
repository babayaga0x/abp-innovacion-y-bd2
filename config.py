# ============================================================
# CONFIGURACIÓN GENERAL DE LA APLICACIÓN
# ============================================================
# Los datos de conexión pueden definirse con variables de
# entorno o en un archivo .env junto a este (no se versiona).
# Si MYSQL_PASSWORD no está definida, la contraseña se
# solicita por consola al iniciar.
#
# MYSQL_DATABASE permite apuntar a una copia de prueba de la
# base (por ejemplo, estimaciones_agricolas_prueba) sin tocar
# el código.
# ============================================================

import os
from pathlib import Path


def cargar_env(ruta=Path(__file__).with_name(".env")):
    """Carga líneas CLAVE=valor del .env sin pisar variables ya definidas."""

    if not ruta.exists():
        return

    for renglon in ruta.read_text(encoding="utf-8").splitlines():

        renglon = renglon.strip()

        if not renglon or renglon.startswith("#") or "=" not in renglon:
            continue

        clave, valor = renglon.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


cargar_env()


DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_USER = os.getenv("MYSQL_USER", "root")
DB_NAME = os.getenv("MYSQL_DATABASE", "estimaciones_agricolas")


# Formato de la consola
ANCHO = 90
SANGRIA_MENU = " " * 10
