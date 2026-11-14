# ============================================================
# RESPUESTA A LAS 5 PREGUNTAS DE ANÁLISIS (Primera Entrega)
# ============================================================
# Período: campañas 2015/2016 a la última cargada.
#
#   P1  ¿Qué regiones presentan una tasa de superficie no
#       cosechada superior al 20 %, y en qué cultivos y campañas
#       se concentra esta situación?
#   P2  ¿Qué región presenta rendimientos inferiores al
#       rendimiento nacional del mismo cultivo y campaña?
#   P3  ¿Qué regiones acumulan 3 o más caídas consecutivas de
#       producción, discriminadas por cultivo?
#   P4  En cada caída de producción detectada, ¿tuvo mayor
#       incidencia la reducción de la superficie cosechada, la
#       disminución del rendimiento o ambas variables?
#   P5  ¿Qué regiones concentran múltiples comportamientos
#       desfavorables simultáneos?
#
# Cada función devuelve una Respuesta con la operación
# utilizada, el resultado, la conclusión y las tablas de
# detalle. Esos campos alimentan la tabla de trazabilidad.
# ============================================================

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from modelos.situaciones import CONCLUSIONES_CORTAS


# Cultivos que se siembran mayormente para pastoreo o forraje:
# su superficie no cosechada no implica una pérdida productiva.
FORRAJEROS = ["avena", "centeno", "mijo"]


@dataclass
class Respuesta:
    numero: int
    pregunta: str
    operacion: str
    resultado: str
    conclusion: str
    tablas: dict = field(default_factory=dict)
    datos: dict = field(default_factory=dict)


def pct(valor, decimales=0):
    return f"{valor:.{decimales}f} %".replace(".", ",")


def millones(valor, decimales=1):
    return f"{valor / 1e6:.{decimales}f}".replace(".", ",")


# ============================================================
# P1 - SUPERFICIE NO COSECHADA
# ============================================================

