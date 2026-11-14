# ============================================================
# CÁLCULO DE LAS SITUACIONES DESFAVORABLES
# ============================================================
# Reconstruye las tablas de resultados a partir de las
# estimaciones activas y de los parámetros vigentes:
#
#   analisis_regional          combinaciones cultivo + campaña + región
#   situacion_desfavorable_1   superficie no cosechada
#   situacion_desfavorable_2   rendimiento regional vs nacional
#   situacion_desfavorable_3   caídas consecutivas de producción
#   situacion_desfavorable_3b  incidencia de superficie y rendimiento
#
# Se ejecuta al iniciar la aplicación, después de modificar un
# parámetro, después de una baja o reactivación de estimaciones
# y después de una actualización desde CSV. Todo el recálculo
# se confirma en una única transacción.
# ============================================================

from db.conexion import consultar, ejecutar, ejecutar_varios, confirmar, revertir
from modelos.parametro import ParametroAnalisis
from modelos.situaciones import (
    CONCLUSION_SUPERFICIE,
    CONCLUSION_RENDIMIENTO,
    CONCLUSION_AMBAS,
    CONCLUSION_NO_DETERMINADA
)


# ============================================================
# ANÁLISIS REGIONAL
# ============================================================
# Incorpora las combinaciones cultivo + campaña + región que
# todavía no existen. Las existentes se conservan para que sus
# analisis_id no cambien entre ejecuciones.
# ============================================================

def cargar_analisis_regional():

    ejecutar("""
        INSERT INTO analisis_regional
            (cultivo_id, campania_id, region_id)

        SELECT DISTINCT
            e.cultivo_id,
            e.campania_id,
            e.region_id

        FROM estimacion e

        WHERE NOT EXISTS (
            SELECT 1
            FROM analisis_regional ar
            WHERE ar.cultivo_id = e.cultivo_id
              AND ar.campania_id = e.campania_id
              AND ar.region_id = e.region_id
        )
    """)


# ============================================================
# SITUACIÓN DESFAVORABLE 1 - Superficie no cosechada
# ============================================================

def calcular_situacion_1(umbral_no_cosechado):

    ejecutar("""
        INSERT INTO situacion_desfavorable_1 (
            analisis_id,
            superficie_sembrada_ha,
            superficie_cosechada_ha,
            superficie_no_cosechada_ha,
            porcentaje_no_cosechado,
            es_desfavorable
        )

        SELECT
            ar.analisis_id,

            SUM(e.superficie_sembrada_ha),

            SUM(e.superficie_cosechada_ha),

            SUM(e.superficie_sembrada_ha)
                - SUM(e.superficie_cosechada_ha),

            CASE
                WHEN SUM(e.superficie_sembrada_ha) > 0
                THEN ROUND(
                    (
                        SUM(e.superficie_sembrada_ha)
                        - SUM(e.superficie_cosechada_ha)
                    )
                    / SUM(e.superficie_sembrada_ha) * 100,
                    2
                )
                ELSE NULL
            END,

            CASE
                WHEN SUM(e.superficie_sembrada_ha) > 0
                 AND (
                    (
                        SUM(e.superficie_sembrada_ha)
                        - SUM(e.superficie_cosechada_ha)
                    )
                    / SUM(e.superficie_sembrada_ha) * 100
                 ) > %s
                THEN 'SI'
                ELSE 'NO'
            END

        FROM analisis_regional ar

        JOIN estimacion e
            ON e.cultivo_id = ar.cultivo_id
            AND e.campania_id = ar.campania_id
            AND e.region_id = ar.region_id
            AND e.activa = 'SI'

        GROUP BY ar.analisis_id
    """, (umbral_no_cosechado,))


# ============================================================
# SITUACIÓN DESFAVORABLE 2 - Bajo rendimiento
# ============================================================
# Rendimiento regional vs rendimiento nacional del mismo
# cultivo y campaña. Ambos se recalculan como
# producción total × 1000 / superficie cosechada total.
# ============================================================

