# ============================================================
# MENÚS DE ANÁLISIS (opciones 1 a 5 del menú principal)
# ============================================================
# Cada pantalla obtiene objetos de las clases de
# modelos/situaciones.py y los muestra en tablas.
# ============================================================

from modelos.dimensiones import Region, Cultivo
from modelos.parametro import ParametroAnalisis
from modelos.situaciones import (
    SituacionDesfavorable1,
    SituacionDesfavorable2,
    SituacionDesfavorable3,
    SituacionDesfavorable3B,
    FocoCritico
)
from ui.consola import (
    limpiar_pantalla,
    pausar,
    titulo,
    linea,
    miles,
    porcentaje,
    imprimir_tabla,
    formatear_fila,
    elegir_de_lista
)


def submenu(opciones):
    """
    Muestra un submenú numerado. opciones es una lista de
    (texto, función). La última opción siempre es "Volver".
    """

    while True:

        print("\n" + "=" * 60)
        print("Menú de consulta detallada:")
        print("=" * 60 + "\n")

        for numero, (texto, _) in enumerate(opciones, start=1):
            print(f"{numero}. {texto}")

        print(f"{len(opciones) + 1}. Volver al menú principal")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == str(len(opciones) + 1):
            limpiar_pantalla()
            return

        if opcion.isdigit() and 1 <= int(opcion) <= len(opciones):
            limpiar_pantalla()
            opciones[int(opcion) - 1][1]()
        else:
            print(f"\nOpción inválida. Ingrese una opción entre 1 y {len(opciones) + 1}.")


# ============================================================
# OPCIÓN 1 - SITUACIÓN DESFAVORABLE 1
# Superficie no cosechada
# ============================================================

def menu_situacion_1():

    limpiar_pantalla()

    casos, regiones, anio_desde, anio_hasta = SituacionDesfavorable1.resumen_general()
    umbral = ParametroAnalisis.valor_de("umbral_no_cosechado")

    print("\nRESUMEN GENERAL\n")
    print(f"Umbral vigente: superficie no cosechada mayor al {umbral:.0f} %")
    print("Casos desfavorables encontrados:", casos)
    print("Regiones afectadas:", regiones)

    if casos:
        print(
            f"Período de los casos: "
            f"{anio_desde}/{anio_desde + 1} - {anio_hasta}/{anio_hasta + 1}"
        )

    columnas = [
        ("REGIÓN", 18, "<"),
        ("CULTIVO", 20, "<"),
        ("CAMPAÑAS", 10, ">"),
        ("SEMBRADA", 16, ">"),
        ("NO COSECH.", 16, ">"),
        ("% NO COSECH.", 16, ">")
    ]

    filas = [
        (
            region,
            cultivo,
            campanias,
            miles(sembrada),
            miles(no_cosechada),
            porcentaje(pct)
        )
        for region, cultivo, campanias, sembrada, no_cosechada, pct
        in SituacionDesfavorable1.resumen_por_region_cultivo()
    ]

    imprimir_tabla(columnas, filas, "RESUMEN - SITUACIÓN DESFAVORABLE 1")

    submenu([
        ("Ver detalle por región", lambda: detalle_situacion_1_por("region")),
        ("Ver detalle por cultivo", lambda: detalle_situacion_1_por("cultivo")),
        ("Ver detalle por campaña", lambda: detalle_situacion_1_por("campania")),
        ("Ver todos los casos", detalle_situacion_1)
    ])


def detalle_situacion_1_por(dimension):

    nombres = {
        "region": ("REGIONES", "una región"),
        "cultivo": ("CULTIVOS", "un cultivo"),
        "campania": ("CAMPAÑAS", "una campaña")
    }

    encabezado, nombre = nombres[dimension]

    elegido = elegir_de_lista(
        SituacionDesfavorable1.contar_desfavorables_por(dimension),
        mostrar=lambda fila: f"{fila[0]:<20}{fila[1]} casos",
        encabezado=f"{encabezado} CON CASOS DESFAVORABLES",
        nombre=nombre
    )

    limpiar_pantalla()

    if elegido is not None:
        detalle_situacion_1(**{dimension: elegido[0]})