def pregunta_1(datos):

    estimaciones = datos["estimaciones"]
    analisis = datos["analisis"]
    umbral = datos["umbral_no_cosechado"]

    # Se recalcula la regla de la situación 1 en pandas a partir
    # de las estimaciones, y se contrasta con el resultado SQL.
    combinaciones = (
        estimaciones
        .groupby(["region", "cultivo", "campania"], as_index=False)
        [["superficie_sembrada_ha", "superficie_cosechada_ha"]]
        .sum()
    )

    combinaciones = combinaciones[combinaciones["superficie_sembrada_ha"] > 0]

    combinaciones["superficie_no_cosechada_ha"] = (
        combinaciones["superficie_sembrada_ha"]
        - combinaciones["superficie_cosechada_ha"]
    )

    combinaciones["porcentaje_no_cosechado"] = (
        combinaciones["superficie_no_cosechada_ha"]
        / combinaciones["superficie_sembrada_ha"]
        * 100
    )

    # Filtro 1: casos por encima del umbral
    desfavorables = combinaciones[combinaciones["porcentaje_no_cosechado"] > umbral]

    casos_sql = int((analisis["s1"] == "SI").sum())

    # Agrupamiento por región
    por_region = (
        desfavorables
        .groupby("region")
        .agg(
            casos=("cultivo", "size"),
            cultivos=("cultivo", "nunique"),
            no_cosechada_ha=("superficie_no_cosechada_ha", "sum")
        )
    )

    por_region["casos_evaluados"] = combinaciones.groupby("region").size()
    por_region["casos_pct"] = por_region["casos"] / por_region["casos_evaluados"] * 100
    por_region = por_region.sort_values("casos", ascending=False)

    # Agrupamiento por cultivo
    por_cultivo = (
        desfavorables
        .groupby("cultivo")
        .agg(
            casos=("region", "size"),
            regiones=("region", "nunique"),
            campanias=("campania", "nunique"),
            no_cosechada_ha=("superficie_no_cosechada_ha", "sum")
        )
        .sort_values("no_cosechada_ha", ascending=False)
    )

    por_cultivo["forrajero"] = np.where(por_cultivo.index.isin(FORRAJEROS), "SI", "NO")
    por_cultivo["participacion_pct"] = (
        por_cultivo["no_cosechada_ha"] / por_cultivo["no_cosechada_ha"].sum() * 100
    )

    participacion_forrajeros = por_cultivo.loc[
        por_cultivo["forrajero"] == "SI", "participacion_pct"
    ].sum()

    # Filtro 2: se excluyen los cultivos forrajeros
    sin_forrajeros = desfavorables[~desfavorables["cultivo"].isin(FORRAJEROS)]

    sin_forrajeros_por_cultivo = (
        sin_forrajeros
        .groupby("cultivo")
        .agg(
            casos=("region", "size"),
            no_cosechada_ha=("superficie_no_cosechada_ha", "sum")
        )
        .sort_values("no_cosechada_ha", ascending=False)
    )

    sin_forrajeros_por_region = (
        sin_forrajeros
        .groupby("region")
        .agg(
            casos=("cultivo", "size"),
            no_cosechada_ha=("superficie_no_cosechada_ha", "sum")
        )
        .sort_values("no_cosechada_ha", ascending=False)
    )

    region_top = por_region.index[0]
    region_top_pct = por_region["casos_pct"].sort_values(ascending=False)
    top_cultivos = por_cultivo.index[:3].tolist()
    cultivo_sin_forraje = sin_forrajeros_por_cultivo.index[0]
    region_sin_forraje = sin_forrajeros_por_region.index[0]

    resultado = (
        f"{len(desfavorables)} casos sobre {len(combinaciones)} combinaciones "
        f"cultivo-campaña-región ({pct(len(desfavorables) / len(combinaciones) * 100)}), "
        f"en las {por_region.shape[0]} regiones. Más casos: {region_top} "
        f"({por_region.loc[region_top, 'casos']}); mayor proporción: "
        f"{region_top_pct.index[0]} ({pct(region_top_pct.iloc[0])} de sus combinaciones). "
        f"Cultivos con más superficie no cosechada: {', '.join(top_cultivos)}."
    )

    conclusion = (
        f"El {pct(participacion_forrajeros)} de la superficie no cosechada en casos "
        f"desfavorables es de cultivos forrajeros ({', '.join(FORRAJEROS)}), que se "
        f"destinan mayormente a pastoreo: no es una pérdida. Sin ellos quedan "
        f"{len(sin_forrajeros)} casos, liderados por {cultivo_sin_forraje} y por la "
        f"región {region_sin_forraje}."
    )

    return Respuesta(
        numero=1,
        pregunta=(
            "¿Qué regiones presentan una tasa de superficie no cosechada superior "
            f"al {umbral:.0f} %, y en qué cultivos y campañas se concentra?"
        ),
        operacion=(
            "groupby(región, cultivo, campaña).sum(); filtro % no cosechado > umbral; "
            "groupby(región) y groupby(cultivo); filtro sin forrajeros (isin); np.where"
        ),
        resultado=resultado,
        conclusion=conclusion,
        tablas={
            "p1_por_region": por_region,
            "p1_por_cultivo": por_cultivo,
            "p1_sin_forrajeros_por_cultivo": sin_forrajeros_por_cultivo,
            "p1_sin_forrajeros_por_region": sin_forrajeros_por_region
        },
        datos={
            "casos_pandas": len(desfavorables),
            "casos_sql": casos_sql,
            "participacion_forrajeros": participacion_forrajeros
        }
    )


# ============================================================
# P2 - BAJO RENDIMIENTO
# ============================================================

