# ============================================================
# MENÚ PRINCIPAL
# ============================================================

from config import ANCHO, SANGRIA_MENU
from modelos.dimensiones import Campania
from ui.consola import (
    NEGRITA,
    CURSIVA,
    TENUE,
    NORMAL,
    limpiar_pantalla,
    texto_centrado
)
from ui.menu_situaciones import (
    menu_situacion_1,
    menu_situacion_2,
    menu_situacion_3,
    menu_incidencia,
    menu_focos_criticos
)
from ui.menu_busquedas import (
    menu_busqueda_por_region,
    menu_busqueda_por_cultivo_campania
)
from ui.menu_gestion import (
    menu_gestion_parametros,
    menu_gestion_estimaciones
)


# Descripción de cada análisis que se muestra en el encabezado
DESCRIPCIONES = [
    (
        "Situación desfavorable 1 - Superficie no cosechada",
        "Identifica regiones, cultivos y campañas con una tasa de superficie "
        "no cosechada superior al umbral establecido."
    ),
    (
        "Situación desfavorable 2 - Bajo rendimiento",
        "Identifica regiones cuyo rendimiento resulta inferior al rendimiento "
        "nacional del mismo cultivo y campaña."
    ),
    (
        "Situación desfavorable 3 - Caída sostenida de la producción",
        "Identifica regiones y cultivos que presentan tres o más caídas "
        "consecutivas de producción."
    ),
    (
        "Análisis de incidencia en la caída de producción",
        "Evalúa, dentro de las caídas sostenidas detectadas, el comportamiento "
        "de la superficie cosechada y del rendimiento."
    ),
    (
        "Focos críticos",
        "Identifica los casos en los que coinciden simultáneamente las tres "
        "situaciones desfavorables."
    )
]


# Opciones: (texto, función). La opción "Salir" se agrega al final.
OPCIONES = [
    ("Situación desfavorable 1 - Superficie no cosechada", menu_situacion_1),
    ("Situación desfavorable 2 - Bajo rendimiento", menu_situacion_2),
    ("Situación desfavorable 3 - Caída sostenida de la producción", menu_situacion_3),
    ("Análisis de incidencia en la caída de producción", menu_incidencia),
    ("Focos críticos", menu_focos_criticos),
    ("Búsqueda por región", menu_busqueda_por_region),
    ("Búsqueda por cultivo y campaña", menu_busqueda_por_cultivo_campania),
    ("Gestión de parámetros", menu_gestion_parametros),
    ("Gestión de estimaciones", menu_gestion_estimaciones)
]

OPCION_SALIR = str(len(OPCIONES) + 1)


def mostrar_menu_principal():

    anio_desde, anio_hasta = Campania.rango_cargado()

    # Encabezado
    print("\n" + "=" * ANCHO)
    print(NEGRITA + "MINISTERIO DE AGRICULTURA, GANADERÍA Y PESCA".center(ANCHO) + NORMAL)
    print("Estadística agrícola por cultivo, campaña, provincia y departamento".center(ANCHO))
    print(
        f"de la República Argentina | Campañas "
        f"{Campania.formatear_rango(anio_desde, anio_hasta)}".center(ANCHO)
    )
    print("=" * ANCHO)

    # Presentación del sistema
    print()
    texto_centrado(
        "El sistema contiene información estadística agrícola correspondiente "
        "a cultivos y campañas de la República Argentina, con datos de "
        "superficie sembrada, superficie cosechada, producción y rendimiento."
    )

    print()
    print(NEGRITA + "A partir de esta información permite detectar:".center(ANCHO) + NORMAL)

    for titulo_analisis, descripcion in DESCRIPCIONES:
        print()
        print(NEGRITA + ("* " + titulo_analisis).center(ANCHO) + NORMAL)
        texto_centrado(descripcion, ancho_texto=76, formato=CURSIVA + TENUE)

    # Opciones
    print()
    print("-" * ANCHO)
    print(NEGRITA + "INGRESE LA OPCIÓN QUE DESEA CONSULTAR".center(ANCHO) + NORMAL)
    print("-" * ANCHO)

    for numero, (texto, _) in enumerate(OPCIONES, start=1):
        print(f"{SANGRIA_MENU}{numero}. {texto}")

    print(f"{SANGRIA_MENU}{OPCION_SALIR}. Salir")
    print("-" * ANCHO)


def ejecutar_menu_principal():

    while True:

        mostrar_menu_principal()

        opcion = input(SANGRIA_MENU + "Seleccione una opción: ").strip()

        if opcion == OPCION_SALIR:
            print("\nPrograma finalizado.")
            return

        if opcion.isdigit() and 1 <= int(opcion) <= len(OPCIONES):
            limpiar_pantalla()
            OPCIONES[int(opcion) - 1][1]()
        else:
            limpiar_pantalla()
            print(f"\nOpción inválida. Ingrese una opción entre 1 y {OPCION_SALIR}.")