def calcular_situacion_2():

    ejecutar("""
        INSERT INTO situacion_desfavorable_2 (
            analisis_id,
            rendimiento_regional_kgxha,
            rendimiento_nacional_kgxha,
            diferencia_rendimiento_kgxha,
            es_desfavorable
        )

        SELECT
            ar.analisis_id,

            -- Rendimiento regional
            CASE
                WHEN SUM(CASE WHEN e.region_id = ar.region_id
                              THEN e.superficie_cosechada_ha ELSE 0 END) > 0
                THEN ROUND(
                    SUM(CASE WHEN e.region_id = ar.region_id
                             THEN e.produccion_tm ELSE 0 END) * 1000
                    /
                    SUM(CASE WHEN e.region_id = ar.region_id
                             THEN e.superficie_cosechada_ha ELSE 0 END),
                    2
                )
                ELSE NULL
            END,

            -- Rendimiento nacional
            CASE
                WHEN SUM(e.superficie_cosechada_ha) > 0
                THEN ROUND(
                    SUM(e.produccion_tm) * 1000
                    / SUM(e.superficie_cosechada_ha),
                    2
                )
                ELSE NULL
            END,

            -- Diferencia regional - nacional
            CASE
                WHEN SUM(CASE WHEN e.region_id = ar.region_id
                              THEN e.superficie_cosechada_ha ELSE 0 END) > 0
                 AND SUM(e.superficie_cosechada_ha) > 0
                THEN ROUND(
                    (
                        SUM(CASE WHEN e.region_id = ar.region_id
                                 THEN e.produccion_tm ELSE 0 END) * 1000
                        /
                        SUM(CASE WHEN e.region_id = ar.region_id
                                 THEN e.superficie_cosechada_ha ELSE 0 END)
                    )
                    -
                    (
                        SUM(e.produccion_tm) * 1000
                        / SUM(e.superficie_cosechada_ha)
                    ),
                    2
                )
                ELSE NULL
            END,

            -- Situación desfavorable
            CASE
                WHEN SUM(CASE WHEN e.region_id = ar.region_id
                              THEN e.superficie_cosechada_ha ELSE 0 END) = 0
                  OR SUM(e.superficie_cosechada_ha) = 0
                THEN NULL

                WHEN (
                        SUM(CASE WHEN e.region_id = ar.region_id
                                 THEN e.produccion_tm ELSE 0 END) * 1000
                        /
                        SUM(CASE WHEN e.region_id = ar.region_id
                                 THEN e.superficie_cosechada_ha ELSE 0 END)
                     )
                     <
                     (
                        SUM(e.produccion_tm) * 1000
                        / SUM(e.superficie_cosechada_ha)
                     )
                THEN 'SI'

                ELSE 'NO'
            END

        FROM analisis_regional ar

        JOIN estimacion e
            ON e.cultivo_id = ar.cultivo_id
            AND e.campania_id = ar.campania_id
            AND e.activa = 'SI'

        GROUP BY
            ar.analisis_id,
            ar.region_id
    """)


# ============================================================
# SITUACIÓN DESFAVORABLE 3 - Caídas consecutivas de producción
# ============================================================
# Criterio metodológico:
#
# - Se analiza cada cultivo y región cronológicamente.
#
# - Existe una caída cuando:
#       producción actual < producción anterior
#
# - Para considerar las caídas como parte de una misma racha
#   se toleran como máximo max_campanias_ausentes campañas
#   ausentes EN TOTAL dentro del tramo. Pueden estar juntas o
#   separadas.
#
# - Si la producción no vuelve a caer, la racha se reinicia.
#
# - Si las ausencias acumuladas superan la tolerancia, se
#   descarta la parte más antigua de la racha hasta volver a
#   cumplirla.
#
# - min_caidas_consecutivas o más caídas válidas:
#       Situación Desfavorable 3 = SI
# ============================================================

def obtener_produccion_regional():

    return consultar("""
        SELECT
            ar.analisis_id,
            ar.cultivo_id,
            ar.region_id,
            ca.anio_inicio,
            SUM(e.produccion_tm) AS produccion_tm

        FROM analisis_regional ar

        JOIN campania ca
            ON ca.campania_id = ar.campania_id

        JOIN estimacion e
            ON e.cultivo_id = ar.cultivo_id
            AND e.campania_id = ar.campania_id
            AND e.region_id = ar.region_id
            AND e.activa = 'SI'

        GROUP BY
            ar.analisis_id,
            ar.cultivo_id,
            ar.region_id,
            ca.anio_inicio

        ORDER BY
            ar.cultivo_id,
            ar.region_id,
            ca.anio_inicio
    """)


