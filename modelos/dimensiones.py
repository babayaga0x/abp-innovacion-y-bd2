# ============================================================
# DIMENSIONES DEL MODELO: Cultivo, Region, Provincia, Campania
# ============================================================
# Cada clase representa una tabla catálogo del modelo
# relacional. Los métodos de clase leen la base y devuelven
# instancias, que la interfaz usa para armar las listas de
# selección.
# ============================================================

from db.conexion import consultar, consultar_uno


class Cultivo:

    def __init__(self, cultivo_id, cultivo_nombre):
        self.cultivo_id = cultivo_id
        self.cultivo_nombre = cultivo_nombre

    def __str__(self):
        return self.cultivo_nombre

    @classmethod
    def listar(cls):

        filas = consultar("""
            SELECT cultivo_id, cultivo_nombre
            FROM cultivo
            ORDER BY cultivo_nombre
        """)

        return [cls(*fila) for fila in filas]


class Region:

    def __init__(self, region_id, region_nombre):
        self.region_id = region_id
        self.region_nombre = region_nombre

    def __str__(self):
        return self.region_nombre

    @classmethod
    def listar(cls):

        filas = consultar("""
            SELECT region_id, region_nombre
            FROM region
            ORDER BY region_nombre
        """)

        return [cls(*fila) for fila in filas]


class Provincia:

    def __init__(self, provincia_id, provincia_nombre, region_id):
        self.provincia_id = provincia_id
        self.provincia_nombre = provincia_nombre
        self.region_id = region_id

    def __str__(self):
        return self.provincia_nombre

    @classmethod
    def listar(cls):

        filas = consultar("""
            SELECT provincia_id, provincia_nombre, region_id
            FROM provincia
            ORDER BY provincia_nombre
        """)

        return [cls(*fila) for fila in filas]


class Campania:

    def __init__(self, campania_id, campania, anio_inicio):
        self.campania_id = campania_id
        self.campania = campania
        self.anio_inicio = anio_inicio

    def __str__(self):
        return self.campania

    @classmethod
    def listar(cls):

        filas = consultar("""
            SELECT campania_id, campania, anio_inicio
            FROM campania
            ORDER BY anio_inicio
        """)

        return [cls(*fila) for fila in filas]

    @staticmethod
    def rango_cargado():
        """Primer y último año de inicio con estimaciones activas."""

        return consultar_uno("""
            SELECT
                MIN(ca.anio_inicio),
                MAX(ca.anio_inicio)
            FROM estimacion e
            JOIN campania ca
                ON e.campania_id = ca.campania_id
            WHERE e.activa = 'SI'
        """)

    @staticmethod
    def formatear_rango(anio_desde, anio_hasta):
        return (
            f"{anio_desde}/{anio_desde + 1} - "
            f"{anio_hasta}/{anio_hasta + 1}"
        )