def detalle_situacion_1(region=None, cultivo=None, campania=None):
    """
    Detalle por campaña, con subtotales por región y cultivo
    (los subtotales se omiten si se filtró una sola campaña).
    """

    casos = SituacionDesfavorable1.listar_desfavorables(region, cultivo, campania)

    columnas = [
        ("REGIÓN", 18, "<"),
        ("CULTIVO", 20, "<"),
        ("CAMPAÑA", 14, "<"),
        ("SEMBRADA", 14, ">"),
        ("COSECHADA", 14, ">"),
        ("NO COSECH.", 14, ">"),
        ("% NO COSECH.", 14, ">")
    ]

    ancho = sum(columna[1] for columna in columnas)
    mostrar_subtotales = campania is None

    titulo("SITUACIÓN DESFAVORABLE 1 - SUPERFICIE NO COSECHADA", ancho)
    print(formatear_fila([c[0] for c in columnas], columnas))
    linea("-", ancho)

    def imprimir_subtotal(grupo, totales):

        sembrada, cosechada, no_cosechada = totales
        pct = no_cosechada / sembrada * 100 if sembrada else 0

        linea("-", ancho)
        # La etiqueta ocupa el ancho de región + cultivo + campaña
        columnas_subtotal = [("", 52, "<")] + columnas[3:]

        print(formatear_fila(
            (
                f"SUBTOTAL - {grupo[0]} / {grupo[1]}",
                miles(sembrada),
                miles(cosechada),
                miles(no_cosechada),
                porcentaje(pct)
            ),
            columnas_subtotal
        ))
        linea("-", ancho)

    grupo_actual = None
    totales = [0, 0, 0]

    for caso in casos:

        grupo = (
            caso.analisis.region.region_nombre,
            caso.analisis.cultivo.cultivo_nombre
        )

        if mostrar_subtotales and grupo_actual is not None and grupo != grupo_actual:
            imprimir_subtotal(grupo_actual, totales)
            totales = [0, 0, 0]

        grupo_actual = grupo

        print(formatear_fila(
            (
                grupo[0],
                grupo[1],
                caso.analisis.campania.campania,
                miles(caso.superficie_sembrada_ha),
                miles(caso.superficie_cosechada_ha),
                miles(caso.superficie_no_cosechada_ha),
                porcentaje(caso.porcentaje_no_cosechado)
            ),
            columnas
        ))

        totales[0] += float(caso.superficie_sembrada_ha)
        totales[1] += float(caso.superficie_cosechada_ha)
        totales[2] += float(caso.superficie_no_cosechada_ha)

    if mostrar_subtotales and grupo_actual is not None:
        imprimir_subtotal(grupo_actual, totales)
    else:
        linea("-", ancho)

    print("Casos desfavorables encontrados:", len(casos))

    pausar("Presione ENTER para volver al menú de consulta detallada...")
    limpiar_pantalla()


# ============================================================
# OPCIÓN 2 - SITUACIÓN DESFAVORABLE 2
# Rendimiento regional inferior al nacional
# ============================================================

def menu_situacion_2():

    limpiar_pantalla()

    columnas = [
        ("REGIÓN", 20, "<"),
        ("CASOS DESFAV.", 16, ">"),
        ("CASOS EVALUADOS", 18, ">"),
        ("% DESFAV.", 12, ">"),
        ("BRECHA PROM.", 16, ">")
    ]

    filas = []

    for region, desfavorables, evaluados, brecha in SituacionDesfavorable2.resumen_por_region():

        filas.append((
            region,
            int(desfavorables or 0),
            evaluados,
            porcentaje((desfavorables or 0) / evaluados * 100 if evaluados else None),
            porcentaje(brecha, 1)
        ))

    imprimir_tabla(columnas, filas, "RESUMEN - SITUACIÓN DESFAVORABLE 2 - BAJO RENDIMIENTO")

    print(
        "Brecha promedio: diferencia porcentual media entre el rendimiento "
        "regional y el nacional,\nen los casos desfavorables."
    )

    submenu([
        ("Ver detalle por región", detalle_situacion_2_por_region),
        ("Ver detalle por cultivo", detalle_situacion_2_por_cultivo)
    ])


def detalle_situacion_2_por_region():

    region = elegir_de_lista(Region.listar(), encabezado="REGIONES", nombre="una región")

    limpiar_pantalla()

    if region is not None:
        detalle_situacion_2(region=region.region_nombre)


