# ============================================================
# ANÁLISIS REGIONAL Y SITUACIONES DESFAVORABLES
# ============================================================
# AnalisisRegional representa una combinación
# cultivo + campaña + región. Se compone de objetos Cultivo,
# Campania y Region, igual que en el modelo relacional
# analisis_regional referencia a esas tres tablas.
#
# Cada clase SituacionDesfavorable* representa una fila de su
# tabla de resultados y conserva una referencia al
# AnalisisRegional al que pertenece. Los métodos de clase
# consultan la base y devuelven listas de objetos, que son los
# que usa la interfaz para mostrar los resultados.
# ============================================================

from db.conexion import consultar
from modelos.dimensiones import Cultivo, Campania, Region


# Columnas y JOINs comunes para reconstruir un AnalisisRegional
COLUMNAS_ANALISIS = """
    ar.analisis_id,
    c.cultivo_id,
    c.cultivo_nombre,
    ca.campania_id,
    ca.campania,
    ca.anio_inicio,
    r.region_id,
    r.region_nombre
"""

CANTIDAD_COLUMNAS_ANALISIS = 8

JOINS_ANALISIS = """
    FROM analisis_regional ar

    JOIN cultivo c
        ON ar.cultivo_id = c.cultivo_id

    JOIN campania ca
        ON ar.campania_id = ca.campania_id

    JOIN region r
        ON ar.region_id = r.region_id
"""


def construir_filtros(region=None, cultivo=None, campania=None):
    """
    Arma las condiciones opcionales de búsqueda.
    Devuelve el texto a agregar al WHERE y sus parámetros.
    """

    condiciones = []
    parametros = []

    if region is not None:
        condiciones.append("r.region_nombre = %s")
        parametros.append(region)

    if cultivo is not None:
        condiciones.append("c.cultivo_nombre = %s")
        parametros.append(cultivo)

    if campania is not None:
        condiciones.append("ca.campania = %s")
        parametros.append(campania)

    texto = "".join(" AND " + condicion for condicion in condiciones)

    return texto, tuple(parametros)


# ============================================================
# ANÁLISIS REGIONAL
# ============================================================

class AnalisisRegional:

    def __init__(self, analisis_id, cultivo, campania, region):
        self.analisis_id = analisis_id
        self.cultivo = cultivo
        self.campania = campania
        self.region = region

        # Resultado de cada situación ('SI', 'NO' o None).
        # Se completan en las búsquedas.
        self.situacion_1 = None
        self.situacion_2 = None
        self.situacion_3 = None

    @property
    def cultivo_id(self):
        return self.cultivo.cultivo_id

    @property
    def campania_id(self):
        return self.campania.campania_id

    @property
    def region_id(self):
        return self.region.region_id

    @classmethod
    def desde_fila(cls, fila):

        return cls(
            fila[0],
            Cultivo(fila[1], fila[2]),
            Campania(fila[3], fila[4], fila[5]),
            Region(fila[6], fila[7])
        )

    def tiene_alguna_alerta(self):
        return "SI" in (self.situacion_1, self.situacion_2, self.situacion_3)

    def cantidad_alertas(self):
        return [
            self.situacion_1,
            self.situacion_2,
            self.situacion_3
        ].count("SI")

    # --------------------------------------------------------
    # Consulta base de las búsquedas
    # --------------------------------------------------------

    @classmethod
    def _buscar(cls, filtros, parametros, orden):

        filas = consultar(f"""
            SELECT
                {COLUMNAS_ANALISIS},
                s1.es_desfavorable,
                s2.es_desfavorable,
                s3.es_desfavorable

            {JOINS_ANALISIS}

            JOIN situacion_desfavorable_1 s1
                ON ar.analisis_id = s1.analisis_id

            JOIN situacion_desfavorable_2 s2
                ON ar.analisis_id = s2.analisis_id

            JOIN situacion_desfavorable_3 s3
                ON ar.analisis_id = s3.analisis_id

            WHERE 1 = 1 {filtros}

            ORDER BY {orden}
        """, parametros)

        resultados = []

        for fila in filas:

            analisis = cls.desde_fila(fila)

            analisis.situacion_1 = fila[8]
            analisis.situacion_2 = fila[9]
            analisis.situacion_3 = fila[10]

            resultados.append(analisis)

        return resultados

    # --------------------------------------------------------
    # BÚSQUEDA 1 - Por región
    # Devuelve los casos con al menos una situación
    # desfavorable dentro de la región.
    # --------------------------------------------------------

    @classmethod
    def buscar_por_region(cls, region_nombre):

        filtros, parametros = construir_filtros(region=region_nombre)

        resultados = cls._buscar(
            filtros,
            parametros,
            "ca.anio_inicio, c.cultivo_nombre"
        )

        return [a for a in resultados if a.tiene_alguna_alerta()]

    # --------------------------------------------------------
    # BÚSQUEDA 2 - Por cultivo y campaña
    # Devuelve la situación de cada región para un cultivo en
    # una campaña determinada.
    # --------------------------------------------------------

    @classmethod
    def buscar_por_cultivo_campania(cls, cultivo_nombre, campania):

        filtros, parametros = construir_filtros(
            cultivo=cultivo_nombre,
            campania=campania
        )

        return cls._buscar(filtros, parametros, "r.region_nombre")