def pregunta_2(datos):

    estimaciones = datos["estimaciones"]
    analisis = datos["analisis"]

    # Recalculo en pandas: rendimiento regional y nacional como
    # producción total × 1000 / superficie cosechada total.
    regional = (
        estimaciones
        .groupby(["region", "cultivo", "campania"])
        [["produccion_tm", "superficie_cosechada_ha"]]
        .sum()
    )

    nacional = (
        estimaciones
        .groupby(["cultivo", "campania"])
        [["produccion_tm", "superficie_cosechada_ha"]]
        .sum()
    )

    regional["rendimiento_regional"] = (
        regional["produccion_tm"] * 1000 / regional["superficie_cosechada_ha"]
    )

    nacional["rendimiento_nacional"] = (
        nacional["produccion_tm"] * 1000 / nacional["superficie_cosechada_ha"]
    )

    comparacion = regional.join(nacional["rendimiento_nacional"], on=["cultivo", "campania"])
    comparacion = comparacion.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["rendimiento_regional", "rendimiento_nacional"]
    )

    casos_pandas = int(
        (comparacion["rendimiento_regional"] < comparacion["rendimiento_nacional"]).sum()
    )

    casos_sql = int((analisis["s2"] == "SI").sum())

    # Análisis por región sobre los resultados de la situación 2
    evaluados = analisis[analisis["s2"].notna()].copy()

    evaluados["brecha_pct"] = (
        evaluados["rendimiento_regional_kgxha"]
        / evaluados["rendimiento_nacional_kgxha"]
        - 1
    ) * 100

    produccion_region = analisis.groupby("region")["produccion_tm"].sum()

    por_region = (
        evaluados
        .groupby("region")
        .agg(
            casos_evaluados=("s2", "size"),
            casos_desfavorables=("s2", lambda serie: (serie == "SI").sum())
        )
    )

    por_region["desfavorables_pct"] = (
        por_region["casos_desfavorables"] / por_region["casos_evaluados"] * 100
    )

    por_region["brecha_mediana_pct"] = (
        evaluados[evaluados["s2"] == "SI"].groupby("region")["brecha_pct"].median()
    )

    por_region["participacion_produccion_pct"] = (
        produccion_region / produccion_region.sum() * 100
    )

    por_region = por_region.sort_values("desfavorables_pct", ascending=False)

    # Cultivos más afectados dentro de la región con mayor proporción
    region_top = por_region.index[0]

    cultivos_region_top = (
        evaluados[(evaluados["region"] == region_top) & (evaluados["s2"] == "SI")]
        .groupby("cultivo")
        .agg(campanias=("campania", "size"), brecha_mediana_pct=("brecha_pct", "median"))
        .sort_values(["campanias", "brecha_mediana_pct"], ascending=[False, True])
    )

    region_menor = por_region.index[-1]
    peso_menor = por_region.loc[region_menor, "participacion_produccion_pct"]
    resto = por_region.drop(region_menor)

    resultado = (
        f"{casos_sql} casos con rendimiento regional inferior al nacional. "
        + "; ".join(
            f"{region} {pct(fila.desfavorables_pct)}"
            for region, fila in por_region.iterrows()
        )
        + f" de sus casos. Brecha mediana en {region_top}: "
        f"{pct(por_region.loc[region_top, 'brecha_mediana_pct'])}."
    )

    conclusion = (
        f"La región con más bajo rendimiento relativo es {region_top}. Fuera del "
        f"{region_menor}, todas las regiones quedan debajo del promedio nacional en "
        f"{pct(resto['desfavorables_pct'].min())} a "
        f"{pct(resto['desfavorables_pct'].max())} de los casos; el {region_menor} solo en "
        f"{pct(por_region.loc[region_menor, 'desfavorables_pct'])}. Como el "
        f"{region_menor} aporta el {pct(peso_menor)} de la producción, el rendimiento "
        f"nacional es casi el suyo: la brecha es estructural, no un evento puntual."
    )

    return Respuesta(
        numero=2,
        pregunta=(
            "¿Qué región presenta rendimientos inferiores al rendimiento nacional "
            "del mismo cultivo y campaña?"
        ),
        operacion=(
            "groupby(región, cultivo, campaña) y groupby(cultivo, campaña); join; "
            "filtro s2 no nulo; groupby(región).agg(size, sum, median)"
        ),
        resultado=resultado,
        conclusion=conclusion,
        tablas={
            "p2_por_region": por_region,
            f"p2_cultivos_{region_top}": cultivos_region_top
        },
        datos={"casos_pandas": casos_pandas, "casos_sql": casos_sql}
    )


# ============================================================
# P3 - CAÍDA SOSTENIDA DE LA PRODUCCIÓN
# ============================================================