def detalle_situacion_2_por_cultivo():

    cultivo = elegir_de_lista(Cultivo.listar(), encabezado="CULTIVOS", nombre="un cultivo")

    limpiar_pantalla()

    if cultivo is not None:
        detalle_situacion_2(cultivo=cultivo.cultivo_nombre)


def detalle_situacion_2(region=None, cultivo=None):

    casos = SituacionDesfavorable2.listar_desfavorables(region=region, cultivo=cultivo)

    columnas = [
        ("REGIÓN", 18, "<"),
        ("CULTIVO", 20, "<"),
        ("CAMPAÑA", 12, "<"),
        ("REND. REG.", 13, ">"),
        ("REND. NAC.", 13, ">"),
        ("DIFERENCIA", 13, ">"),
        ("BRECHA", 11, ">")
    ]

    filas = [
        (
            caso.analisis.region.region_nombre,
            caso.analisis.cultivo.cultivo_nombre,
            caso.analisis.campania.campania,
            miles(caso.rendimiento_regional_kgxha),
            miles(caso.rendimiento_nacional_kgxha),
            miles(caso.diferencia_rendimiento_kgxha),
            porcentaje(caso.brecha_pct, 1)
        )
        for caso in casos
    ]

    filtro = region or cultivo

    imprimir_tabla(
        columnas,
        filas,
        f"SITUACIÓN DESFAVORABLE 2 - {filtro} (rendimientos en kg/ha)"
    )

    print("Casos desfavorables encontrados:", len(casos))

    pausar("Presione ENTER para volver al menú de consulta detallada...")
    limpiar_pantalla()


# ============================================================
# OPCIÓN 3 - SITUACIÓN DESFAVORABLE 3
# Caída sostenida de la producción
# ============================================================

def menu_situacion_3():

    limpiar_pantalla()

    min_caidas = int(ParametroAnalisis.valor_de("min_caidas_consecutivas"))
    max_ausentes = int(ParametroAnalisis.valor_de("max_campanias_ausentes"))

    print("\nCRITERIO VIGENTE\n")
    print(f"Caídas consecutivas mínimas: {min_caidas}")
    print(f"Campañas ausentes toleradas dentro de una racha: {max_ausentes}")

    columnas = [
        ("REGIÓN", 20, "<"),
        ("CULTIVO", 22, "<"),
        ("CAMPAÑAS DESFAV.", 18, ">"),
        ("MÁX. CAÍDAS SEGUIDAS", 22, ">")
    ]

    filas = SituacionDesfavorable3.resumen_por_region_cultivo()

    imprimir_tabla(columnas, filas, "RESUMEN - SITUACIÓN DESFAVORABLE 3 - CAÍDA SOSTENIDA")

    print("Combinaciones región / cultivo afectadas:", len(filas))

    submenu([
        ("Ver detalle por región", detalle_situacion_3_por_region),
        ("Ver todos los casos", detalle_situacion_3)
    ])


def detalle_situacion_3_por_region():

    region = elegir_de_lista(Region.listar(), encabezado="REGIONES", nombre="una región")

    limpiar_pantalla()

    if region is not None:
        detalle_situacion_3(region=region.region_nombre)


def detalle_situacion_3(region=None):

    casos = SituacionDesfavorable3.listar_desfavorables(region=region)

    columnas = [
        ("REGIÓN", 18, "<"),
        ("CULTIVO", 20, "<"),
        ("CAMPAÑA", 12, "<"),
        ("PROD. ANTERIOR", 16, ">"),
        ("PROD. ACTUAL", 16, ">"),
        ("VARIACIÓN", 12, ">"),
        ("CAÍDAS", 8, ">")
    ]

    filas = [
        (
            caso.analisis.region.region_nombre,
            caso.analisis.cultivo.cultivo_nombre,
            caso.analisis.campania.campania,
            miles(caso.produccion_anterior_tm),
            miles(caso.produccion_actual_tm),
            porcentaje(caso.variacion_produccion_pct, 1),
            caso.caidas_consecutivas
        )
        for caso in casos
    ]

    imprimir_tabla(
        columnas,
        filas,
        "SITUACIÓN DESFAVORABLE 3 - CAMPAÑAS CON CAÍDA SOSTENIDA (producción en t)"
    )

    print("Casos desfavorables encontrados:", len(casos))

    pausar("Presione ENTER para volver al menú de consulta detallada...")
    limpiar_pantalla()