# ============================================================
# SITUACIÓN DESFAVORABLE 1 - Superficie no cosechada
# ============================================================

class SituacionDesfavorable1:

    def __init__(
        self,
        situacion_1_id,
        analisis_id,
        superficie_sembrada_ha,
        superficie_cosechada_ha,
        superficie_no_cosechada_ha,
        porcentaje_no_cosechado,
        es_desfavorable,
        analisis=None
    ):
        self.situacion_1_id = situacion_1_id
        self.analisis_id = analisis_id
        self.superficie_sembrada_ha = superficie_sembrada_ha
        self.superficie_cosechada_ha = superficie_cosechada_ha
        self.superficie_no_cosechada_ha = superficie_no_cosechada_ha
        self.porcentaje_no_cosechado = porcentaje_no_cosechado
        self.es_desfavorable = es_desfavorable
        self.analisis = analisis

    @classmethod
    def listar_desfavorables(cls, region=None, cultivo=None, campania=None):

        filtros, parametros = construir_filtros(region, cultivo, campania)

        filas = consultar(f"""
            SELECT
                {COLUMNAS_ANALISIS},
                s1.situacion_1_id,
                s1.analisis_id,
                s1.superficie_sembrada_ha,
                s1.superficie_cosechada_ha,
                s1.superficie_no_cosechada_ha,
                s1.porcentaje_no_cosechado,
                s1.es_desfavorable

            {JOINS_ANALISIS}

            JOIN situacion_desfavorable_1 s1
                ON ar.analisis_id = s1.analisis_id

            WHERE s1.es_desfavorable = 'SI' {filtros}

            ORDER BY
                r.region_nombre,
                c.cultivo_nombre,
                ca.anio_inicio
        """, parametros)

        return [
            cls(
                *fila[CANTIDAD_COLUMNAS_ANALISIS:],
                analisis=AnalisisRegional.desde_fila(fila)
            )
            for fila in filas
        ]

    # Cantidad de casos desfavorables agrupados por
    # 'region', 'cultivo' o 'campania'.
    @staticmethod
    def contar_desfavorables_por(dimension):

        columnas = {
            "region": ("r.region_nombre", "r.region_nombre"),
            "cultivo": ("c.cultivo_nombre", "c.cultivo_nombre"),
            "campania": ("ca.campania", "ca.anio_inicio")
        }

        columna, orden = columnas[dimension]

        return consultar(f"""
            SELECT
                {columna},
                COUNT(*) AS cantidad_casos

            {JOINS_ANALISIS}

            JOIN situacion_desfavorable_1 s1
                ON ar.analisis_id = s1.analisis_id

            WHERE s1.es_desfavorable = 'SI'

            GROUP BY {columna}, {orden}

            ORDER BY {orden}
        """)

    @staticmethod
    def resumen_por_region_cultivo():

        return consultar(f"""
            SELECT
                r.region_nombre,
                c.cultivo_nombre,
                COUNT(DISTINCT ar.campania_id) AS campanias_desfavorables,
                SUM(s1.superficie_sembrada_ha) AS superficie_sembrada,
                SUM(s1.superficie_no_cosechada_ha) AS superficie_no_cosechada,
                ROUND(
                    SUM(s1.superficie_no_cosechada_ha)
                    / SUM(s1.superficie_sembrada_ha) * 100,
                    0
                ) AS porcentaje_no_cosechado

            {JOINS_ANALISIS}

            JOIN situacion_desfavorable_1 s1
                ON ar.analisis_id = s1.analisis_id

            WHERE s1.es_desfavorable = 'SI'

            GROUP BY
                r.region_nombre,
                c.cultivo_nombre

            ORDER BY
                r.region_nombre,
                c.cultivo_nombre
        """)

    @staticmethod
    def resumen_general():
        """Casos, regiones afectadas y período de los casos."""

        return consultar(f"""
            SELECT
                COUNT(*),
                COUNT(DISTINCT ar.region_id),
                MIN(ca.anio_inicio),
                MAX(ca.anio_inicio)

            {JOINS_ANALISIS}

            JOIN situacion_desfavorable_1 s1
                ON ar.analisis_id = s1.analisis_id

            WHERE s1.es_desfavorable = 'SI'
        """)[0]