def calcular_caidas_consecutivas(filas_produccion, min_caidas, max_ausentes):
    """
    Recorre la producción ordenada por cultivo, región y año y
    devuelve una tupla por campaña, lista para insertar en
    situacion_desfavorable_3.
    """

    resultados = []

    cultivo_anterior = None
    region_anterior = None
    anio_anterior = None
    produccion_anterior = None

    # Campañas ausentes asociadas a cada caída de la racha actual
    ausencias_racha = []

    for analisis_id, cultivo_id, region_id, anio_inicio, produccion_actual in filas_produccion:

        hay_caida = None
        variacion_produccion_pct = None

        misma_serie = (
            cultivo_id == cultivo_anterior
            and region_id == region_anterior
        )

        if (
            misma_serie
            and produccion_actual is not None
            and produccion_anterior is not None
        ):

            # Cantidad de campañas sin datos entre ambos registros
            ausentes_entre_registros = max(
                anio_inicio - anio_anterior - 1,
                0
            )

            if produccion_anterior > 0:

                variacion_produccion_pct = round(
                    (float(produccion_actual) - float(produccion_anterior))
                    / float(produccion_anterior)
                    * 100,
                    2
                )

            if produccion_actual < produccion_anterior:

                hay_caida = "SI"

                ausencias_racha.append(ausentes_entre_registros)

                # Se descartan las caídas más antiguas hasta que
                # el tramo vuelva a cumplir la tolerancia.
                while ausencias_racha and sum(ausencias_racha) > max_ausentes:
                    ausencias_racha.pop(0)

            else:

                hay_caida = "NO"
                ausencias_racha = []

        else:

            # Primer registro de una serie cultivo + región
            ausencias_racha = []

        caidas_consecutivas = len(ausencias_racha)

        es_desfavorable = (
            "SI" if caidas_consecutivas >= min_caidas else "NO"
        )

        resultados.append(
            (
                analisis_id,
                produccion_actual,
                produccion_anterior if misma_serie else None,
                variacion_produccion_pct,
                hay_caida,
                caidas_consecutivas,
                es_desfavorable
            )
        )

        cultivo_anterior = cultivo_id
        region_anterior = region_id
        anio_anterior = anio_inicio
        produccion_anterior = produccion_actual

    return resultados


