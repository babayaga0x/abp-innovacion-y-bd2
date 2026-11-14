# ============================================================
# CARGA DE DATOS DESDE MYSQL A DATAFRAMES DE PANDAS
# ============================================================
# Se cargan cuatro DataFrames:
#
#   estimaciones  una fila por cultivo + campaña + provincia
#                 (estimaciones activas del modelo normalizado)
#   analisis      una fila por cultivo + campaña + región, con
#                 los resultados de las situaciones 1, 2 y 3
#   rachas        una fila por racha de caída sostenida (3.b)
#   focos         la VIEW vw_foco_critico
#
# Las columnas DECIMAL de MySQL llegan como objetos Decimal;
# se convierten a float para operar con pandas y NumPy.
# ============================================================

import pandas as pd

from db.conexion import obtener_conexion
from modelos.parametro import ParametroAnalisis


def a_dataframe(sql, parametros=None):
    """Ejecuta una consulta y devuelve el resultado como DataFrame."""

    cursor = obtener_conexion().cursor()

    try:
        cursor.execute(sql, parametros)
        columnas = [descripcion[0] for descripcion in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=columnas)

    finally:
        cursor.close()


def convertir_a_float(df, columnas):
    df[columnas] = df[columnas].astype(float)
    return df


# ============================================================
# ESTIMACIONES (cultivo + campaña + provincia)
# ============================================================

def cargar_estimaciones():

    df = a_dataframe("""
        SELECT
            r.region_nombre AS region,
            p.provincia_nombre AS provincia,
            c.cultivo_nombre AS cultivo,
            ca.campania,
            ca.anio_inicio,
            e.superficie_sembrada_ha,
            e.superficie_cosechada_ha,
            e.produccion_tm,
            e.rendimiento_kgxha,
            e.porcentaje_cosechado

        FROM estimacion e

        JOIN region r ON e.region_id = r.region_id
        JOIN provincia p ON e.provincia_id = p.provincia_id
        JOIN cultivo c ON e.cultivo_id = c.cultivo_id
        JOIN campania ca ON e.campania_id = ca.campania_id

        WHERE e.activa = 'SI'
    """)

    return convertir_a_float(df, [
        "superficie_sembrada_ha",
        "superficie_cosechada_ha",
        "produccion_tm",
        "rendimiento_kgxha",
        "porcentaje_cosechado"
    ])


# ============================================================
# ANÁLISIS REGIONAL (cultivo + campaña + región)
# ============================================================

def cargar_analisis():

    df = a_dataframe("""
        SELECT
            ar.analisis_id,
            r.region_nombre AS region,
            c.cultivo_nombre AS cultivo,
            ca.campania,
            ca.anio_inicio,

            s1.superficie_sembrada_ha,
            s1.superficie_cosechada_ha,
            s1.superficie_no_cosechada_ha,
            s1.porcentaje_no_cosechado,
            s1.es_desfavorable AS s1,

            s2.rendimiento_regional_kgxha,
            s2.rendimiento_nacional_kgxha,
            s2.diferencia_rendimiento_kgxha,
            s2.es_desfavorable AS s2,

            s3.produccion_actual_tm AS produccion_tm,
            s3.produccion_anterior_tm,
            s3.variacion_produccion_pct,
            s3.caidas_consecutivas,
            s3.es_desfavorable AS s3

        FROM analisis_regional ar

        JOIN region r ON ar.region_id = r.region_id
        JOIN cultivo c ON ar.cultivo_id = c.cultivo_id
        JOIN campania ca ON ar.campania_id = ca.campania_id

        JOIN situacion_desfavorable_1 s1 ON ar.analisis_id = s1.analisis_id
        JOIN situacion_desfavorable_2 s2 ON ar.analisis_id = s2.analisis_id
        JOIN situacion_desfavorable_3 s3 ON ar.analisis_id = s3.analisis_id
    """)

    return convertir_a_float(df, [
        "superficie_sembrada_ha",
        "superficie_cosechada_ha",
        "superficie_no_cosechada_ha",
        "porcentaje_no_cosechado",
        "rendimiento_regional_kgxha",
        "rendimiento_nacional_kgxha",
        "diferencia_rendimiento_kgxha",
        "produccion_tm",
        "produccion_anterior_tm",
        "variacion_produccion_pct"
    ])


# ============================================================
# RACHAS DE CAÍDA SOSTENIDA (situación 3.b)
# ============================================================

def cargar_rachas():

    return a_dataframe("""
        SELECT
            r.region_nombre AS region,
            c.cultivo_nombre AS cultivo,
            ca_ini.campania AS campania_inicio,
            ca_ini.anio_inicio AS anio_inicio,
            ca_fin.campania AS campania_fin,
            ca_fin.anio_inicio AS anio_fin,
            s3b.cantidad_caidas_produccion,
            s3b.cantidad_caidas_superficie,
            s3b.cantidad_caidas_rendimiento,
            s3b.conclusion

        FROM situacion_desfavorable_3b s3b

        JOIN region r ON s3b.region_id = r.region_id
        JOIN cultivo c ON s3b.cultivo_id = c.cultivo_id
        JOIN analisis_regional ar_ini ON s3b.analisis_id_inicio = ar_ini.analisis_id
        JOIN campania ca_ini ON ar_ini.campania_id = ca_ini.campania_id
        JOIN analisis_regional ar_fin ON s3b.analisis_id_fin = ar_fin.analisis_id
        JOIN campania ca_fin ON ar_fin.campania_id = ca_fin.campania_id

        ORDER BY r.region_nombre, c.cultivo_nombre, ca_ini.anio_inicio
    """)


# ============================================================
# FOCOS CRÍTICOS (VIEW)
# ============================================================

def cargar_focos():

    df = a_dataframe("SELECT * FROM vw_foco_critico ORDER BY region, cultivo, campania")

    return convertir_a_float(df, [
        "porcentaje_no_cosechado",
        "rendimiento_regional_kgxha",
        "rendimiento_nacional_kgxha",
        "produccion_actual_tm",
        "produccion_anterior_tm",
        "variacion_produccion_pct"
    ])


# ============================================================
# TODO JUNTO
# ============================================================

def cargar_datos():

    return {
        "estimaciones": cargar_estimaciones(),
        "analisis": cargar_analisis(),
        "rachas": cargar_rachas(),
        "focos": cargar_focos(),
        "umbral_no_cosechado": float(
            ParametroAnalisis.valor_de("umbral_no_cosechado")
        )
    }