# ============================================================
# SITUACIÓN DESFAVORABLE 2 - Bajo rendimiento
# ============================================================

class SituacionDesfavorable2:

    def __init__(
        self,
        situacion_2_id,
        analisis_id,
        rendimiento_regional_kgxha,
        rendimiento_nacional_kgxha,
        diferencia_rendimiento_kgxha,
        es_desfavorable,
        analisis=None
    ):
        self.situacion_2_id = situacion_2_id
        self.analisis_id = analisis_id
        self.rendimiento_regional_kgxha = rendimiento_regional_kgxha
        self.rendimiento_nacional_kgxha = rendimiento_nacional_kgxha
        self.diferencia_rendimiento_kgxha = diferencia_rendimiento_kgxha
        self.es_desfavorable = es_desfavorable
        self.analisis = analisis

    @property
    def brecha_pct(self):
        """Diferencia con el rendimiento nacional, en porcentaje."""

        if not self.rendimiento_nacional_kgxha:
            return None

        return (
            float(self.diferencia_rendimiento_kgxha)
            / float(self.rendimiento_nacional_kgxha)
            * 100
        )

    @classmethod
    def listar_desfavorables(cls, region=None, cultivo=None, campania=None):

        filtros, parametros = construir_filtros(region, cultivo, campania)

        filas = consultar(f"""
            SELECT
                {COLUMNAS_ANALISIS},
                s2.situacion_2_id,
                s2.analisis_id,
                s2.rendimiento_regional_kgxha,
                s2.rendimiento_nacional_kgxha,
                s2.diferencia_rendimiento_kgxha,
                s2.es_desfavorable

            {JOINS_ANALISIS}

            JOIN situacion_desfavorable_2 s2
                ON ar.analisis_id = s2.analisis_id

            WHERE s2.es_desfavorable = 'SI' {filtros}

            ORDER BY
                r.region_nombre,
                c.cultivo_nombre,
                ca.anio_inicio
        """, parametros)

        return [
            cls(
                *fila[CANTIDAD_COLUMNAS_ANALISIS:],
                analisis=AnalisisRegional.desde_fila(fila)
            )
            for fila in filas
        ]

    @staticmethod
    def resumen_por_region():
        """
        Por región: casos desfavorables, casos evaluados y brecha
        promedio (%) de los casos desfavorables.
        """

        return consultar(f"""
            SELECT
                r.region_nombre,
                SUM(s2.es_desfavorable = 'SI') AS casos_desfavorables,
                COUNT(s2.es_desfavorable) AS casos_evaluados,
                ROUND(
                    AVG(
                        CASE
                            WHEN s2.es_desfavorable = 'SI'
                            THEN s2.diferencia_rendimiento_kgxha
                                 / s2.rendimiento_nacional_kgxha * 100
                        END
                    ),
                    1
                ) AS brecha_promedio_pct

            {JOINS_ANALISIS}

            JOIN situacion_desfavorable_2 s2
                ON ar.analisis_id = s2.analisis_id

            GROUP BY r.region_nombre

            ORDER BY r.region_nombre
        """)


