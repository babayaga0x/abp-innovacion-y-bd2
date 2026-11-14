# ============================================================
# CONEXIÓN CON MYSQL
# ============================================================
# Una única conexión compartida por toda la aplicación.
# Los módulos no manejan cursores directamente: usan las
# funciones consultar / ejecutar, que abren y cierran el
# cursor en cada operación.
#
# Las funciones no confirman cambios: cada operación de
# negocio decide cuándo llamar a confirmar() o revertir(),
# para poder agrupar varios pasos en una misma transacción.
# ============================================================

import os
from getpass import getpass

import mysql.connector

from config import DB_HOST, DB_USER, DB_NAME


_conexion = None


def obtener_conexion():

    global _conexion

    if _conexion is None or not _conexion.is_connected():

        password = os.getenv("MYSQL_PASSWORD")

        if password is None:
            password = getpass("Ingrese la contraseña de MySQL: ")

        _conexion = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=password,
            database=DB_NAME,
            allow_local_infile=True
        )

    return _conexion


# ------------------------------------------------------------
# Consultas (SELECT)
# ------------------------------------------------------------

def consultar(sql, parametros=None):

    cursor = obtener_conexion().cursor()

    try:
        cursor.execute(sql, parametros)
        return cursor.fetchall()

    finally:
        cursor.close()


def consultar_uno(sql, parametros=None):

    filas = consultar(sql, parametros)

    return filas[0] if filas else None


# ------------------------------------------------------------
# Sentencias de modificación (INSERT, UPDATE, DELETE, DDL)
# ------------------------------------------------------------

def ejecutar(sql, parametros=None):

    cursor = obtener_conexion().cursor()

    try:
        cursor.execute(sql, parametros)
        return cursor.rowcount

    finally:
        cursor.close()


def ejecutar_varios(sql, filas):

    if not filas:
        return 0

    cursor = obtener_conexion().cursor()

    try:
        cursor.executemany(sql, filas)
        return cursor.rowcount

    finally:
        cursor.close()


# ------------------------------------------------------------
# Transacciones
# ------------------------------------------------------------

def confirmar():
    obtener_conexion().commit()


def revertir():
    obtener_conexion().rollback()


def cerrar():

    global _conexion

    if _conexion is not None and _conexion.is_connected():
        _conexion.close()

    _conexion = None
