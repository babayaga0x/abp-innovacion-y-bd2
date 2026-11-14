# ============================================================
# UTILIDADES DE CONSOLA
# ============================================================
# Funciones de presentación compartidas por todos los menús:
# limpieza de pantalla, títulos, formato de números y la
# selección de un elemento de una lista numerada.
# ============================================================

import os
import textwrap

from config import ANCHO


# Formatos para la terminal
NEGRITA = "\033[1m"
CURSIVA = "\033[3m"
TENUE = "\033[2m"
NORMAL = "\033[0m"


def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")


def pausar(mensaje="Presione ENTER para continuar..."):
    input("\n" + mensaje)


def linea(caracter="-", ancho=ANCHO):
    print(caracter * ancho)


def titulo(texto, ancho=ANCHO):
    print("\n" + "=" * ancho)
    print(texto.center(ancho))
    print("=" * ancho)


def texto_centrado(texto, ancho_texto=78, ancho=ANCHO, formato=""):

    for renglon in textwrap.wrap(texto, width=ancho_texto):
        print(formato + renglon.center(ancho) + (NORMAL if formato else ""))


# ------------------------------------------------------------
# Formato de números (separador de miles con punto)
# ------------------------------------------------------------

def miles(valor):

    if valor is None:
        return "-"

    return format(int(round(float(valor))), ",").replace(",", ".")


def porcentaje(valor, decimales=0):

    if valor is None:
        return "-"

    return f"{float(valor):.{decimales}f} %".replace(".", ",")


# ------------------------------------------------------------
# Tablas
# ------------------------------------------------------------
# columnas: lista de (título, ancho, alineación), con
# alineación "<" (izquierda) o ">" (derecha).
# ------------------------------------------------------------

def formatear_fila(valores, columnas):

    partes = []

    for valor, (_, ancho, alineacion) in zip(valores, columnas):

        texto = "" if valor is None else str(valor)

        # Deja al menos un espacio entre columnas
        texto = texto[:ancho - 1]

        partes.append(f"{texto:{alineacion}{ancho}}")

    return "".join(partes)


def imprimir_tabla(columnas, filas, titulo_tabla=None):

    ancho = sum(columna[1] for columna in columnas)

    if titulo_tabla:
        titulo(titulo_tabla, ancho)

    print(formatear_fila([columna[0] for columna in columnas], columnas))
    linea("-", ancho)

    for fila in filas:
        print(formatear_fila(fila, columnas))

    linea("-", ancho)


# ------------------------------------------------------------
# Selección de un elemento de una lista numerada
# ------------------------------------------------------------

def elegir_de_lista(elementos, mostrar=str, encabezado=None, nombre="una opción"):
    """
    Muestra los elementos numerados y devuelve el elegido.
    Devuelve None si el usuario presiona ENTER o si la opción
    es inválida.
    """

    if not elementos:
        print("\nNo hay elementos para seleccionar.")
        pausar()
        return None

    if encabezado:
        print(f"\n{encabezado}\n")

    for numero, elemento in enumerate(elementos, start=1):
        print(f"{numero:>3}. {mostrar(elemento)}")

    opcion = input(
        f"\nSeleccione {nombre} o presione ENTER para volver: "
    ).strip()

    if opcion == "":
        return None

    if not opcion.isdigit() or not 1 <= int(opcion) <= len(elementos):
        print("\nOpción inválida.")
        pausar()
        return None

    return elementos[int(opcion) - 1]


def confirmar_accion(mensaje):
    respuesta = input(f"\n{mensaje} (S/N): ").strip().upper()
    return respuesta == "S"
