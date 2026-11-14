# ============================================================
# PARÁMETROS DE ANÁLISIS
# ============================================================
# Los umbrales usados por las reglas de análisis se guardan en
# MySQL (tabla parametro_analisis) y no quedan fijos en el
# código. La modificación es el UPDATE del CRUD.
# ============================================================

from db.conexion import consultar, consultar_uno, ejecutar, confirmar


# Reglas de validación por parámetro:
# (valor mínimo, valor máximo, debe ser entero)
VALIDACIONES = {
    "umbral_no_cosechado": (0, 100, False),
    "min_caidas_consecutivas": (1, 9, True),
    "max_campanias_ausentes": (0, 9, True)
}


class ParametroAnalisis:

    def __init__(
        self,
        parametro_id=None,
        nombre=None,
        valor=None,
        descripcion=None,
        es_obligatorio="NO"
    ):
        self.parametro_id = parametro_id
        self.nombre = nombre
        self.valor = valor
        self.descripcion = descripcion
        self.es_obligatorio = es_obligatorio

    # READ - Buscar parámetro por nombre
    @classmethod
    def buscar(cls, nombre):

        fila = consultar_uno("""
            SELECT
                parametro_id,
                nombre,
                valor,
                descripcion,
                es_obligatorio
            FROM parametro_analisis
            WHERE nombre = %s
        """, (nombre,))

        return cls(*fila) if fila else None

    # READ - Listar todos los parámetros
    @classmethod
    def listar(cls):

        filas = consultar("""
            SELECT
                parametro_id,
                nombre,
                valor,
                descripcion,
                es_obligatorio
            FROM parametro_analisis
            ORDER BY parametro_id
        """)

        return [cls(*fila) for fila in filas]

    @classmethod
    def valor_de(cls, nombre):
        return cls.buscar(nombre).valor

    # Validación previa a la modificación.
    # Devuelve un mensaje de error o None si el valor es válido.
    def validar(self, nuevo_valor):

        if self.nombre not in VALIDACIONES:
            return None

        minimo, maximo, entero = VALIDACIONES[self.nombre]

        if entero and nuevo_valor != int(nuevo_valor):
            return "El valor debe ser un número entero."

        if not minimo <= nuevo_valor <= maximo:
            return f"El valor debe estar entre {minimo} y {maximo}."

        return None

    # UPDATE - Modificación del valor
    def modificar(self, nuevo_valor):

        ejecutar("""
            UPDATE parametro_analisis
            SET valor = %s
            WHERE parametro_id = %s
        """, (nuevo_valor, self.parametro_id))

        confirmar()

        self.valor = nuevo_valor