# ============================================================
# SITUACIÓN DESFAVORABLE 3 - Caída sostenida de producción
# ============================================================

class SituacionDesfavorable3:

    def __init__(
        self,
        situacion_3_id,
        analisis_id,
        produccion_actual_tm,
        produccion_anterior_tm,
        variacion_produccion_pct,
        hay_caida,
        caidas_consecutivas,
        es_desfavorable,
        analisis=None
    ):
        self.situacion_3_id = situacion_3_id
        self.analisis_id = analisis_id
        self.produccion_actual_tm = produccion_actual_tm
        self.produccion_anterior_tm = produccion_anterior_tm
        self.variacion_produccion_pct = variacion_produccion_pct
        self.hay_caida = hay_caida
        self.caidas_consecutivas = caidas_consecutivas
        self.es_desfavorable = es_desfavorable
        self.analisis = analisis

    @classmethod
    def listar_desfavorables(cls, region=None, cultivo=None, campania=None):

        filtros, parametros = construir_filtros(region, cultivo, campania)

        filas = consultar(f"""
            SELECT
                {COLUMNAS_ANALISIS},
                s3.situacion_3_id,
                s3.analisis_id,
                s3.produccion_actual_tm,
                s3.produccion_anterior_tm,
                s3.variacion_produccion_pct,
                s3.hay_caida,
                s3.caidas_consecutivas,
                s3.es_desfavorable

            {JOINS_ANALISIS}

            JOIN situacion_desfavorable_3 s3
                ON ar.analisis_id = s3.analisis_id

            WHERE s3.es_desfavorable = 'SI' {filtros}

            ORDER BY
                r.region_nombre,
                c.cultivo_nombre,
                ca.anio_inicio
        """, parametros)

        return [
            cls(
                *fila[CANTIDAD_COLUMNAS_ANALISIS:],
                analisis=AnalisisRegional.desde_fila(fila)
            )
            for fila in filas
        ]

    @staticmethod
    def resumen_por_region_cultivo():
        """
        Por región y cultivo: campañas en situación desfavorable
        y máxima cantidad de caídas consecutivas alcanzada.
        """

        return consultar(f"""
            SELECT
                r.region_nombre,
                c.cultivo_nombre,
                COUNT(*) AS campanias_desfavorables,
                MAX(s3.caidas_consecutivas) AS max_caidas

            {JOINS_ANALISIS}

            JOIN situacion_desfavorable_3 s3
                ON ar.analisis_id = s3.analisis_id

            WHERE s3.es_desfavorable = 'SI'

            GROUP BY
                r.region_nombre,
                c.cultivo_nombre

            ORDER BY
                r.region_nombre,
                c.cultivo_nombre
        """)


# ============================================================
# SITUACIÓN DESFAVORABLE 3.b - Incidencia en la caída
# ============================================================
# Una fila por racha de caída sostenida de producción, con la
# cantidad de tramos en los que cayó la superficie cosechada
# y la cantidad en los que cayó el rendimiento.
# ============================================================

CONCLUSION_SUPERFICIE = (
    "Caída con mayor incidencia de la reducción "
    "de superficie cosechada"
)

CONCLUSION_RENDIMIENTO = (
    "Caída con mayor incidencia de la disminución "
    "del rendimiento"
)

CONCLUSION_AMBAS = (
    "Caída con incidencia de la reducción de superficie "
    "cosechada y de la disminución del rendimiento"
)

CONCLUSION_NO_DETERMINADA = (
    "Caída no determinada por reducción de superficie "
    "cosechada ni disminución de rendimiento"
)

CONCLUSIONES_CORTAS = {
    CONCLUSION_SUPERFICIE: "Superficie cosechada",
    CONCLUSION_RENDIMIENTO: "Rendimiento",
    CONCLUSION_AMBAS: "Ambas variables",
    CONCLUSION_NO_DETERMINADA: "No determinada"
}