def pregunta_3(datos):

    analisis = datos["analisis"]
    rachas = datos["rachas"]

    series_totales = analisis.groupby(["region", "cultivo"]).ngroups

    por_region = (
        rachas
        .groupby("region")
        .agg(
            rachas=("cultivo", "size"),
            cultivos=("cultivo", lambda serie: ", ".join(sorted(serie.unique()))),
            max_caidas=("cantidad_caidas_produccion", "max")
        )
        .sort_values("rachas", ascending=False)
    )

    detalle = rachas[[
        "region",
        "cultivo",
        "campania_inicio",
        "campania_fin",
        "cantidad_caidas_produccion"
    ]]

    cultivos_frecuentes = rachas["cultivo"].value_counts()
    cultivo_frecuente = cultivos_frecuentes.index[0]
    regiones_cultivo_frecuente = rachas.loc[
        rachas["cultivo"] == cultivo_frecuente, "region"
    ].nunique()

    regiones_top = por_region[por_region["rachas"] == por_region["rachas"].max()].index.tolist()

    resultado = (
        f"{len(rachas)} rachas de 3 o más caídas consecutivas en "
        f"{rachas.groupby(['region', 'cultivo']).ngroups} combinaciones región-cultivo. "
        + "; ".join(
            f"{region}: {fila.rachas} ({fila.cultivos})"
            for region, fila in por_region.iterrows()
        )
        + "."
    )

    conclusion = (
        f"Es un fenómeno acotado: afecta a {len(rachas)} de {series_totales} series "
        f"región-cultivo ({pct(len(rachas) / series_totales * 100)}). "
        f"{' y '.join(regiones_top)} {'concentra' if len(regiones_top) == 1 else 'concentran'} "
        f"más rachas. {cultivo_frecuente.capitalize()} "
        f"tiene rachas en {regiones_cultivo_frecuente} regiones distintas: es un patrón del "
        f"cultivo que se repite en varias zonas, no un problema de una sola región."
    )

    return Respuesta(
        numero=3,
        pregunta=(
            "¿Qué regiones acumulan 3 o más caídas consecutivas de producción, "
            "discriminadas por cultivo?"
        ),
        operacion=(
            "groupby(región).agg(size, unique, max) sobre las rachas; "
            "value_counts() de cultivos; ngroups"
        ),
        resultado=resultado,
        conclusion=conclusion,
        tablas={"p3_por_region": por_region, "p3_rachas": detalle}
    )


# ============================================================
# P4 - INCIDENCIA DE SUPERFICIE Y RENDIMIENTO
# ============================================================
# Además del criterio por conteo de la situación 3.b, se mide
# la magnitud con una descomposición logarítmica (NumPy):
#
#   producción = superficie cosechada × rendimiento / 1000
#   ln(P1/P0) = ln(S1/S0) + ln(R1/R0)
#
# La proporción ln(S1/S0) / ln(P1/P0) es la parte de la caída
# explicada por la superficie; el resto, por el rendimiento.
# ============================================================

def descomponer_caida(produccion, superficie, rendimiento):
    """
    Recibe arreglos [inicial, final] y devuelve el aporte (%) de
    superficie y de rendimiento a la variación de producción.
    """

    variacion_produccion = np.log(produccion[1] / produccion[0])
    variacion_superficie = np.log(superficie[1] / superficie[0])
    variacion_rendimiento = np.log(rendimiento[1] / rendimiento[0])

    return (
        variacion_superficie / variacion_produccion * 100,
        variacion_rendimiento / variacion_produccion * 100,
        (np.exp(variacion_produccion) - 1) * 100
    )


