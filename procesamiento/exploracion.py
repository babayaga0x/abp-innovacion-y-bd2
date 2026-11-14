# ============================================================
# EXPLORACIÓN: FILTROS, AGRUPAMIENTOS, DESCRIBE Y NUMPY
# ============================================================
# Operaciones generales sobre los DataFrames antes de responder
# las preguntas de análisis:
#
#   - Filtros y agrupamiento (groupby) para ubicar el peso de
#     cada región y de los cultivos principales.
#   - Estadísticas descriptivas con describe() y su lectura.
#   - Operaciones con NumPy sobre datos numéricos.
# ============================================================

import numpy as np
import pandas as pd


CULTIVOS_PRINCIPALES = ["soja", "maíz", "trigo", "girasol"]


# ============================================================
# FILTROS Y AGRUPAMIENTO
# ============================================================

def participacion_por_region(estimaciones):
    """
    Filtro 1: cultivos principales (soja, maíz, trigo, girasol).
    Filtro 2: última campaña disponible.
    Agrupamiento: producción por región.
    """

    ultima_campania = estimaciones["anio_inicio"].max()

    filtro_cultivos = estimaciones["cultivo"].isin(CULTIVOS_PRINCIPALES)
    filtro_campania = estimaciones["anio_inicio"] == ultima_campania

    seleccion = estimaciones[filtro_cultivos & filtro_campania]

    tabla = (
        seleccion
        .groupby("region")
        .agg(
            provincias=("provincia", "nunique"),
            produccion_tm=("produccion_tm", "sum"),
            superficie_cosechada_ha=("superficie_cosechada_ha", "sum")
        )
        .sort_values("produccion_tm", ascending=False)
    )

    tabla["participacion_pct"] = tabla["produccion_tm"] / tabla["produccion_tm"].sum() * 100

    # Rendimiento recalculado: producción total / superficie cosechada total
    tabla["rendimiento_kgxha"] = (
        tabla["produccion_tm"] * 1000 / tabla["superficie_cosechada_ha"]
    )

    peso_principales = (
        seleccion["produccion_tm"].sum()
        / estimaciones.loc[filtro_campania, "produccion_tm"].sum()
        * 100
    )

    return tabla, ultima_campania, peso_principales


def produccion_nacional_por_campania(estimaciones):

    tabla = (
        estimaciones
        .groupby(["anio_inicio", "campania"], as_index=False)
        [["superficie_sembrada_ha", "superficie_cosechada_ha", "produccion_tm"]]
        .sum()
    )

    tabla["variacion_produccion_pct"] = tabla["produccion_tm"].pct_change() * 100

    return tabla


# ============================================================
# ESTADÍSTICAS DESCRIPTIVAS
# ============================================================

COLUMNAS_DESCRIBE = [
    "superficie_sembrada_ha",
    "superficie_cosechada_ha",
    "produccion_tm",
    "rendimiento_kgxha",
    "porcentaje_cosechado"
]


def estadisticas_descriptivas(estimaciones):

    descripcion = estimaciones[COLUMNAS_DESCRIBE].describe()

    # Asimetría: cuántas veces la media supera a la mediana
    media_sobre_mediana = descripcion.loc["mean"] / descripcion.loc["50%"]

    cosechado = estimaciones["porcentaje_cosechado"].dropna()

    lectura = {
        "registros": int(descripcion.loc["count", "produccion_tm"]),
        "produccion_media": descripcion.loc["mean", "produccion_tm"],
        "produccion_mediana": descripcion.loc["50%", "produccion_tm"],
        "produccion_media_sobre_mediana": media_sobre_mediana["produccion_tm"],
        "produccion_max": descripcion.loc["max", "produccion_tm"],
        "sembrada_media_sobre_mediana": media_sobre_mediana["superficie_sembrada_ha"],
        "rendimiento_min": descripcion.loc["min", "rendimiento_kgxha"],
        "rendimiento_max": descripcion.loc["max", "rendimiento_kgxha"],
        "cosechado_mediana": descripcion.loc["50%", "porcentaje_cosechado"],
        "cosechado_q1": descripcion.loc["25%", "porcentaje_cosechado"],
        "cosechado_menor_80_pct": (cosechado < 80).mean() * 100,
        "sin_cosecha": int((estimaciones["superficie_cosechada_ha"] == 0).sum())
    }

    return descripcion, lectura


# ============================================================
# OPERACIONES CON NUMPY
# ============================================================

def rendimiento_simple_vs_ponderado(estimaciones, campania_anio):
    """
    Compara, por cultivo principal, el promedio simple de los
    rendimientos provinciales (np.mean) con el rendimiento
    ponderado por superficie cosechada (np.average), que es
    equivalente a producción total / superficie cosechada total.
    """

    filas = []

    for cultivo in CULTIVOS_PRINCIPALES:

        datos = estimaciones[
            (estimaciones["cultivo"] == cultivo)
            & (estimaciones["anio_inicio"] == campania_anio)
            & (estimaciones["superficie_cosechada_ha"] > 0)
        ]

        rendimientos = datos["rendimiento_kgxha"].to_numpy()
        superficies = datos["superficie_cosechada_ha"].to_numpy()

        simple = np.mean(rendimientos)
        ponderado = np.average(rendimientos, weights=superficies)

        filas.append({
            "cultivo": cultivo,
            "provincias": len(datos),
            "promedio_simple": simple,
            "promedio_ponderado": ponderado,
            "diferencia_pct": (simple / ponderado - 1) * 100
        })

    return pd.DataFrame(filas).set_index("cultivo")


def percentiles_cosechado(estimaciones):

    valores = estimaciones["porcentaje_cosechado"].dropna().to_numpy()
    niveles = np.array([10, 25, 50, 75, 90])

    return pd.Series(np.percentile(valores, niveles), index=[f"P{n}" for n in niveles])


def semaforo_no_cosechado(analisis, umbral):
    """
    Clasifica cada cultivo + campaña + región con np.select:
    verde (hasta 10 %), amarillo (hasta el umbral) y rojo
    (por encima del umbral, situación desfavorable 1).
    """

    porcentaje = analisis["porcentaje_no_cosechado"].to_numpy()

    categorias = np.select(
        [porcentaje <= 10, porcentaje <= umbral, porcentaje > umbral],
        ["verde", "amarillo", "rojo"],
        default="sin dato"
    )

    return pd.Series(categorias).value_counts().reindex(
        ["verde", "amarillo", "rojo", "sin dato"], fill_value=0
    )
