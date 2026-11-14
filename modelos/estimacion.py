# ============================================================
# ESTIMACIÓN
# ============================================================
# Una estimación es la producción de un cultivo, en una
# campaña y una provincia (tabla estimacion).
#
# BAJA LÓGICA
# Las estimaciones provienen de una fuente oficial, por lo
# que no se eliminan físicamente. La baja marca el registro
# como inactivo (activa = 'NO') y guarda la fecha y el motivo.
# Las estimaciones inactivas quedan excluidas de todos los
# análisis y pueden reactivarse.
# ============================================================

from db.conexion import consultar, consultar_uno, ejecutar, confirmar


SELECT_ESTIMACION = """
    SELECT
        e.estimacion_id,
        e.cultivo_id,
        e.campania_id,
        e.provincia_id,
        e.region_id,
        e.superficie_sembrada_ha,
        e.superficie_cosechada_ha,
        e.produccion_tm,
        e.rendimiento_kgxha,
        e.porcentaje_cosechado,
        e.activa,
        e.fecha_baja,
        e.motivo_baja,
        c.cultivo_nombre,
        ca.campania,
        p.provincia_nombre,
        r.region_nombre

    FROM estimacion e

    JOIN cultivo c
        ON e.cultivo_id = c.cultivo_id

    JOIN campania ca
        ON e.campania_id = ca.campania_id

    JOIN provincia p
        ON e.provincia_id = p.provincia_id

    JOIN region r
        ON e.region_id = r.region_id
"""


class Estimacion:

    def __init__(
        self,
        estimacion_id,
        cultivo_id,
        campania_id,
        provincia_id,
        region_id,
        superficie_sembrada_ha,
        superficie_cosechada_ha,
        produccion_tm,
        rendimiento_kgxha,
        porcentaje_cosechado,
        activa="SI",
        fecha_baja=None,
        motivo_baja=None,
        cultivo_nombre=None,
        campania=None,
        provincia_nombre=None,
        region_nombre=None
    ):
        self.estimacion_id = estimacion_id
        self.cultivo_id = cultivo_id
        self.campania_id = campania_id
        self.provincia_id = provincia_id
        self.region_id = region_id
        self.superficie_sembrada_ha = superficie_sembrada_ha
        self.superficie_cosechada_ha = superficie_cosechada_ha
        self.produccion_tm = produccion_tm
        self.rendimiento_kgxha = rendimiento_kgxha
        self.porcentaje_cosechado = porcentaje_cosechado
        self.activa = activa
        self.fecha_baja = fecha_baja
        self.motivo_baja = motivo_baja

        # Descripciones de las dimensiones (para mostrar)
        self.cultivo_nombre = cultivo_nombre
        self.campania = campania
        self.provincia_nombre = provincia_nombre
        self.region_nombre = region_nombre

    def esta_activa(self):
        return self.activa == "SI"

    # --------------------------------------------------------
    # READ
    # --------------------------------------------------------

    @classmethod
    def buscar(cls, estimacion_id):

        fila = consultar_uno(
            SELECT_ESTIMACION + " WHERE e.estimacion_id = %s",
            (estimacion_id,)
        )

        return cls(*fila) if fila else None

    @classmethod
    def listar_por_cultivo_campania(cls, cultivo_id, campania_id, activa="SI"):

        filas = consultar(
            SELECT_ESTIMACION + """
            WHERE e.cultivo_id = %s
              AND e.campania_id = %s
              AND e.activa = %s
            ORDER BY r.region_nombre, p.provincia_nombre
            """,
            (cultivo_id, campania_id, activa)
        )

        return [cls(*fila) for fila in filas]

    @classmethod
    def listar_inactivas(cls):

        filas = consultar(
            SELECT_ESTIMACION + """
            WHERE e.activa = 'NO'
            ORDER BY e.fecha_baja DESC
            """
        )

        return [cls(*fila) for fila in filas]

    @staticmethod
    def contar_por_estado():
        """Cantidad de estimaciones activas e inactivas."""

        filas = consultar("""
            SELECT activa, COUNT(*)
            FROM estimacion
            GROUP BY activa
        """)

        conteo = {"SI": 0, "NO": 0}
        conteo.update(dict(filas))

        return conteo

    @staticmethod
    def ultimo_anio_cargado():
        """
        Último año de inicio presente en estimacion.

        Incluye las estimaciones dadas de baja: la actualización
        incremental no debe volver a cargar una campaña solo
        porque sus registros estén inactivos.
        """

        fila = consultar_uno("""
            SELECT MAX(ca.anio_inicio)
            FROM estimacion e
            JOIN campania ca
                ON e.campania_id = ca.campania_id
        """)

        return fila[0]

    # --------------------------------------------------------
    # DELETE lógico
    # --------------------------------------------------------

    def dar_de_baja(self, motivo):

        ejecutar("""
            UPDATE estimacion
            SET activa = 'NO',
                fecha_baja = NOW(),
                motivo_baja = %s
            WHERE estimacion_id = %s
              AND activa = 'SI'
        """, (motivo, self.estimacion_id))

        confirmar()

        self.activa = "NO"
        self.motivo_baja = motivo

    # --------------------------------------------------------
    # Reactivación (revierte la baja lógica)
    # --------------------------------------------------------

    def reactivar(self):

        ejecutar("""
            UPDATE estimacion
            SET activa = 'SI',
                fecha_baja = NULL,
                motivo_baja = NULL
            WHERE estimacion_id = %s
        """, (self.estimacion_id,))

        confirmar()

        self.activa = "SI"
        self.fecha_baja = None
        self.motivo_baja = None