def descomposicion_rachas(analisis, rachas):

    filas = []

    for racha in rachas.itertuples():

        serie = analisis[
            (analisis["region"] == racha.region)
            & (analisis["cultivo"] == racha.cultivo)
        ].sort_values("anio_inicio")

        # Base: última campaña con datos antes del inicio de la racha
        anteriores = serie[serie["anio_inicio"] < racha.anio_inicio]
        final = serie[serie["anio_inicio"] == racha.anio_fin]

        if anteriores.empty or final.empty:
            continue

        extremos = pd.concat([anteriores.iloc[[-1]], final])

        produccion = extremos["produccion_tm"].to_numpy()
        superficie = extremos["superficie_cosechada_ha"].to_numpy()
        rendimiento = extremos["rendimiento_regional_kgxha"].to_numpy()

        if np.any(produccion <= 0) or np.any(superficie <= 0) or np.any(rendimiento <= 0):
            continue

        aporte_superficie, aporte_rendimiento, variacion = descomponer_caida(
            produccion, superficie, rendimiento
        )

        filas.append({
            "region": racha.region,
            "cultivo": racha.cultivo,
            "desde": anteriores.iloc[-1]["campania"],
            "hasta": racha.campania_fin,
            "variacion_produccion_pct": variacion,
            "aporte_superficie_pct": aporte_superficie,
            "aporte_rendimiento_pct": aporte_rendimiento,
            "conclusion_conteo": CONCLUSIONES_CORTAS.get(racha.conclusion, racha.conclusion)
        })

    tabla = pd.DataFrame(filas)

    tabla["dominante_magnitud"] = np.where(
        tabla["aporte_superficie_pct"] > 50,
        "Superficie cosechada",
        "Rendimiento"
    )

    return tabla


def descomposicion_campania(estimaciones, anio):
    """Descompone por región la variación de producción entre anio-1 y anio."""

    totales = (
        estimaciones[estimaciones["anio_inicio"].isin([anio - 1, anio])]
        .groupby(["region", "anio_inicio"])
        [["produccion_tm", "superficie_cosechada_ha"]]
        .sum()
        .unstack("anio_inicio")
    )

    filas = []

    for region in list(totales.index) + ["Total país"]:

        if region == "Total país":
            produccion = totales["produccion_tm"].sum().to_numpy()
            superficie = totales["superficie_cosechada_ha"].sum().to_numpy()
        else:
            produccion = totales.loc[region, "produccion_tm"].to_numpy()
            superficie = totales.loc[region, "superficie_cosechada_ha"].to_numpy()

        rendimiento = produccion * 1000 / superficie

        aporte_superficie, aporte_rendimiento, variacion = descomponer_caida(
            produccion, superficie, rendimiento
        )

        filas.append({
            "region": region,
            "produccion_anterior_tm": produccion[0],
            "produccion_tm": produccion[1],
            "variacion_produccion_pct": variacion,
            "aporte_superficie_pct": aporte_superficie,
            "aporte_rendimiento_pct": aporte_rendimiento
        })

    return pd.DataFrame(filas).set_index("region")


def pregunta_4(datos):

    analisis = datos["analisis"]
    rachas = datos["rachas"]

    conteo = (
        rachas["conclusion"]
        .map(CONCLUSIONES_CORTAS)
        .value_counts()
        .rename("rachas")
        .to_frame()
    )

    conteo["pct"] = conteo["rachas"] / conteo["rachas"].sum() * 100

    magnitud = descomposicion_rachas(analisis, rachas)

    dominante = magnitud["dominante_magnitud"].value_counts()
    aporte_rendimiento_medio = np.mean(magnitud["aporte_rendimiento_pct"].to_numpy())

    resultado = (
        "Criterio por conteo (3.b): "
        + ", ".join(f"{nombre.lower()} {int(fila.rachas)}" for nombre, fila in conteo.iterrows())
        + f". Por magnitud (descomposición logarítmica): "
        + ", ".join(f"{nombre.lower()} {valor}" for nombre, valor in dominante.items())
        + f" de {len(magnitud)} rachas; el rendimiento explica en promedio el "
        f"{pct(aporte_rendimiento_medio)} de la caída."
    )

    mayoria = dominante.index[0].lower()

    conclusion = (
        f"El conteo de tramos deja muchas rachas como 'ambas variables' "
        f"({conteo.loc['Ambas variables', 'rachas'] if 'Ambas variables' in conteo.index else 0}); "
        f"al medir magnitudes, la mayoría ({dominante.iloc[0]} de {len(magnitud)}) se explica "
        f"principalmente por {mayoria}. No hay una causa única: cada racha requiere "
        f"una respuesta distinta (superficie → decisión de siembra; rendimiento → clima "
        f"y manejo)."
    )

    return Respuesta(
        numero=4,
        pregunta=(
            "En cada caída de producción detectada, ¿tuvo mayor incidencia la reducción "
            "de la superficie cosechada, la disminución del rendimiento o ambas?"
        ),
        operacion=(
            "value_counts() de la conclusión 3.b; descomposición np.log(P1/P0) = "
            "np.log(S1/S0) + np.log(R1/R0); np.where; np.mean"
        ),
        resultado=resultado,
        conclusion=conclusion,
        tablas={"p4_conteo": conteo, "p4_magnitud": magnitud}
    )


