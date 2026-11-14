# ============================================================
# PROCESAMIENTO DE DATOS CON PANDAS Y NUMPY (Entrega 3)
# ============================================================
# Ejecutar desde la carpeta abp3:
#
#     python -m procesamiento
#
# 1. Carga los datos de MySQL en DataFrames.
# 2. Aplica filtros y agrupamientos.
# 3. Obtiene estadísticas descriptivas con describe().
# 4. Realiza operaciones con NumPy.
# 5. Responde las 5 preguntas de análisis.
# 6. Arma la tabla de trazabilidad y el hallazgo principal.
# 7. Exporta tablas (CSV), trazabilidad (CSV y Markdown),
#    gráficos (PNG) y el reporte de consola a
#    salidas/entrega3/.
# ============================================================

import sys
import textwrap
from pathlib import Path

import pandas as pd

from procesamiento import calidad, exploracion, graficos
from procesamiento.carga import cargar_datos
from procesamiento.conclusiones import hallazgo_principal, tabla_trazabilidad
from procesamiento.graficos import miles_es
from procesamiento.preguntas import responder_preguntas, pct


CARPETA_SALIDA = Path(__file__).resolve().parent.parent / "salidas" / "entrega3"
ANCHO = 100

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)
pd.set_option("display.float_format", lambda valor: miles_es(valor, 1))


# ------------------------------------------------------------
# Salida por consola y a archivo al mismo tiempo
# ------------------------------------------------------------

class Duplicador:

    def __init__(self, *destinos):
        self.destinos = destinos

    def write(self, texto):
        for destino in self.destinos:
            destino.write(texto)

    def flush(self):
        for destino in self.destinos:
            destino.flush()


def seccion(titulo):
    print("\n" + "=" * ANCHO)
    print(titulo)
    print("=" * ANCHO)


def parrafo(texto, sangria=""):
    print(textwrap.fill(texto, width=ANCHO, initial_indent=sangria, subsequent_indent=sangria))


# ------------------------------------------------------------
# Exportación
# ------------------------------------------------------------

def exportar_csv(tabla, nombre, carpeta):
    ruta = carpeta / f"{nombre}.csv"
    tabla.to_csv(ruta, sep=";", decimal=",", encoding="utf-8-sig", float_format="%.2f")
    return ruta


def exportar_trazabilidad_markdown(trazabilidad, hallazgo, ruta):

    lineas = [
        "# Tabla de trazabilidad",
        "",
        "| Pregunta | Operación utilizada | Resultado | Conclusión |",
        "|---|---|---|---|"
    ]

    for fila in trazabilidad.itertuples(index=False):
        celdas = [str(valor).replace("|", "/") for valor in fila]
        lineas.append("| " + " | ".join(celdas) + " |")

    lineas += [
        "",
        "## Hallazgo principal",
        "",
        hallazgo["hallazgo"],
        "",
        "## Decisión de gestión",
        "",
        hallazgo["decision"],
        ""
    ]

    ruta.write_text("\n".join(lineas), encoding="utf-8")


# ============================================================
# PROCESAMIENTO
# ============================================================