# ============================================================
# OPCIÓN 4 - ANÁLISIS DE INCIDENCIA (Situación 3.b)
# ============================================================

def menu_incidencia():

    limpiar_pantalla()

    resumen = SituacionDesfavorable3B.resumen_por_conclusion()
    total = sum(fila[1] for fila in resumen)

    columnas = [
        ("CONCLUSIÓN", 104, "<"),
        ("RACHAS", 10, ">"),
        ("%", 10, ">")
    ]

    filas = [
        (conclusion, rachas, porcentaje(rachas / total * 100 if total else None))
        for conclusion, rachas in resumen
    ]

    imprimir_tabla(columnas, filas, "ANÁLISIS DE INCIDENCIA EN LA CAÍDA DE PRODUCCIÓN")

    print("Rachas de caída sostenida analizadas:", total)
    print(
        "\nEn cada racha se cuenta en cuántos tramos cayó la superficie cosechada "
        "y en cuántos cayó\nel rendimiento; la variable con más caídas es la de "
        "mayor incidencia."
    )

    submenu([
        ("Ver rachas por región", detalle_incidencia_por_region),
        ("Ver todas las rachas", detalle_incidencia)
    ])


def detalle_incidencia_por_region():

    region = elegir_de_lista(Region.listar(), encabezado="REGIONES", nombre="una región")

    limpiar_pantalla()

    if region is not None:
        detalle_incidencia(region=region.region_nombre)


def detalle_incidencia(region=None):

    rachas = SituacionDesfavorable3B.listar(region=region)

    columnas = [
        ("REGIÓN", 18, "<"),
        ("CULTIVO", 18, "<"),
        ("DESDE", 11, "<"),
        ("HASTA", 11, "<"),
        ("C. PROD.", 9, ">"),
        ("C. SUP.", 9, ">"),
        ("C. REND.", 10, ">"),
        ("   MAYOR INCIDENCIA", 24, "<")
    ]

    filas = [
        (
            racha.region,
            racha.cultivo,
            racha.campania_inicio,
            racha.campania_fin,
            racha.cantidad_caidas_produccion,
            racha.cantidad_caidas_superficie,
            racha.cantidad_caidas_rendimiento,
            "   " + racha.conclusion_corta
        )
        for racha in rachas
    ]

    imprimir_tabla(columnas, filas, "RACHAS DE CAÍDA SOSTENIDA E INCIDENCIA")

    print("C. PROD / C. SUP / C. REND: tramos con caída de producción, "
          "superficie cosechada y rendimiento.")
    print("Rachas encontradas:", len(rachas))

    pausar("Presione ENTER para volver al menú de consulta detallada...")
    limpiar_pantalla()


# ============================================================
# OPCIÓN 5 - FOCOS CRÍTICOS (VIEW vw_foco_critico)
# ============================================================

def menu_focos_criticos():

    limpiar_pantalla()

    focos = FocoCritico.listar()

    if not focos:

        titulo("FOCOS CRÍTICOS", 120)
        print(
            "\nNo se detectaron casos en los que coincidan "
            "las tres situaciones desfavorables."
        )

    else:

        columnas = [
            ("REGIÓN", 18, "<"),
            ("CULTIVO", 20, "<"),
            ("CAMPAÑA", 14, "<"),
            ("% NO COSECH.", 14, ">"),
            ("REND. REG.", 14, ">"),
            ("REND. NAC.", 14, ">"),
            ("VAR. PROD.", 14, ">"),
            ("CAÍDAS", 10, ">")
        ]

        filas = [
            (
                foco.region,
                foco.cultivo,
                foco.campania,
                porcentaje(foco.porcentaje_no_cosechado),
                miles(foco.rendimiento_regional_kgxha),
                miles(foco.rendimiento_nacional_kgxha),
                porcentaje(foco.variacion_produccion_pct, 1),
                foco.caidas_consecutivas
            )
            for foco in focos
        ]

        imprimir_tabla(columnas, filas, "FOCOS CRÍTICOS")

        print("Focos críticos encontrados:", len(focos))

    pausar("Presione ENTER para volver al menú principal...")
    limpiar_pantalla()
