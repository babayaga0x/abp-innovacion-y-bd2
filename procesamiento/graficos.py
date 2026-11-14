# ============================================================
# GRÁFICOS DEL PROCESAMIENTO (matplotlib, PNG para el informe)
# ============================================================
# Paleta: azul como serie principal, naranja para destacar el
# dato que responde la pregunta. Textos en tinta neutra,
# grilla tenue, un solo eje por gráfico.
# ============================================================

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


SUPERFICIE = "#fcfcfb"
TEXTO = "#0b0b0b"
TEXTO_SECUNDARIO = "#52514e"
GRILLA = "#e4e3df"

AZUL = "#2a78d6"
NARANJA = "#eb6834"

# Escala ordinal de un solo tono (1, 2 y 3 alertas)
AZULES = ["#86b6ef", "#2a78d6", "#104281"]


plt.rcParams.update({
    "figure.facecolor": SUPERFICIE,
    "axes.facecolor": SUPERFICIE,
    "axes.edgecolor": GRILLA,
    "axes.labelcolor": TEXTO_SECUNDARIO,
    "axes.titlecolor": TEXTO,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.titlepad": 14,
    "xtick.color": TEXTO_SECUNDARIO,
    "ytick.color": TEXTO_SECUNDARIO,
    "font.size": 10,
    "legend.frameon": False,
    "savefig.dpi": 150,
    "savefig.bbox": "tight"
})


def preparar_ejes(ax, eje_valores="y"):

    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)

    ax.grid(axis=eje_valores, color=GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)


def miles_es(valor, decimales=0):
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def guardar(fig, carpeta, nombre):
    ruta = carpeta / nombre
    fig.savefig(ruta)
    plt.close(fig)
    return ruta


# ============================================================
# 1. Producción nacional por campaña
# ============================================================

def grafico_produccion_nacional(nacional, campania_destacada, carpeta):

    fig, ax = plt.subplots(figsize=(10, 4.8))

    valores = nacional["produccion_tm"].to_numpy() / 1e6
    colores = [
        NARANJA if campania == campania_destacada else AZUL
        for campania in nacional["campania"]
    ]

    barras = ax.bar(
        nacional["campania"], valores, color=colores, width=0.7,
        edgecolor=SUPERFICIE, linewidth=2
    )

    for barra, campania, valor in zip(barras, nacional["campania"], valores):
        if campania == campania_destacada or valor == valores.max():
            ax.annotate(
                f"{miles_es(valor, 1)} Mt",
                (barra.get_x() + barra.get_width() / 2, valor),
                xytext=(0, 4), textcoords="offset points",
                ha="center", color=TEXTO, fontsize=9
            )

    preparar_ejes(ax)
    ax.set_ylabel("Millones de toneladas")
    ax.set_title(
        f"Producción nacional por campaña — la caída de {campania_destacada}"
    )
    ax.tick_params(axis="x", rotation=0, labelsize=8.5)

    return guardar(fig, carpeta, "01_produccion_nacional_por_campania.png")


# ============================================================
# 2. P1 - Superficie no cosechada por cultivo
# ============================================================

def grafico_no_cosechada_por_cultivo(por_cultivo, carpeta, cantidad=8):

    datos = por_cultivo.head(cantidad).iloc[::-1]

    fig, ax = plt.subplots(figsize=(9, 5))

    colores = np.where(datos["forrajero"] == "SI", NARANJA, AZUL)
    valores = datos["no_cosechada_ha"].to_numpy() / 1e6

    ax.barh(datos.index, valores, color=colores, height=0.7, edgecolor=SUPERFICIE, linewidth=2)

    for posicion, (valor, participacion) in enumerate(zip(valores, datos["participacion_pct"])):
        ax.annotate(
            f"{miles_es(valor, 1)} Mha · {miles_es(participacion, 0)} %",
            (valor, posicion), xytext=(4, 0), textcoords="offset points",
            va="center", color=TEXTO_SECUNDARIO, fontsize=8.5
        )

    preparar_ejes(ax, "x")
    ax.set_xlabel("Superficie no cosechada en casos desfavorables (millones de ha, acumulado del período)")
    ax.set_title("P1 · Superficie no cosechada por cultivo")
    ax.set_xlim(0, valores.max() * 1.3)

    ax.legend(
        handles=[
            plt.Rectangle((0, 0), 1, 1, color=NARANJA),
            plt.Rectangle((0, 0), 1, 1, color=AZUL)
        ],
        labels=["Forrajero (pastoreo)", "Grano / industrial"],
        loc="lower right"
    )

    return guardar(fig, carpeta, "02_p1_no_cosechada_por_cultivo.png")