def procesar():

    carpeta_tablas = CARPETA_SALIDA / "tablas"
    carpeta_graficos = CARPETA_SALIDA / "graficos"
    carpeta_tablas.mkdir(parents=True, exist_ok=True)
    carpeta_graficos.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # 1. Carga
    # --------------------------------------------------------

    seccion("1. CARGA DE DATOS DESDE MYSQL A PANDAS")

    datos = cargar_datos()

    for nombre in ("estimaciones", "analisis", "rachas", "focos"):
        filas, columnas = datos[nombre].shape
        print(f"{nombre:<14}{filas:>6} filas × {columnas:>2} columnas")

    estimaciones = datos["estimaciones"]

    print("\nPrimeras filas de estimaciones:")
    print(estimaciones.head())

    # --------------------------------------------------------
    # 1.b Calidad inicial del CSV crudo
    # --------------------------------------------------------

    seccion("1.b CALIDAD INICIAL DE LOS DATOS (CSV crudo, estimaciones_csv)")

    faltantes, no_numericos, controles = calidad.diagnostico_calidad(calidad.cargar_csv_crudo())

    print("Valores faltantes (nulos o vacíos) por columna:\n")
    print(faltantes)
    print("\nValores no numéricos en columnas numéricas:\n")
    print(no_numericos.to_frame("no_numericos"))
    print("\nControles:\n")
    print(controles)

    exportar_csv(faltantes, "calidad_faltantes", carpeta_tablas)
    exportar_csv(controles, "calidad_controles", carpeta_tablas)

    # --------------------------------------------------------
    # 2. Filtros y agrupamiento
    # --------------------------------------------------------

    seccion("2. FILTROS Y AGRUPAMIENTO")

    participacion, ultima, peso_principales = exploracion.participacion_por_region(estimaciones)

    print("Filtro 1: cultivo en", exploracion.CULTIVOS_PRINCIPALES)
    print(f"Filtro 2: campaña {ultima}/{ultima + 1}")
    print("Agrupamiento: groupby('region') → provincias, producción, superficie, rendimiento\n")
    print(participacion)

    print()
    parrafo(
        f"Los cuatro cultivos principales representan el {pct(peso_principales)} de la "
        f"producción de la campaña. {participacion.index[0]} aporta el "
        f"{pct(participacion['participacion_pct'].iloc[0])} con un rendimiento de "
        f"{miles_es(participacion['rendimiento_kgxha'].iloc[0])} kg/ha, frente a "
        f"{miles_es(participacion['rendimiento_kgxha'].min())} kg/ha de "
        f"{participacion['rendimiento_kgxha'].idxmin()}."
    )

    exportar_csv(participacion, "exploracion_participacion_por_region", carpeta_tablas)

    nacional = exploracion.produccion_nacional_por_campania(estimaciones)
    print("\nProducción nacional por campaña (groupby campaña + pct_change):\n")
    print(nacional.set_index("campania").drop(columns="anio_inicio"))
    exportar_csv(nacional, "exploracion_produccion_nacional", carpeta_tablas)

    # --------------------------------------------------------
    # 3. Estadísticas descriptivas
    # --------------------------------------------------------

    seccion("3. ESTADÍSTICAS DESCRIPTIVAS — describe()")

    descripcion, lectura = exploracion.estadisticas_descriptivas(estimaciones)
    print(descripcion)
    exportar_csv(descripcion, "describe_estimaciones", carpeta_tablas)

    print("\nInterpretación:")

    parrafo(
        f"- Distribuciones muy asimétricas: la producción media por registro "
        f"({miles_es(lectura['produccion_media'])} t) es "
        f"{lectura['produccion_media_sobre_mediana']:.0f} veces la mediana "
        f"({miles_es(lectura['produccion_mediana'])} t), y en superficie sembrada "
        f"{lectura['sembrada_media_sobre_mediana']:.0f} veces. Pocos cultivos y "
        f"provincias concentran casi todo el volumen (máximo "
        f"{miles_es(lectura['produccion_max'])} t); la mediana describe mejor un caso típico.",
        "  "
    )
    parrafo(
        f"- El rendimiento va de {miles_es(lectura['rendimiento_min'])} a "
        f"{miles_es(lectura['rendimiento_max'])} kg/ha porque mezcla cultivos muy distintos: "
        f"solo es comparable dentro de un mismo cultivo y campaña (por eso S2 compara "
        f"contra el nacional del mismo cultivo y campaña).",
        "  "
    )
    parrafo(
        f"- La mediana del porcentaje cosechado es {pct(lectura['cosechado_mediana'], 1)} y el "
        f"primer cuartil {pct(lectura['cosechado_q1'], 1)}: el {pct(lectura['cosechado_menor_80_pct'])} "
        f"de los registros cosecha menos del 80 % de lo sembrado y "
        f"{lectura['sin_cosecha']} registros no cosecharon nada.",
        "  "
    )

    # --------------------------------------------------------
    # 4. NumPy
    # --------------------------------------------------------

    seccion("4. OPERACIONES CON NUMPY")

    rendimientos = exploracion.rendimiento_simple_vs_ponderado(estimaciones, ultima)
    print(f"a) np.mean vs np.average(weights=superficie cosechada) — campaña {ultima}/{ultima + 1}\n")
    print(rendimientos)
    exportar_csv(rendimientos, "numpy_rendimiento_simple_vs_ponderado", carpeta_tablas)

    mayor = rendimientos["diferencia_pct"].abs().idxmax()
    print()
    parrafo(
        f"El promedio simple de rendimientos provinciales se aparta del rendimiento real "
        f"hasta {pct(abs(rendimientos.loc[mayor, 'diferencia_pct']), 1)} ({mayor}), porque "
        f"da el mismo peso a una provincia marginal que a una núcleo. Esto justifica "
        f"recalcular el rendimiento como producción total / superficie cosechada total."
    )

    percentiles = exploracion.percentiles_cosechado(estimaciones)
    print("\nb) np.percentile del porcentaje cosechado:\n")
    print(percentiles.to_frame("porcentaje_cosechado").T)

    semaforo = exploracion.semaforo_no_cosechado(datos["analisis"], datos["umbral_no_cosechado"])
    print(
        f"\nc) np.select — semáforo de superficie no cosechada "
        f"(verde ≤ 10 %, amarillo ≤ {datos['umbral_no_cosechado']:.0f} %, rojo > "
        f"{datos['umbral_no_cosechado']:.0f} %):\n"
    )
    print(semaforo.to_frame("combinaciones").T)

    print(
        "\nd) np.log — descomposición de las caídas de producción "
        "(ver pregunta 4 y hallazgo principal)."
    )

    # --------------------------------------------------------
    # 5. Preguntas
    # --------------------------------------------------------

    respuestas = responder_preguntas(datos)

    for respuesta in respuestas:

        seccion(f"5.{respuesta.numero} PREGUNTA {respuesta.numero}")
        parrafo(respuesta.pregunta)

        print()
        parrafo(f"Operación: {respuesta.operacion}", "  ")

        if "casos_sql" in respuesta.datos:
            coincide = respuesta.datos["casos_pandas"] == respuesta.datos["casos_sql"]
            print(
                f"  Validación pandas vs SQL: {respuesta.datos['casos_pandas']} vs "
                f"{respuesta.datos['casos_sql']} casos → "
                f"{'coinciden' if coincide else 'NO COINCIDEN'}"
            )

        nombre_tabla, tabla = next(iter(respuesta.tablas.items()))
        print(f"\n{nombre_tabla}:\n")
        print(tabla)

        print()
        parrafo(f"Resultado: {respuesta.resultado}", "  ")
        print()
        parrafo(f"Conclusión: {respuesta.conclusion}", "  ")

        for nombre, tabla in respuesta.tablas.items():
            exportar_csv(tabla, nombre, carpeta_tablas)

    # --------------------------------------------------------
    # 6. Trazabilidad y hallazgo
    # --------------------------------------------------------

    seccion("6. TABLA DE TRAZABILIDAD")

    trazabilidad = tabla_trazabilidad(respuestas)

    for fila in trazabilidad.itertuples(index=False):
        print()
        parrafo(fila.Pregunta)
        parrafo(f"Operación:  {fila[1]}", "   ")
        parrafo(f"Resultado:  {fila.Resultado}", "   ")
        parrafo(f"Conclusión: {fila[3]}", "   ")

    hallazgo = hallazgo_principal(datos, respuestas)

    seccion("7. HALLAZGO PRINCIPAL Y DECISIÓN DE GESTIÓN")

    print(hallazgo["descomposicion"])
    print()
    parrafo(f"Hallazgo: {hallazgo['hallazgo']}")
    print()
    parrafo(f"Decisión: {hallazgo['decision']}")

    exportar_csv(trazabilidad.set_index("Pregunta"), "trazabilidad", CARPETA_SALIDA)
    exportar_csv(hallazgo["descomposicion"], "hallazgo_descomposicion", carpeta_tablas)
    exportar_trazabilidad_markdown(trazabilidad, hallazgo, CARPETA_SALIDA / "trazabilidad.md")

    # --------------------------------------------------------
    # 7. Gráficos
    # --------------------------------------------------------

    seccion("8. GRÁFICOS")

    rutas = [
        graficos.grafico_produccion_nacional(nacional, hallazgo["campania"], carpeta_graficos),
        graficos.grafico_no_cosechada_por_cultivo(
            respuestas[0].tablas["p1_por_cultivo"], carpeta_graficos
        ),
        graficos.grafico_bajo_rendimiento(respuestas[1].tablas["p2_por_region"], carpeta_graficos),
        graficos.grafico_descomposicion(
            hallazgo["descomposicion"], hallazgo["campania"], carpeta_graficos
        ),
        graficos.grafico_alertas(
            respuestas[4].tablas["p5_alertas_por_region"], carpeta_graficos
        )
    ]

    for ruta in rutas:
        print(ruta.relative_to(CARPETA_SALIDA.parent.parent))

    print(f"\nSalidas en: {CARPETA_SALIDA}")


def main():

    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

    with open(CARPETA_SALIDA / "reporte_consola.txt", "w", encoding="utf-8") as archivo:

        consola = sys.stdout
        sys.stdout = Duplicador(consola, archivo)

        try:
            procesar()
        finally:
            sys.stdout = consola


if __name__ == "__main__":
    main()
