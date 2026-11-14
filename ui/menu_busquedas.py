# ============================================================
# BÚSQUEDAS (opciones 6 y 7 del menú principal)
# ============================================================
# Búsqueda 1: por región (un criterio).
# Búsqueda 2: por cultivo y campaña (dos criterios simultáneos).
#
# Ambas devuelven objetos AnalisisRegional con el resultado de
# las tres situaciones desfavorables.
# ============================================================

from modelos.dimensiones import Region, Cultivo, Campania
from modelos.situaciones import AnalisisRegional
from ui.consola import limpiar_pantalla, pausar, imprimir_tabla, elegir_de_lista


COLUMNAS_SITUACIONES = [
    ("S1", 8, ">"),
    ("S2", 8, ">"),
    ("S3", 8, ">"),
    ("ALERTAS", 10, ">")
]


def valores_situaciones(analisis):

    return (
        analisis.situacion_1 or "-",
        analisis.situacion_2 or "-",
        analisis.situacion_3 or "-",
        analisis.cantidad_alertas()
    )


def imprimir_referencias():
    print("S1: superficie no cosechada | S2: bajo rendimiento | "
          "S3: caída sostenida de la producción")


# ============================================================
# OPCIÓN 6 - BÚSQUEDA POR REGIÓN
# ============================================================

def menu_busqueda_por_region():

    limpiar_pantalla()

    region = elegir_de_lista(
        Region.listar(),
        encabezado="BÚSQUEDA POR REGIÓN",
        nombre="una región"
    )

    if region is None:
        limpiar_pantalla()
        return

    resultados = AnalisisRegional.buscar_por_region(region.region_nombre)

    limpiar_pantalla()

    columnas = [
        ("CULTIVO", 20, "<"),
        ("CAMPAÑA", 15, "<")
    ] + COLUMNAS_SITUACIONES

    filas = [
        (
            analisis.cultivo.cultivo_nombre,
            analisis.campania.campania
        ) + valores_situaciones(analisis)
        for analisis in resultados
    ]

    imprimir_tabla(columnas, filas, f"RESULTADOS DESFAVORABLES - {region}")

    imprimir_referencias()
    print("Casos con al menos una situación desfavorable:", len(resultados))

    pausar("Presione ENTER para volver al menú principal...")
    limpiar_pantalla()


# ============================================================
# OPCIÓN 7 - BÚSQUEDA POR CULTIVO Y CAMPAÑA
# ============================================================

def menu_busqueda_por_cultivo_campania():

    limpiar_pantalla()

    cultivo = elegir_de_lista(
        Cultivo.listar(),
        encabezado="BÚSQUEDA POR CULTIVO Y CAMPAÑA\n\nCULTIVOS",
        nombre="un cultivo"
    )

    if cultivo is None:
        limpiar_pantalla()
        return

    limpiar_pantalla()

    campania = elegir_de_lista(
        Campania.listar(),
        encabezado=f"CULTIVO SELECCIONADO: {cultivo}\n\nCAMPAÑAS",
        nombre="una campaña"
    )

    if campania is None:
        limpiar_pantalla()
        return

    resultados = AnalisisRegional.buscar_por_cultivo_campania(
        cultivo.cultivo_nombre,
        campania.campania
    )

    limpiar_pantalla()

    columnas = [("REGIÓN", 20, "<")] + COLUMNAS_SITUACIONES

    filas = [
        (analisis.region.region_nombre,) + valores_situaciones(analisis)
        for analisis in resultados
    ]

    imprimir_tabla(columnas, filas, f"{cultivo} - CAMPAÑA {campania}")

    imprimir_referencias()
    print("Regiones encontradas:", len(resultados))

    pausar("Presione ENTER para volver al menú principal...")
    limpiar_pantalla()