# ============================================================
# P5 - FOCOS CRÍTICOS
# ============================================================

def pregunta_5(datos):

    analisis = datos["analisis"].copy()
    focos = datos["focos"]

    analisis["alertas"] = (
        (analisis["s1"] == "SI").astype(int)
        + (analisis["s2"] == "SI").astype(int)
        + (analisis["s3"] == "SI").astype(int)
    )

    por_region = (
        analisis
        .groupby("region")
        .agg(
            combinaciones=("alertas", "size"),
            con_1_alerta=("alertas", lambda serie: (serie == 1).sum()),
            con_2_alertas=("alertas", lambda serie: (serie == 2).sum()),
            con_3_alertas=("alertas", lambda serie: (serie == 3).sum())
        )
    )

    por_region["multiples_pct"] = (
        (por_region["con_2_alertas"] + por_region["con_3_alertas"])
        / por_region["combinaciones"]
        * 100
    )

    por_region = por_region.sort_values(
        ["con_3_alertas", "con_2_alertas"], ascending=False
    )

    # Filtro: combinaciones con dos o más alertas simultáneas
    multiples = analisis[analisis["alertas"] >= 2]

    combinaciones_multiples = (
        multiples
        .groupby(["region", "cultivo"])
        .size()
        .rename("campanias_con_2_o_mas_alertas")
        .sort_values(ascending=False)
        .to_frame()
    )

    focos_forrajeros = focos["cultivo"].isin(FORRAJEROS).sum()
    focos_grano = focos[~focos["cultivo"].isin(FORRAJEROS)]

    region_mas_multiples = por_region["multiples_pct"].idxmax()

    resultado = (
        f"{len(focos)} focos críticos (3 alertas a la vez): "
        + "; ".join(
            f"{fila.region} {fila.cultivo} {fila.campania}" for fila in focos.itertuples()
        )
        + f". Con 2 o más alertas: {len(multiples)} casos; mayor proporción en "
        f"{region_mas_multiples} ({pct(por_region.loc[region_mas_multiples, 'multiples_pct'])})."
    )

    if not focos_grano.empty:
        foco = focos_grano.iloc[0]
        detalle_grano = (
            f"El único foco en un cultivo de grano es {foco['cultivo']} en {foco['region']} "
            f"({foco['campania']}), con una caída de producción de "
            f"{pct(foco['variacion_produccion_pct'], 1)}."
        )
    else:
        detalle_grano = "No hay focos en cultivos de grano."

    if focos["region"].value_counts().max() <= 1:
        lectura_focos = (
            "Cada región tiene a lo sumo un foco crítico, así que la concentración se "
            "ve mejor con 2 o más alertas"
        )
    else:
        lectura_focos = (
            f"{focos['region'].value_counts().idxmax()} reúne más focos críticos; con 2 "
            f"o más alertas"
        )

    conclusion = (
        f"{lectura_focos}: {region_mas_multiples} es la más expuesta. "
        f"{focos_forrajeros} de los {len(focos)} focos son forrajeros. {detalle_grano}"
    )

    return Respuesta(
        numero=5,
        pregunta="¿Qué regiones concentran múltiples comportamientos desfavorables simultáneos?",
        operacion=(
            "consulta de la VIEW vw_foco_critico; suma de banderas S1+S2+S3; "
            "filtro alertas >= 2; groupby(región) y groupby(región, cultivo)"
        ),
        resultado=resultado,
        conclusion=conclusion,
        tablas={
            "p5_focos": focos,
            "p5_alertas_por_region": por_region,
            "p5_combinaciones_multiples": combinaciones_multiples
        }
    )


def responder_preguntas(datos):

    return [
        pregunta_1(datos),
        pregunta_2(datos),
        pregunta_3(datos),
        pregunta_4(datos),
        pregunta_5(datos)
    ]
