# ============================================================
# TABLA DE TRAZABILIDAD Y HALLAZGO PRINCIPAL
# ============================================================

import pandas as pd

from procesamiento.exploracion import produccion_nacional_por_campania
from procesamiento.preguntas import descomposicion_campania, pct, millones


def tabla_trazabilidad(respuestas):
    """Pregunta → operación → resultado → conclusión."""

    return pd.DataFrame(
        [
            {
                "Pregunta": f"P{r.numero}. {r.pregunta}",
                "Operación utilizada": r.operacion,
                "Resultado": r.resultado,
                "Conclusión": r.conclusion
            }
            for r in respuestas
        ]
    )


# ============================================================
# HALLAZGO PRINCIPAL
# ============================================================
# Entre los resultados de las 5 preguntas, el de mayor impacto
# productivo es la caída de la campaña con menor producción del
# período (la sequía 2022/2023): se cuantifica a nivel país y
# por región con la misma descomposición logarítmica de P4.
# ============================================================

def hallazgo_principal(datos, respuestas):

    estimaciones = datos["estimaciones"]
    focos = datos["focos"]

    nacional = produccion_nacional_por_campania(estimaciones)
    peor = nacional.loc[nacional["variacion_produccion_pct"].idxmin()]
    anio = int(peor["anio_inicio"])

    descomposicion = descomposicion_campania(estimaciones, anio)

    pais = descomposicion.loc["Total país"]
    regiones = descomposicion.drop("Total país")
    region_critica = regiones["variacion_produccion_pct"].idxmin()
    critica = regiones.loc[region_critica]

    participacion = (
        estimaciones.groupby("region")["produccion_tm"].sum()
        / estimaciones["produccion_tm"].sum()
        * 100
    )

    ranking = participacion.rank(ascending=False).astype(int)

    foco_region = focos[
        (focos["region"] == region_critica) & (focos["campania"] == peor["campania"])
    ]

    texto_foco = ""

    if not foco_region.empty:
        foco = foco_region.iloc[0]
        texto_foco = (
            f" Allí se ubica además el único foco crítico de un cultivo de grano: "
            f"{foco['cultivo']} {foco['campania']}, con producción "
            f"{pct(foco['variacion_produccion_pct'], 1)} respecto de la campaña anterior, "
            f"rendimiento "
            f"{pct((foco['rendimiento_regional_kgxha'] / foco['rendimiento_nacional_kgxha'] - 1) * 100)} "
            f"respecto del nacional y {pct(foco['porcentaje_no_cosechado'])} de superficie "
            f"sin cosechar."
        )

    hallazgo = (
        f"En la campaña {peor['campania']} la producción nacional cayó "
        f"{pct(abs(pais['variacion_produccion_pct']))} ({millones(pais['produccion_anterior_tm'])} → "
        f"{millones(pais['produccion_tm'])} millones de t) y el "
        f"{pct(pais['aporte_rendimiento_pct'])} de esa caída se explica por el rendimiento, "
        f"no por la superficie. En todas las regiones el rendimiento explica entre "
        f"{pct(regiones['aporte_rendimiento_pct'].min())} y "
        f"{pct(regiones['aporte_rendimiento_pct'].max())}. La más afectada fue {region_critica} "
        f"({pct(critica['variacion_produccion_pct'])}), que es la región número "
        f"{ranking[region_critica]} en producción ({pct(participacion[region_critica])} del total "
        f"del período).{texto_foco}"
    )

    decision = (
        f"Priorizar a {region_critica} en los instrumentos de gestión del riesgo climático "
        f"orientados al rendimiento (seguros multirriesgo o por índice de rendimiento, "
        f"alerta temprana de déficit hídrico y asistencia técnica en manejo del agua), en "
        f"lugar de medidas sobre la superficie sembrada: la pérdida no vino de sembrar o "
        f"cosechar menos hectáreas sino de producir menos por hectárea. Como seguimiento, "
        f"usar la situación desfavorable 2 de {region_critica} campaña a campaña como "
        f"indicador de alerta."
    )

    return {
        "campania": peor["campania"],
        "anio": anio,
        "descomposicion": descomposicion,
        "region_critica": region_critica,
        "hallazgo": hallazgo,
        "decision": decision
    }