class SituacionDesfavorable3B:

    def __init__(
        self,
        situacion_3b_id,
        cultivo_id,
        region_id,
        analisis_id_inicio,
        analisis_id_fin,
        cantidad_caidas_produccion,
        cantidad_caidas_superficie,
        cantidad_caidas_rendimiento,
        conclusion,
        cultivo=None,
        region=None,
        campania_inicio=None,
        campania_fin=None
    ):
        self.situacion_3b_id = situacion_3b_id
        self.cultivo_id = cultivo_id
        self.region_id = region_id
        self.analisis_id_inicio = analisis_id_inicio
        self.analisis_id_fin = analisis_id_fin
        self.cantidad_caidas_produccion = cantidad_caidas_produccion
        self.cantidad_caidas_superficie = cantidad_caidas_superficie
        self.cantidad_caidas_rendimiento = cantidad_caidas_rendimiento
        self.conclusion = conclusion

        # Descripciones para mostrar
        self.cultivo = cultivo
        self.region = region
        self.campania_inicio = campania_inicio
        self.campania_fin = campania_fin

    @property
    def conclusion_corta(self):
        return CONCLUSIONES_CORTAS.get(self.conclusion, self.conclusion)

    @classmethod
    def listar(cls, region=None):

        filtros, parametros = construir_filtros(region=region)

        filas = consultar(f"""
            SELECT
                s3b.situacion_3b_id,
                s3b.cultivo_id,
                s3b.region_id,
                s3b.analisis_id_inicio,
                s3b.analisis_id_fin,
                s3b.cantidad_caidas_produccion,
                s3b.cantidad_caidas_superficie,
                s3b.cantidad_caidas_rendimiento,
                s3b.conclusion,
                c.cultivo_nombre,
                r.region_nombre,
                ca_ini.campania,
                ca_fin.campania

            FROM situacion_desfavorable_3b s3b

            JOIN cultivo c
                ON s3b.cultivo_id = c.cultivo_id

            JOIN region r
                ON s3b.region_id = r.region_id

            JOIN analisis_regional ar_ini
                ON s3b.analisis_id_inicio = ar_ini.analisis_id

            JOIN campania ca_ini
                ON ar_ini.campania_id = ca_ini.campania_id

            JOIN analisis_regional ar_fin
                ON s3b.analisis_id_fin = ar_fin.analisis_id

            JOIN campania ca_fin
                ON ar_fin.campania_id = ca_fin.campania_id

            WHERE 1 = 1 {filtros}

            ORDER BY
                r.region_nombre,
                c.cultivo_nombre,
                ca_ini.anio_inicio
        """, parametros)

        return [cls(*fila) for fila in filas]

    @staticmethod
    def resumen_por_conclusion():

        return consultar("""
            SELECT
                conclusion,
                COUNT(*) AS rachas
            FROM situacion_desfavorable_3b
            GROUP BY conclusion
            ORDER BY rachas DESC
        """)


# ============================================================
# FOCO CRÍTICO (VIEW vw_foco_critico)
# ============================================================

class FocoCritico:

    def __init__(
        self,
        analisis_id,
        cultivo,
        region,
        campania,
        porcentaje_no_cosechado,
        rendimiento_regional_kgxha,
        rendimiento_nacional_kgxha,
        produccion_actual_tm,
        produccion_anterior_tm,
        variacion_produccion_pct,
        caidas_consecutivas
    ):
        self.analisis_id = analisis_id
        self.cultivo = cultivo
        self.region = region
        self.campania = campania
        self.porcentaje_no_cosechado = porcentaje_no_cosechado
        self.rendimiento_regional_kgxha = rendimiento_regional_kgxha
        self.rendimiento_nacional_kgxha = rendimiento_nacional_kgxha
        self.produccion_actual_tm = produccion_actual_tm
        self.produccion_anterior_tm = produccion_anterior_tm
        self.variacion_produccion_pct = variacion_produccion_pct
        self.caidas_consecutivas = caidas_consecutivas

    @classmethod
    def listar(cls):

        filas = consultar("""
            SELECT
                analisis_id,
                cultivo,
                region,
                campania,
                porcentaje_no_cosechado,
                rendimiento_regional_kgxha,
                rendimiento_nacional_kgxha,
                produccion_actual_tm,
                produccion_anterior_tm,
                variacion_produccion_pct,
                caidas_consecutivas
            FROM vw_foco_critico
            ORDER BY region, cultivo, campania
        """)

        return [cls(*fila) for fila in filas]