def calcular_situacion_3(min_caidas, max_ausentes):

    resultados = calcular_caidas_consecutivas(
        obtener_produccion_regional(),
        min_caidas,
        max_ausentes
    )

    ejecutar_varios("""
        INSERT INTO situacion_desfavorable_3 (
            analisis_id,
            produccion_actual_tm,
            produccion_anterior_tm,
            variacion_produccion_pct,
            hay_caida,
            caidas_consecutivas,
            es_desfavorable
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, resultados)


# ============================================================
# SITUACIÓN DESFAVORABLE 3.b - Incidencia en la caída
# ============================================================
# Dentro de cada racha de caída sostenida se cuentan los
# tramos con reducción de superficie cosechada y los tramos con
# disminución del rendimiento. La conclusión compara ambos
# conteos:
#
# 1. superficie > rendimiento → mayor incidencia de superficie.
# 2. rendimiento > superficie → mayor incidencia de rendimiento.
# 3. iguales y mayores que 0  → incidencia de ambas variables.
# 4. ambos en 0               → caída no determinada por ninguna.
# ============================================================

def identificar_rachas(min_caidas):
    """Agrupa las caídas detectadas en rachas de min_caidas o más."""

    filas_caidas = consultar("""
        SELECT
            s3.analisis_id,
            ar.cultivo_id,
            ar.region_id,
            ca.anio_inicio,
            s3.caidas_consecutivas
        FROM situacion_desfavorable_3 s3
        JOIN analisis_regional ar
            ON s3.analisis_id = ar.analisis_id
        JOIN campania ca
            ON ar.campania_id = ca.campania_id
        WHERE s3.hay_caida = 'SI'
        ORDER BY
            ar.cultivo_id,
            ar.region_id,
            ca.anio_inicio
    """)

    rachas = []
    racha_actual = []

    cultivo_anterior = None
    region_anterior = None
    numero_caida_anterior = None

    for fila in filas_caidas:

        cultivo_id = fila[1]
        region_id = fila[2]
        numero_caida = fila[4]

        continua_racha = (
            cultivo_id == cultivo_anterior
            and region_id == region_anterior
            and numero_caida_anterior is not None
            and numero_caida == numero_caida_anterior + 1
        )

        if numero_caida == 1:

            # Comienza una nueva racha
            if len(racha_actual) >= min_caidas:
                rachas.append(racha_actual)

            racha_actual = [fila]

        elif continua_racha:

            racha_actual.append(fila)

        else:

            # Se cortó la secuencia anterior
            if len(racha_actual) >= min_caidas:
                rachas.append(racha_actual)

            racha_actual = []

        cultivo_anterior = cultivo_id
        region_anterior = region_id
        numero_caida_anterior = numero_caida

    if len(racha_actual) >= min_caidas:
        rachas.append(racha_actual)

    return rachas


def obtener_metricas_por_analisis():
    """
    Superficie cosechada y rendimiento regional de cada análisis,
    y el análisis anterior de la misma serie cultivo + región.
    """

    filas = consultar("""
        SELECT
            ar.analisis_id,
            ar.cultivo_id,
            ar.region_id,
            s1.superficie_cosechada_ha,
            s2.rendimiento_regional_kgxha
        FROM analisis_regional ar
        JOIN campania ca
            ON ar.campania_id = ca.campania_id
        JOIN situacion_desfavorable_1 s1
            ON ar.analisis_id = s1.analisis_id
        JOIN situacion_desfavorable_2 s2
            ON ar.analisis_id = s2.analisis_id
        ORDER BY
            ar.cultivo_id,
            ar.region_id,
            ca.anio_inicio
    """)

    metricas = {}
    anterior_por_analisis = {}

    serie_anterior = None
    analisis_anterior = None

    for analisis_id, cultivo_id, region_id, superficie, rendimiento in filas:

        metricas[analisis_id] = {
            "superficie": superficie,
            "rendimiento": rendimiento
        }

        serie = (cultivo_id, region_id)

        anterior_por_analisis[analisis_id] = (
            analisis_anterior if serie == serie_anterior else None
        )

        serie_anterior = serie
        analisis_anterior = analisis_id

    return metricas, anterior_por_analisis


def disminuyo(actual, anterior):
    return actual is not None and anterior is not None and actual < anterior


def concluir(caidas_superficie, caidas_rendimiento):

    if caidas_superficie > caidas_rendimiento:
        return CONCLUSION_SUPERFICIE

    if caidas_rendimiento > caidas_superficie:
        return CONCLUSION_RENDIMIENTO

    if caidas_superficie > 0:
        return CONCLUSION_AMBAS

    return CONCLUSION_NO_DETERMINADA


def calcular_situacion_3b(min_caidas):

    rachas = identificar_rachas(min_caidas)
    metricas, anterior_por_analisis = obtener_metricas_por_analisis()

    resultados = []

    for racha in rachas:

        caidas_superficie = 0
        caidas_rendimiento = 0

        for fila_caida in racha:

            actual = metricas[fila_caida[0]]
            anterior = metricas[anterior_por_analisis[fila_caida[0]]]

            if disminuyo(actual["superficie"], anterior["superficie"]):
                caidas_superficie += 1

            if disminuyo(actual["rendimiento"], anterior["rendimiento"]):
                caidas_rendimiento += 1

        resultados.append(
            (
                racha[0][1],    # cultivo_id
                racha[0][2],    # region_id
                racha[0][0],    # primer analisis_id de la racha
                racha[-1][0],   # último analisis_id de la racha
                len(racha),
                caidas_superficie,
                caidas_rendimiento,
                concluir(caidas_superficie, caidas_rendimiento)
            )
        )

    ejecutar_varios("""
        INSERT INTO situacion_desfavorable_3b (
            cultivo_id,
            region_id,
            analisis_id_inicio,
            analisis_id_fin,
            cantidad_caidas_produccion,
            cantidad_caidas_superficie,
            cantidad_caidas_rendimiento,
            conclusion
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, resultados)


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

def recalcular_analisis():
    """
    Recalcula todas las situaciones desfavorables con los
    parámetros vigentes. Devuelve la cantidad de casos
    desfavorables de cada situación.
    """

    umbral = float(ParametroAnalisis.valor_de("umbral_no_cosechado"))
    min_caidas = int(ParametroAnalisis.valor_de("min_caidas_consecutivas"))
    max_ausentes = int(ParametroAnalisis.valor_de("max_campanias_ausentes"))

    try:

        cargar_analisis_regional()

        # Son resultados calculados: se reconstruyen completos
        for tabla in (
            "situacion_desfavorable_3b",
            "situacion_desfavorable_3",
            "situacion_desfavorable_2",
            "situacion_desfavorable_1"
        ):
            ejecutar(f"DELETE FROM {tabla}")

        calcular_situacion_1(umbral)
        calcular_situacion_2()
        calcular_situacion_3(min_caidas, max_ausentes)
        calcular_situacion_3b(min_caidas)

        confirmar()

    except Exception:

        revertir()
        raise

    return contar_casos_desfavorables()


def contar_casos_desfavorables():

    fila = consultar("""
        SELECT
            (SELECT COUNT(*) FROM situacion_desfavorable_1
             WHERE es_desfavorable = 'SI'),
            (SELECT COUNT(*) FROM situacion_desfavorable_2
             WHERE es_desfavorable = 'SI'),
            (SELECT COUNT(*) FROM situacion_desfavorable_3
             WHERE es_desfavorable = 'SI'),
            (SELECT COUNT(*) FROM situacion_desfavorable_3b),
            (SELECT COUNT(*) FROM vw_foco_critico)
    """)[0]

    return {
        "situacion_1": fila[0],
        "situacion_2": fila[1],
        "situacion_3": fila[2],
        "rachas_3b": fila[3],
        "focos_criticos": fila[4]
    }