# ============================================================
# 3. P2 - Casos con rendimiento bajo el nacional, por región
# ============================================================

def grafico_bajo_rendimiento(por_region, carpeta):

    datos = por_region.sort_values("desfavorables_pct")

    fig, ax = plt.subplots(figsize=(9, 4))

    valores = datos["desfavorables_pct"].to_numpy()

    ax.barh(datos.index, valores, color=AZUL, height=0.65, edgecolor=SUPERFICIE, linewidth=2)

    for posicion, (valor, brecha) in enumerate(zip(valores, datos["brecha_mediana_pct"])):
        ax.annotate(
            f"{miles_es(valor)} %  (brecha mediana {miles_es(brecha)} %)",
            (valor, posicion), xytext=(4, 0), textcoords="offset points",
            va="center", color=TEXTO_SECUNDARIO, fontsize=8.5
        )

    preparar_ejes(ax, "x")
    ax.set_xlim(0, 115)
    ax.set_xlabel("% de combinaciones cultivo-campaña con rendimiento regional < nacional")
    ax.set_title("P2 · Bajo rendimiento relativo por región")

    return guardar(fig, carpeta, "03_p2_bajo_rendimiento_por_region.png")


# ============================================================
# 4. P4 / Hallazgo - Descomposición de la caída de una campaña
# ============================================================

def grafico_descomposicion(descomposicion, campania, carpeta):

    datos = descomposicion.iloc[::-1]

    fig, ax = plt.subplots(figsize=(10, 4.4))

    superficie = datos["aporte_superficie_pct"].to_numpy()
    rendimiento = datos["aporte_rendimiento_pct"].to_numpy()
    etiquetas = [
        f"{region}  ({miles_es(variacion, 0)} %)"
        for region, variacion in zip(datos.index, datos["variacion_produccion_pct"])
    ]

    ax.barh(etiquetas, superficie, color=NARANJA, height=0.65,
            edgecolor=SUPERFICIE, linewidth=2, label="Superficie cosechada")
    ax.barh(etiquetas, rendimiento, left=superficie, color=AZUL, height=0.65,
            edgecolor=SUPERFICIE, linewidth=2, label="Rendimiento")

    for posicion, (valor_s, valor_r) in enumerate(zip(superficie, rendimiento)):
        ax.text(valor_s / 2, posicion, f"{miles_es(valor_s)} %", ha="center", va="center",
                color="white", fontsize=8.5, fontweight="bold")
        ax.text(valor_s + valor_r / 2, posicion, f"{miles_es(valor_r)} %", ha="center",
                va="center", color="white", fontsize=8.5, fontweight="bold")

    preparar_ejes(ax, "x")
    ax.set_xlim(0, 100)
    ax.set_xlabel("Parte de la caída de producción explicada por cada variable (%)")
    ax.set_title(f"Hallazgo · ¿Por qué cayó la producción en {campania}?")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2)

    return guardar(fig, carpeta, "04_hallazgo_descomposicion_caida.png")


# ============================================================
# 5. P5 - Alertas simultáneas por región
# ============================================================

def grafico_alertas(por_region, carpeta):

    datos = por_region.sort_values("multiples_pct")

    fig, ax = plt.subplots(figsize=(9, 4))

    acumulado = np.zeros(len(datos))
    columnas = ["con_1_alerta", "con_2_alertas", "con_3_alertas"]
    nombres = ["1 alerta", "2 alertas", "3 alertas (foco crítico)"]

    for columna, nombre, color in zip(columnas, nombres, AZULES):

        valores = (datos[columna] / datos["combinaciones"] * 100).to_numpy()

        ax.barh(datos.index, valores, left=acumulado, color=color, height=0.65,
                edgecolor=SUPERFICIE, linewidth=2, label=nombre)

        acumulado += valores

    for posicion, valor in enumerate(datos["multiples_pct"]):
        ax.annotate(
            f"{miles_es(valor)} % con 2 o más",
            (acumulado[posicion], posicion), xytext=(4, 0), textcoords="offset points",
            va="center", color=TEXTO_SECUNDARIO, fontsize=8.5
        )

    preparar_ejes(ax, "x")
    ax.set_xlim(0, 100)
    ax.set_xlabel("% de combinaciones cultivo-campaña de la región")
    ax.set_title("P5 · Alertas simultáneas por región")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3)

    return guardar(fig, carpeta, "05_p5_alertas_por_region.png")
