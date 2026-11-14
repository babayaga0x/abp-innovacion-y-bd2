import mysql.connector
from getpass import getpass

# ============================================================
# Conexión con MySQL
# ============================================================

conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password=getpass("Ingrese la contraseña de MySQL: "),
    database="estimaciones_agricolas",
    allow_local_infile=True
)

print("Conexión exitosa")
 
cursor = conexion.cursor()

# ============================================================
# Creación objeto "Cultivo"
# ============================================================

class Cultivo:

    def __init__(self, cultivo_id, cultivo_nombre):
        self.cultivo_id = cultivo_id
        self.cultivo_nombre = cultivo_nombre


# ============================================================
# Creación objeto "Region"
# ============================================================

class Region:

    def __init__(self, region_id, region_nombre):
        self.region_id = region_id
        self.region_nombre = region_nombre


# ============================================================
# Creación objeto "Provincia"
# ============================================================

class Provincia:

    def __init__(self, provincia_id, provincia_nombre, region_id):
        self.provincia_id = provincia_id
        self.provincia_nombre = provincia_nombre
        self.region_id = region_id



# ============================================================
# Creación objeto "Campania"
# ============================================================

class Campania:

    def __init__(self, campania_id, campania, anio_inicio):
        self.campania_id = campania_id
        self.campania = campania
        self.anio_inicio = anio_inicio



# ============================================================
# Creación objeto "Estimacion"
# ============================================================

class Estimacion:

    def __init__(self, estimacion_id, cultivo_id, campania_id, provincia_id, region_id, superficie_sembrada_ha, superficie_cosechada_ha, produccion_tm, rendimiento_kgxha, porcentaje_cosechado):
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

    








# ============================================================
# Creación objeto "ParametroAnalisis"

# PARÁMETROS DE ANÁLISIS
# Configuración de criterios utilizados
# ============================================================


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
    @staticmethod
    def buscar(nombre):

        cursor.execute("""
        SELECT
            parametro_id,
            nombre,
            valor,
            descripcion,
            es_obligatorio
        FROM parametro_analisis
        WHERE nombre = %s
        """, (nombre,))

        fila = cursor.fetchone()

        if fila is None:
            return None

        return ParametroAnalisis(
            fila[0],
            fila[1],
            fila[2],
            fila[3],
            fila[4]
        )


    # READ - Listar todos los parámetros
    @staticmethod
    def listar():

        cursor.execute("""
        SELECT
            parametro_id,
            nombre,
            valor,
            descripcion,
            es_obligatorio
        FROM parametro_analisis
        ORDER BY parametro_id
        """)

        filas = cursor.fetchall()

        parametros = []

        for fila in filas:

            parametro = ParametroAnalisis(
                fila[0],
                fila[1],
                fila[2],
                fila[3],
                fila[4]
            )

            parametros.append(parametro)

        return parametros


    # UPDATE - Modificación del valor
    def modificar(self, nuevo_valor):

        cursor.execute("""
        UPDATE parametro_analisis
        SET valor = %s
        WHERE parametro_id = %s
        """, (
            nuevo_valor,
            self.parametro_id
        ))

        conexion.commit()

        self.valor = nuevo_valor


    
# ============================================================
# Creación tabla "parametro_analisis"
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS parametro_analisis (
    parametro_id INT AUTO_INCREMENT PRIMARY KEY,

    nombre VARCHAR(100) NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    descripcion VARCHAR(255),

    es_obligatorio ENUM('SI', 'NO')
        NOT NULL DEFAULT 'NO',

    UNIQUE (nombre)
)
""")

conexion.commit()

print("Tabla parametro_analisis creada correctamente")


# ============================================================
# Parámetros iniciales del análisis
# ============================================================

parametros_iniciales = [
    (
        "umbral_no_cosechado",
        20,
        "Porcentaje máximo antes de considerar desfavorable la superficie no cosechada",
        "SI"
    ),
    (
        "min_caidas_consecutivas",
        3,
        "Cantidad mínima de caídas consecutivas para Situación Desfavorable 3",
        "SI"
    ),
    (
        "max_campanias_ausentes",
        2,
        "Máximo de campañas ausentes admitidas dentro de una racha de caídas",
        "SI"
    )
]


cursor.executemany("""
INSERT IGNORE INTO parametro_analisis
    (nombre, valor, descripcion, es_obligatorio)
VALUES (%s, %s, %s, %s)
""", parametros_iniciales)

conexion.commit()

print("Parámetros de análisis cargados correctamente")



# ============================================================
# Lectura de parámetros utilizados por los análisis
# ============================================================

parametro_umbral = ParametroAnalisis.buscar("umbral_no_cosechado")
parametro_min_caidas = ParametroAnalisis.buscar("min_caidas_consecutivas")
parametro_max_ausentes = ParametroAnalisis.buscar("max_campanias_ausentes")

UMBRAL_NO_COSECHADO = float(parametro_umbral.valor)
MIN_CAIDAS_CONSECUTIVAS = int(parametro_min_caidas.valor)
MAX_CAMPANIAS_AUSENTES = int(parametro_max_ausentes.valor)



# ============================================================
# Creación objeto "AnalisisRegional"
# ============================================================

class AnalisisRegional:

    def __init__(self, analisis_id, cultivo_id, campania_id, region_id):
        self.analisis_id = analisis_id
        self.cultivo_id = cultivo_id
        self.campania_id = campania_id
        self.region_id = region_id

# ============================================================
# Creación tabla "analisis_regional"
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS analisis_regional (
    analisis_id INT AUTO_INCREMENT PRIMARY KEY,
    cultivo_id INT NOT NULL,
    campania_id INT NOT NULL,
    region_id INT NOT NULL,

    UNIQUE (cultivo_id, campania_id, region_id),

    FOREIGN KEY (cultivo_id) REFERENCES cultivo(cultivo_id),
    FOREIGN KEY (campania_id) REFERENCES campania(campania_id),
    FOREIGN KEY (region_id) REFERENCES region(region_id)
)
""")

conexion.commit()
print("Tabla analisis_regional creada correctamente")


# ============================================================
# Carga de combinaciones únicas desde la tabla estimacion:
# cultivo + campaña + región
# ============================================================

cursor.execute("""
INSERT IGNORE INTO analisis_regional
    (cultivo_id, campania_id, region_id)

SELECT DISTINCT
    e.cultivo_id,
    e.campania_id,
    e.region_id

FROM estimacion e
""")

conexion.commit()


print("Tabla analisis_regional actualizada correctamente")

# ============================================================
# Creación objeto "SituacionDesfavorable1"
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
        es_desfavorable
    ):
        self.situacion_1_id = situacion_1_id
        self.analisis_id = analisis_id
        self.superficie_sembrada_ha = superficie_sembrada_ha
        self.superficie_cosechada_ha = superficie_cosechada_ha
        self.superficie_no_cosechada_ha = superficie_no_cosechada_ha
        self.porcentaje_no_cosechado = porcentaje_no_cosechado
        self.es_desfavorable = es_desfavorable

# ============================================================
# Creación tabla "situacion_desfavorable_1"
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS situacion_desfavorable_1 (
    situacion_1_id INT AUTO_INCREMENT PRIMARY KEY,
    analisis_id INT NOT NULL,

    superficie_sembrada_ha DECIMAL(15,2),
    superficie_cosechada_ha DECIMAL(15,2),
    superficie_no_cosechada_ha DECIMAL(15,2),
    porcentaje_no_cosechado DECIMAL(6,2),

    es_desfavorable CHAR(2) NOT NULL,

    UNIQUE (analisis_id),

    FOREIGN KEY (analisis_id)
        REFERENCES analisis_regional(analisis_id)
)
""")

conexion.commit()

print("Tabla situacion_desfavorable_1 creada correctamente")

# ============================================================
# Cálculo y carga de Situación Desfavorable 1
# Superficie no cosechada por cultivo + campaña + región
# ============================================================

cursor.execute("""
INSERT INTO situacion_desfavorable_1 (
    analisis_id,
    superficie_sembrada_ha,
    superficie_cosechada_ha,
    superficie_no_cosechada_ha,
    porcentaje_no_cosechado,
    es_desfavorable
)

SELECT
    ar.analisis_id,

    SUM(e.superficie_sembrada_ha),

    SUM(e.superficie_cosechada_ha),

    SUM(e.superficie_sembrada_ha)
        - SUM(e.superficie_cosechada_ha),

    CASE
        WHEN SUM(e.superficie_sembrada_ha) > 0
        THEN ROUND(
            (
                SUM(e.superficie_sembrada_ha)
                - SUM(e.superficie_cosechada_ha)
            )
            / SUM(e.superficie_sembrada_ha) * 100,
            2
        )
        ELSE NULL
    END,

    CASE
        WHEN SUM(e.superficie_sembrada_ha) > 0
         AND (
            (
                SUM(e.superficie_sembrada_ha)
                - SUM(e.superficie_cosechada_ha)
            )
            / SUM(e.superficie_sembrada_ha) * 100
         ) > %s
        THEN 'SI'
        ELSE 'NO'
    END

FROM analisis_regional ar

JOIN estimacion e
    ON e.cultivo_id = ar.cultivo_id
    AND e.campania_id = ar.campania_id
    AND e.region_id = ar.region_id

GROUP BY ar.analisis_id

ON DUPLICATE KEY UPDATE
    superficie_sembrada_ha = VALUES(superficie_sembrada_ha),
    superficie_cosechada_ha = VALUES(superficie_cosechada_ha),
    superficie_no_cosechada_ha = VALUES(superficie_no_cosechada_ha),
    porcentaje_no_cosechado = VALUES(porcentaje_no_cosechado),
    es_desfavorable = VALUES(es_desfavorable)
""", (UMBRAL_NO_COSECHADO,))

conexion.commit()

print("Situación desfavorable 1 calculada correctamente")

# ============================================================
# Creación objeto "SituacionDesfavorable2"
# ============================================================

class SituacionDesfavorable2:

    def __init__(
        self,
        situacion_2_id,
        analisis_id,
        rendimiento_regional_kgxha,
        rendimiento_nacional_kgxha,
        diferencia_rendimiento_kgxha,
        es_desfavorable
    ):
        self.situacion_2_id = situacion_2_id
        self.analisis_id = analisis_id
        self.rendimiento_regional_kgxha = rendimiento_regional_kgxha
        self.rendimiento_nacional_kgxha = rendimiento_nacional_kgxha
        self.diferencia_rendimiento_kgxha = diferencia_rendimiento_kgxha
        self.es_desfavorable = es_desfavorable


# ============================================================
# Creación tabla "situacion_desfavorable_2"
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS situacion_desfavorable_2 (
    situacion_2_id INT AUTO_INCREMENT PRIMARY KEY,
    analisis_id INT NOT NULL,

    rendimiento_regional_kgxha DECIMAL(15,2),
    rendimiento_nacional_kgxha DECIMAL(15,2),
    diferencia_rendimiento_kgxha DECIMAL(15,2),

    es_desfavorable CHAR(2),

    UNIQUE (analisis_id),

    FOREIGN KEY (analisis_id)
        REFERENCES analisis_regional(analisis_id)
)
""")

conexion.commit()

print("Tabla situacion_desfavorable_2 creada correctamente")

# ============================================================
# Cálculo y carga de Situación Desfavorable 2
# Rendimiento regional vs rendimiento nacional
# por cultivo y campaña
# ============================================================

cursor.execute("""
INSERT INTO situacion_desfavorable_2 (
    analisis_id,
    rendimiento_regional_kgxha,
    rendimiento_nacional_kgxha,
    diferencia_rendimiento_kgxha,
    es_desfavorable
)

SELECT
    ar.analisis_id,

    -- Rendimiento regional
    CASE
        WHEN SUM(
            CASE
                WHEN e.region_id = ar.region_id
                THEN e.superficie_cosechada_ha
                ELSE 0
            END
        ) > 0
        THEN ROUND(
            SUM(
                CASE
                    WHEN e.region_id = ar.region_id
                    THEN e.produccion_tm
                    ELSE 0
                END
            ) * 1000
            /
            SUM(
                CASE
                    WHEN e.region_id = ar.region_id
                    THEN e.superficie_cosechada_ha
                    ELSE 0
                END
            ),
            2
        )
        ELSE NULL
    END AS rendimiento_regional,

    -- Rendimiento nacional
    CASE
        WHEN SUM(e.superficie_cosechada_ha) > 0
        THEN ROUND(
            SUM(e.produccion_tm) * 1000
            / SUM(e.superficie_cosechada_ha),
            2
        )
        ELSE NULL
    END AS rendimiento_nacional,

    -- Diferencia regional - nacional
    CASE
        WHEN SUM(
            CASE
                WHEN e.region_id = ar.region_id
                THEN e.superficie_cosechada_ha
                ELSE 0
            END
        ) > 0
        AND SUM(e.superficie_cosechada_ha) > 0
        THEN ROUND(
            (
                SUM(
                    CASE
                        WHEN e.region_id = ar.region_id
                        THEN e.produccion_tm
                        ELSE 0
                    END
                ) * 1000
                /
                SUM(
                    CASE
                        WHEN e.region_id = ar.region_id
                        THEN e.superficie_cosechada_ha
                        ELSE 0
                    END
                )
            )
            -
            (
                SUM(e.produccion_tm) * 1000
                / SUM(e.superficie_cosechada_ha)
            ),
            2
        )
        ELSE NULL
    END,

    -- Situación desfavorable
    CASE
        WHEN SUM(
            CASE
                WHEN e.region_id = ar.region_id
                THEN e.superficie_cosechada_ha
                ELSE 0
            END
        ) = 0
        OR SUM(e.superficie_cosechada_ha) = 0
        THEN NULL

        WHEN
            (
                SUM(
                    CASE
                        WHEN e.region_id = ar.region_id
                        THEN e.produccion_tm
                        ELSE 0
                    END
                ) * 1000
                /
                SUM(
                    CASE
                        WHEN e.region_id = ar.region_id
                        THEN e.superficie_cosechada_ha
                        ELSE 0
                    END
                )
            )
            <
            (
                SUM(e.produccion_tm) * 1000
                / SUM(e.superficie_cosechada_ha)
            )
        THEN 'SI'

        ELSE 'NO'
    END

FROM analisis_regional ar

JOIN estimacion e
    ON e.cultivo_id = ar.cultivo_id
    AND e.campania_id = ar.campania_id

GROUP BY
    ar.analisis_id,
    ar.region_id

ON DUPLICATE KEY UPDATE
    rendimiento_regional_kgxha = VALUES(rendimiento_regional_kgxha),
    rendimiento_nacional_kgxha = VALUES(rendimiento_nacional_kgxha),
    diferencia_rendimiento_kgxha = VALUES(diferencia_rendimiento_kgxha),
    es_desfavorable = VALUES(es_desfavorable)
""")

conexion.commit()

print("Situación desfavorable 2 calculada correctamente")



# ============================================================
# SITUACIÓN DESFAVORABLE 3.a
# Caídas consecutivas de producción

# Creación objeto "SituacionDesfavorable3"
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
        es_desfavorable
    ):
        self.situacion_3_id = situacion_3_id
        self.analisis_id = analisis_id
        self.produccion_actual_tm = produccion_actual_tm
        self.produccion_anterior_tm = produccion_anterior_tm
        self.variacion_produccion_pct = variacion_produccion_pct
        self.hay_caida = hay_caida
        self.caidas_consecutivas = caidas_consecutivas
        self.es_desfavorable = es_desfavorable


# ------------------------------------------------------------
# Creación tabla "situacion_desfavorable_3.a"
# ------------------------------------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS situacion_desfavorable_3 (
    situacion_3_id INT AUTO_INCREMENT PRIMARY KEY,
    analisis_id INT NOT NULL,

    produccion_actual_tm DECIMAL(15,2),
    produccion_anterior_tm DECIMAL(15,2),
    variacion_produccion_pct DECIMAL(10,2),

    hay_caida CHAR(2),
    caidas_consecutivas INT NOT NULL DEFAULT 0,
    es_desfavorable CHAR(2) NOT NULL,

    UNIQUE (analisis_id),

    FOREIGN KEY (analisis_id)
        REFERENCES analisis_regional(analisis_id)
)
""")

conexion.commit()

# print("Tabla situacion_desfavorable_3 creada correctamente")


# ------------------------------------------------------------
# Producción regional por:
# cultivo + región + campaña
# ------------------------------------------------------------

cursor.execute("""
SELECT
    ar.analisis_id,
    ar.cultivo_id,
    ar.region_id,
    ca.anio_inicio,
    SUM(e.produccion_tm) AS produccion_tm

FROM analisis_regional ar

JOIN campania ca
    ON ca.campania_id = ar.campania_id

JOIN estimacion e
    ON e.cultivo_id = ar.cultivo_id
    AND e.campania_id = ar.campania_id
    AND e.region_id = ar.region_id

GROUP BY
    ar.analisis_id,
    ar.cultivo_id,
    ar.region_id,
    ca.anio_inicio

ORDER BY
    ar.cultivo_id,
    ar.region_id,
    ca.anio_inicio
""")

filas_produccion = cursor.fetchall()


# ------------------------------------------------------------
# Criterio metodológico:
#
# - Se analiza cada cultivo y región cronológicamente.
#
# - Existe una caída cuando:
#       producción actual < producción anterior
#
# - Para considerar las caídas como parte de una misma racha
#   se toleran como máximo 2 campañas ausentes EN TOTAL
#   dentro del tramo.
#
# - Las campañas ausentes pueden estar juntas o separadas.
#
# - Si la producción no vuelve a caer, la racha se reinicia.
#
# - Si las ausencias acumuladas superan 2, se descarta la
#   parte más antigua de la racha hasta volver a cumplir
#   la tolerancia.
#
# - 3 o más caídas consecutivas válidas:
#       Situación Desfavorable 3.a = SI
# ------------------------------------------------------------


resultados_situacion_3 = []

cultivo_anterior = None
region_anterior = None
anio_anterior = None
produccion_anterior = None

# Guarda la cantidad de campañas ausentes correspondiente
# a cada caída que integra la racha actual.
ausencias_racha = []


for fila in filas_produccion:

    analisis_id = fila[0]
    cultivo_id = fila[1]
    region_id = fila[2]
    anio_inicio = fila[3]
    produccion_actual = fila[4]

    hay_caida = None
    variacion_produccion_pct = None

    misma_serie = (
        cultivo_id == cultivo_anterior
        and region_id == region_anterior
    )


    # --------------------------------------------------------
    # Comparación con el registro anterior
    # del mismo cultivo y región
    # --------------------------------------------------------

    if (
        misma_serie
        and produccion_actual is not None
        and produccion_anterior is not None
    ):

        # Cantidad de campañas sin datos entre ambos registros
        ausentes_entre_registros = max(
            anio_inicio - anio_anterior - 1,
            0
        )


        # Variación porcentual de producción
        if produccion_anterior > 0:

            variacion_produccion_pct = round(
                (
                    float(produccion_actual)
                    - float(produccion_anterior)
                )
                / float(produccion_anterior)
                * 100,
                2
            )


        # ----------------------------------------------------
        # Se detecta una caída de producción
        # ----------------------------------------------------

        if produccion_actual < produccion_anterior:

            hay_caida = "SI"

            # Incorporamos las campañas ausentes
            # correspondientes a esta nueva caída
            ausencias_racha.append(
                ausentes_entre_registros
            )


            # Si toda la racha supera la tolerancia máxima,
            # eliminamos las caídas más antiguas hasta que
            # el tramo vuelva a tener como máximo 2 ausencias.
            while (
                sum(ausencias_racha)
                > MAX_CAMPANIAS_AUSENTES
                and len(ausencias_racha) > 0
            ):

                ausencias_racha.pop(0)


        # ----------------------------------------------------
        # La producción no disminuyó
        # ----------------------------------------------------

        else:

            hay_caida = "NO"

            # Se interrumpe completamente la racha
            ausencias_racha = []


    # --------------------------------------------------------
    # Primer registro de una serie cultivo + región
    # --------------------------------------------------------

    else:

        ausencias_racha = []


    # Cantidad de caídas consecutivas válidas
    caidas_consecutivas = len(ausencias_racha)


    # --------------------------------------------------------
    # Clasificación Situación Desfavorable 3.a
    # --------------------------------------------------------

    if caidas_consecutivas >= MIN_CAIDAS_CONSECUTIVAS:
        es_desfavorable = "SI"
    else:
        es_desfavorable = "NO"


    # --------------------------------------------------------
    # Guardamos el resultado de esta campaña
    # --------------------------------------------------------

    resultados_situacion_3.append(
        (
            analisis_id,
            produccion_actual,
            produccion_anterior if misma_serie else None,
            variacion_produccion_pct,
            hay_caida,
            caidas_consecutivas,
            es_desfavorable
        )
    )


    # El registro actual pasa a ser el anterior
    # para la próxima comparación

    cultivo_anterior = cultivo_id
    region_anterior = region_id
    anio_anterior = anio_inicio
    produccion_anterior = produccion_actual


# ------------------------------------------------------------
# Carga de resultados en MySQL
# ------------------------------------------------------------

# Esta tabla contiene resultados calculados.
# Por eso se reconstruye en cada ejecución.

cursor.execute("""
DELETE FROM situacion_desfavorable_3
""")


consulta_insert_situacion_3 = """
INSERT INTO situacion_desfavorable_3 (
    analisis_id,
    produccion_actual_tm,
    produccion_anterior_tm,
    variacion_produccion_pct,
    hay_caida,
    caidas_consecutivas,
    es_desfavorable
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""


cursor.executemany(
    consulta_insert_situacion_3,
    resultados_situacion_3
)

conexion.commit()

# print("Situación desfavorable 3 calculada correctamente")




# ============================================================
# SITUACIÓN DESFAVORABLE 3.b
# Evaluación de superficie cosechada y rendimiento
# dentro de las rachas de caída de producción
# ============================================================


# Creación objeto "SituacionDesfavorable3B"

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
        conclusion
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


# ============================================================
# Creación tabla "situacion_desfavorable_3b"
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS situacion_desfavorable_3b (

    situacion_3b_id INT AUTO_INCREMENT PRIMARY KEY,

    cultivo_id INT NOT NULL,
    region_id INT NOT NULL,

    analisis_id_inicio INT NOT NULL,
    analisis_id_fin INT NOT NULL,

    cantidad_caidas_produccion INT NOT NULL,
    cantidad_caidas_superficie INT NOT NULL,
    cantidad_caidas_rendimiento INT NOT NULL,

    conclusion VARCHAR(180) NOT NULL,

    FOREIGN KEY (cultivo_id)
        REFERENCES cultivo(cultivo_id),

    FOREIGN KEY (region_id)
        REFERENCES region(region_id),

    FOREIGN KEY (analisis_id_inicio)
        REFERENCES analisis_regional(analisis_id),

    FOREIGN KEY (analisis_id_fin)
        REFERENCES analisis_regional(analisis_id)
)
""")

conexion.commit()



# ------------------------------------------------------------
# Identificación de rachas de producción ya detectadas
# ------------------------------------------------------------

cursor.execute("""
SELECT
    s3.analisis_id,
    ar.cultivo_id,
    ar.region_id,
    ca.anio_inicio,
    s3.caidas_consecutivas
FROM situacion_desfavorable_3 s3
JOIN analisis_regional ar
    ON s3.analisis_id = ar.analisis_id
JOIN campania ca
    ON ar.campania_id = ca.campania_id
WHERE s3.hay_caida = 'SI'
ORDER BY
    ar.cultivo_id,
    ar.region_id,
    ca.anio_inicio
""")

filas_caidas = cursor.fetchall()

rachas_produccion = []
racha_actual = []

cultivo_anterior = None
region_anterior = None
numero_caida_anterior = None


for fila in filas_caidas:

    analisis_id = fila[0]
    cultivo_id = fila[1]
    region_id = fila[2]
    anio_inicio = fila[3]
    numero_caida = fila[4]

    continua_racha = (
        cultivo_id == cultivo_anterior
        and region_id == region_anterior
        and numero_caida_anterior is not None
        and numero_caida == numero_caida_anterior + 1
    )

    if numero_caida == 1:
        # Comienza una nueva racha
        if len(racha_actual) >= MIN_CAIDAS_CONSECUTIVAS:
            rachas_produccion.append(racha_actual)

        racha_actual = [fila]

    elif continua_racha:
        # Continúa la racha existente
        racha_actual.append(fila)

    else:
        # Se cortó la secuencia anterior
        if len(racha_actual) >= MIN_CAIDAS_CONSECUTIVAS:
            rachas_produccion.append(racha_actual)

        racha_actual = []

    cultivo_anterior = cultivo_id
    region_anterior = region_id
    numero_caida_anterior = numero_caida


# Guarda la última racha si corresponde
if len(racha_actual) >= MIN_CAIDAS_CONSECUTIVAS:
    rachas_produccion.append(racha_actual)



# print("Rachas de producción con", MIN_CAIDAS_CONSECUTIVAS, "o más caídas:", len(rachas_produccion))





# ------------------------------------------------------------
# Criterio de conclusión
# ------------------------------------------------------------
# Dentro de cada racha de caída sostenida de producción se cuenta:
#
# - cuántos tramos presentan reducción de superficie cosechada;
# - cuántos tramos presentan disminución del rendimiento.
#
# La conclusión se determina comparando ambos conteos:
#
# 1. Si las reducciones de superficie son mayores que las
#    disminuciones de rendimiento:
#    → mayor incidencia de la reducción de superficie cosechada.
#
# 2. Si las disminuciones de rendimiento son mayores que las
#    reducciones de superficie:
#    → mayor incidencia de la disminución del rendimiento.
#
# 3. Si ambos conteos son iguales y mayores que cero:
#    → incidencia de ambas variables.
#
# 4. Si ambos conteos son cero:
#    → caída no determinada por reducción de superficie cosechada
#      ni disminución de rendimiento.
# ------------------------------------------------------------


# ------------------------------------------------------------
# Evaluación de superficie cosechada y rendimiento
# en las rachas de producción ya identificadas
# ------------------------------------------------------------

cursor.execute("""
SELECT
    ar.analisis_id,
    ar.cultivo_id,
    ar.region_id,
    ca.anio_inicio,
    c.cultivo_nombre,
    r.region_nombre,
    s1.superficie_cosechada_ha,
    s2.rendimiento_regional_kgxha
FROM analisis_regional ar
JOIN campania ca
    ON ar.campania_id = ca.campania_id
JOIN cultivo c
    ON ar.cultivo_id = c.cultivo_id
JOIN region r
    ON ar.region_id = r.region_id
JOIN situacion_desfavorable_1 s1
    ON ar.analisis_id = s1.analisis_id
JOIN situacion_desfavorable_2 s2
    ON ar.analisis_id = s2.analisis_id
ORDER BY
    ar.cultivo_id,
    ar.region_id,
    ca.anio_inicio
""")

filas_metricas = cursor.fetchall()


# Guardamos los datos de cada análisis y el registro anterior
datos_analisis = {}
anterior_por_analisis = {}

cultivo_anterior = None
region_anterior = None
analisis_anterior = None


for fila in filas_metricas:

    analisis_id = fila[0]
    cultivo_id = fila[1]
    region_id = fila[2]

    datos_analisis[analisis_id] = {
        "anio_inicio": fila[3],
        "cultivo_nombre": fila[4],
        "region_nombre": fila[5],
        "superficie": fila[6],
        "rendimiento": fila[7]
    }

    misma_serie = (
        cultivo_id == cultivo_anterior
        and region_id == region_anterior
    )

    if misma_serie:
        anterior_por_analisis[analisis_id] = analisis_anterior
    else:
        anterior_por_analisis[analisis_id] = None

    cultivo_anterior = cultivo_id
    region_anterior = region_id
    analisis_anterior = analisis_id


# ------------------------------------------------------------
# Conteo dentro de cada racha
# ------------------------------------------------------------

resultados_3b = []


for racha in rachas_produccion:

    cantidad_caidas_superficie = 0
    cantidad_caidas_rendimiento = 0

    for fila_caida in racha:

        analisis_id_actual = fila_caida[0]

        analisis_id_anterior = anterior_por_analisis[
            analisis_id_actual
        ]

        actual = datos_analisis[analisis_id_actual]
        anterior = datos_analisis[analisis_id_anterior]


        # Caída de superficie cosechada
        if (
            actual["superficie"] is not None
            and anterior["superficie"] is not None
            and actual["superficie"] < anterior["superficie"]
        ):
            cantidad_caidas_superficie += 1


        # Caída de rendimiento
        if (
            actual["rendimiento"] is not None
            and anterior["rendimiento"] is not None
            and actual["rendimiento"] < anterior["rendimiento"]
        ):
            cantidad_caidas_rendimiento += 1


    cantidad_caidas_produccion = len(racha)


    # Conclusión de la racha

    if cantidad_caidas_superficie > cantidad_caidas_rendimiento:

        conclusion = (
            "Caída con mayor incidencia de la reducción "
            "de superficie cosechada"
        )

    elif cantidad_caidas_rendimiento > cantidad_caidas_superficie:

        conclusion = (
            "Caída con mayor incidencia de la disminución "
            "del rendimiento"
        )

    elif (
        cantidad_caidas_superficie > 0
        and cantidad_caidas_rendimiento > 0
    ):

        conclusion = (
            "Caída con incidencia de la reducción de superficie "
            "cosechada y de la disminución del rendimiento"
        )

    else:

        conclusion = (
            "Caída no determinada por reducción de superficie "
            "cosechada ni disminución de rendimiento"
        )


    resultados_3b.append(
        (
            racha[0][1],       # cultivo_id
            racha[0][2],       # region_id
            racha[0][0],       # primer analisis_id de la racha
            racha[-1][0],      # último analisis_id de la racha
            cantidad_caidas_produccion,
            cantidad_caidas_superficie,
            cantidad_caidas_rendimiento,
            conclusion
        )
    )




# ------------------------------------------------------------
# Carga de resultados de Situación Desfavorable 3.b
# ------------------------------------------------------------

cursor.execute("""
DELETE FROM situacion_desfavorable_3b
""")

consulta_insert_3b = """
INSERT INTO situacion_desfavorable_3b (
    cultivo_id,
    region_id,
    analisis_id_inicio,
    analisis_id_fin,
    cantidad_caidas_produccion,
    cantidad_caidas_superficie,
    cantidad_caidas_rendimiento,
    conclusion
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

cursor.executemany(
    consulta_insert_3b,
    resultados_3b
)

conexion.commit()

# print("Situación desfavorable 3.b calculada y cargada correctamente:", len(resultados_3b),"rachas")




# ============================================================
# VIEW - FOCOS CRÍTICOS
# ============================================================
# Se considera foco crítico a una combinación de cultivo,
# región y campaña que presenta simultáneamente:
#
# - Situación desfavorable 1: superficie no cosechada.
# - Situación desfavorable 2: rendimiento regional inferior
#   al rendimiento nacional.
# - Situación desfavorable 3: caída sostenida de producción.
# ============================================================

cursor.execute("""
CREATE OR REPLACE VIEW vw_foco_critico AS

SELECT
    ar.analisis_id,

    c.cultivo_nombre AS cultivo,
    r.region_nombre AS region,
    ca.campania,

    s1.porcentaje_no_cosechado,

    s2.rendimiento_regional_kgxha,
    s2.rendimiento_nacional_kgxha,

    s3.produccion_actual_tm,
    s3.produccion_anterior_tm,
    s3.variacion_produccion_pct,
    s3.caidas_consecutivas

FROM analisis_regional ar

JOIN cultivo c
    ON ar.cultivo_id = c.cultivo_id

JOIN region r
    ON ar.region_id = r.region_id

JOIN campania ca
    ON ar.campania_id = ca.campania_id

JOIN situacion_desfavorable_1 s1
    ON ar.analisis_id = s1.analisis_id

JOIN situacion_desfavorable_2 s2
    ON ar.analisis_id = s2.analisis_id

JOIN situacion_desfavorable_3 s3
    ON ar.analisis_id = s3.analisis_id

WHERE
    s1.es_desfavorable = 'SI'
    AND s2.es_desfavorable = 'SI'
    AND s3.es_desfavorable = 'SI'
""")

conexion.commit()

# print("VIEW vw_foco_critico creada correctamente")



# ------------------------------------------------------------
# Consulta de la VIEW desde Python
# ------------------------------------------------------------

cursor.execute("""
SELECT *
FROM vw_foco_critico
ORDER BY cultivo, region, campania
""")

focos_criticos = cursor.fetchall()

# print("Focos críticos detectados:", len(focos_criticos))



# ============================================================
# BÚSQUEDA 1 - RESULTADOS DESFAVORABLES POR REGIÓN
# ============================================================
# Permite consultar una región determinada y recuperar todos
# los casos en los que se haya detectado al menos una situación
# desfavorable dentro del período analizado.
#
# Para cada resultado se muestran:
# - región,
# - cultivo,
# - campaña,
# - resultado de la Situación Desfavorable 1,
# - resultado de la Situación Desfavorable 2,
# - resultado de la Situación Desfavorable 3.
#
# La búsqueda devuelve únicamente los registros en los que
# al menos una de las tres situaciones haya sido clasificada
# como desfavorable.
# ============================================================


def buscar_por_region(region_nombre):

    cursor.execute("""
    SELECT
        r.region_nombre,
        c.cultivo_nombre,
        ca.campania,
        s1.es_desfavorable AS situacion_1,
        s2.es_desfavorable AS situacion_2,
        s3.es_desfavorable AS situacion_3

    FROM analisis_regional ar

    JOIN region r
        ON ar.region_id = r.region_id

    JOIN cultivo c
        ON ar.cultivo_id = c.cultivo_id

    JOIN campania ca
        ON ar.campania_id = ca.campania_id

    JOIN situacion_desfavorable_1 s1
        ON ar.analisis_id = s1.analisis_id

    JOIN situacion_desfavorable_2 s2
        ON ar.analisis_id = s2.analisis_id

    JOIN situacion_desfavorable_3 s3
        ON ar.analisis_id = s3.analisis_id

    WHERE r.region_nombre = %s

      AND (
          s1.es_desfavorable = 'SI'
          OR s2.es_desfavorable = 'SI'
          OR s3.es_desfavorable = 'SI'
      )

    ORDER BY
        ca.anio_inicio,
        c.cultivo_nombre
    """, (region_nombre,))

    return cursor.fetchall()


# ============================================================
# BÚSQUEDA 2 - RESULTADOS POR CULTIVO Y CAMPAÑA
# ============================================================
# Permite consultar un cultivo específico dentro de una campaña
# determinada y recuperar su situación en las distintas regiones.
#
# Para cada resultado se muestran:
# - cultivo,
# - campaña,
# - región,
# - resultado de la Situación Desfavorable 1,
# - resultado de la Situación Desfavorable 2,
# - resultado de la Situación Desfavorable 3.
#
# A diferencia de la búsqueda por región, esta consulta utiliza
# dos criterios simultáneos: cultivo y campaña.
# ============================================================

def buscar_por_cultivo_campania(cultivo_nombre, campania):

    cursor.execute("""
    SELECT
        c.cultivo_nombre,
        ca.campania,
        r.region_nombre,
        s1.es_desfavorable AS situacion_1,
        s2.es_desfavorable AS situacion_2,
        s3.es_desfavorable AS situacion_3

    FROM analisis_regional ar

    JOIN cultivo c
        ON ar.cultivo_id = c.cultivo_id

    JOIN campania ca
        ON ar.campania_id = ca.campania_id

    JOIN region r
        ON ar.region_id = r.region_id

    JOIN situacion_desfavorable_1 s1
        ON ar.analisis_id = s1.analisis_id

    JOIN situacion_desfavorable_2 s2
        ON ar.analisis_id = s2.analisis_id

    JOIN situacion_desfavorable_3 s3
        ON ar.analisis_id = s3.analisis_id

    WHERE
        c.cultivo_nombre = %s
        AND ca.campania = %s

    ORDER BY
        r.region_nombre
    """, (cultivo_nombre, campania))

    return cursor.fetchall()






def ver_detalle_por_region_situacion_1():

    cursor.execute("""
        SELECT
            r.region_nombre,
            COUNT(*) AS cantidad_casos

        FROM situacion_desfavorable_1 s1

        JOIN analisis_regional ar
            ON s1.analisis_id = ar.analisis_id

        JOIN region r
            ON ar.region_id = r.region_id

        WHERE s1.es_desfavorable = 'SI'

        GROUP BY r.region_nombre

        ORDER BY r.region_nombre
    """)

    regiones = cursor.fetchall()

    limpiar_pantalla()

    print("\nREGIONES CON CASOS DESFAVORABLES\n")

    for numero, region in enumerate(regiones, start=1):
        print(
            f"{numero}. "
            f"{region[0]:<20}"
            f"{region[1]} casos"
        )

    print()

    opcion_region = input(
        "Seleccione una región o presione ENTER para volver: "
    )

    if opcion_region == "":
        return

    if not opcion_region.isdigit():
        print("\nOpción inválida.")
        return

    numero_region = int(opcion_region)

    if numero_region < 1 or numero_region > len(regiones):
        print("\nOpción inválida.")
        return

    region_seleccionada = regiones[numero_region - 1][0]

    
    ver_detalle_situacion_1(
        region_seleccionada=region_seleccionada
    )

    def ver_detalle_por_cultivo_situacion_1():

        cursor.execute("""
            SELECT
                c.cultivo_nombre,
                COUNT(*) AS cantidad_casos

            FROM situacion_desfavorable_1 s1

            JOIN analisis_regional ar
                ON s1.analisis_id = ar.analisis_id

            JOIN cultivo c
                ON ar.cultivo_id = c.cultivo_id

            WHERE s1.es_desfavorable = 'SI'

            GROUP BY c.cultivo_nombre

            ORDER BY c.cultivo_nombre
        """)

        cultivos = cursor.fetchall()

        print("\nCULTIVOS CON CASOS DESFAVORABLES\n")

        for numero, cultivo in enumerate(cultivos, start=1):
            print(
                f"{numero}. "
                f"{cultivo[0]:<20}"
                f"{cultivo[1]} casos"
            )

        print()

        opcion_cultivo = input(
            "Seleccione un cultivo o presione ENTER para volver: "
        )

        if opcion_cultivo == "":
            return

        if not opcion_cultivo.isdigit():
            print("\nOpción inválida.")
            return

        numero_cultivo = int(opcion_cultivo)

        if numero_cultivo < 1 or numero_cultivo > len(cultivos):
            print("\nOpción inválida.")
            return

        cultivo_seleccionado = cultivos[numero_cultivo - 1][0]

        limpiar_pantalla()

        ver_detalle_situacion_1(
            cultivo_seleccionado=cultivo_seleccionado
        )


def ver_detalle_por_campania_situacion_1():

    cursor.execute("""
        SELECT
            ca.campania,
            COUNT(*) AS cantidad_casos,
            ca.anio_inicio

        FROM situacion_desfavorable_1 s1

        JOIN analisis_regional ar
            ON s1.analisis_id = ar.analisis_id

        JOIN campania ca
            ON ar.campania_id = ca.campania_id

        WHERE s1.es_desfavorable = 'SI'

        GROUP BY
            ca.campania,
            ca.anio_inicio

        ORDER BY ca.anio_inicio
    """)

    campanias = cursor.fetchall()

    print("\nCAMPAÑAS CON CASOS DESFAVORABLES\n")

    for numero, campania in enumerate(campanias, start=1):
        print(
            f"{numero}. "
            f"{campania[0]:<15}"
            f"{campania[1]} casos"
        )

    print()

    opcion_campania = input(
        "Seleccione una campaña o presione ENTER para volver: "
    )

    if opcion_campania == "":
        return

    if not opcion_campania.isdigit():
        print("\nOpción inválida.")
        return

    numero_campania = int(opcion_campania)

    if numero_campania < 1 or numero_campania > len(campanias):
        print("\nOpción inválida.")
        return

    campania_seleccionada = campanias[numero_campania - 1][0]

    limpiar_pantalla()

    ver_detalle_situacion_1(
        campania_seleccionada=campania_seleccionada
    )

    












# ============================================================
# CONFIGURACIÓN PARA CONSULTAS DE SITUACIÓN DESFAVORABLE 1
# ============================================================

import textwrap
import os
from tkinter import Tk, filedialog


def limpiar_pantalla():
    os.system("cls")


ANCHO = 90
SANGRIA_MENU = " " * 10


# ============================================================
# DETALLE POR REGIÓN
# ============================================================

def ver_detalle_por_region_situacion_1():

    cursor.execute("""
        SELECT
            r.region_nombre,
            COUNT(*) AS cantidad_casos

        FROM situacion_desfavorable_1 s1

        JOIN analisis_regional ar
            ON s1.analisis_id = ar.analisis_id

        JOIN region r
            ON ar.region_id = r.region_id

        WHERE s1.es_desfavorable = 'SI'

        GROUP BY r.region_nombre

        ORDER BY r.region_nombre
    """)

    regiones = cursor.fetchall()

    limpiar_pantalla()

    print("\nREGIONES CON CASOS DESFAVORABLES\n")

    for numero, region in enumerate(regiones, start=1):
        print(
            f"{numero}. "
            f"{region[0]:<20}"
            f"{region[1]} casos"
        )

    print()

    opcion_region = input(
        "Seleccione una región o presione ENTER para volver: "
    )

    if opcion_region == "":
        limpiar_pantalla()
        return

    if not opcion_region.isdigit():
        print("\nOpción inválida.")
        input("\nPresione ENTER para volver...")
        limpiar_pantalla()
        return

    numero_region = int(opcion_region)

    if numero_region < 1 or numero_region > len(regiones):
        print("\nOpción inválida.")
        input("\nPresione ENTER para volver...")
        limpiar_pantalla()
        return

    region_seleccionada = regiones[numero_region - 1][0]

    limpiar_pantalla()

    ver_detalle_situacion_1(
        region_seleccionada=region_seleccionada
    )


# ============================================================
# DETALLE POR CULTIVO
# ============================================================

def ver_detalle_por_cultivo_situacion_1():

    cursor.execute("""
        SELECT
            c.cultivo_nombre,
            COUNT(*) AS cantidad_casos

        FROM situacion_desfavorable_1 s1

        JOIN analisis_regional ar
            ON s1.analisis_id = ar.analisis_id

        JOIN cultivo c
            ON ar.cultivo_id = c.cultivo_id

        WHERE s1.es_desfavorable = 'SI'

        GROUP BY c.cultivo_nombre

        ORDER BY c.cultivo_nombre
    """)

    cultivos = cursor.fetchall()

    limpiar_pantalla()

    print("\nCULTIVOS CON CASOS DESFAVORABLES\n")

    for numero, cultivo in enumerate(cultivos, start=1):
        print(
            f"{numero}. "
            f"{cultivo[0]:<20}"
            f"{cultivo[1]} casos"
        )

    print()

    opcion_cultivo = input(
        "Seleccione un cultivo o presione ENTER para volver: "
    )

    if opcion_cultivo == "":
        limpiar_pantalla()
        return

    if not opcion_cultivo.isdigit():
        print("\nOpción inválida.")
        input("\nPresione ENTER para volver...")
        limpiar_pantalla()
        return

    numero_cultivo = int(opcion_cultivo)

    if numero_cultivo < 1 or numero_cultivo > len(cultivos):
        print("\nOpción inválida.")
        input("\nPresione ENTER para volver...")
        limpiar_pantalla()
        return

    cultivo_seleccionado = cultivos[numero_cultivo - 1][0]

    limpiar_pantalla()

    ver_detalle_situacion_1(
        cultivo_seleccionado=cultivo_seleccionado
    )


# ============================================================
# DETALLE POR CAMPAÑA
# ============================================================

def ver_detalle_por_campania_situacion_1():

    cursor.execute("""
        SELECT
            ca.campania,
            COUNT(*) AS cantidad_casos,
            ca.anio_inicio

        FROM situacion_desfavorable_1 s1

        JOIN analisis_regional ar
            ON s1.analisis_id = ar.analisis_id

        JOIN campania ca
            ON ar.campania_id = ca.campania_id

        WHERE s1.es_desfavorable = 'SI'

        GROUP BY
            ca.campania,
            ca.anio_inicio

        ORDER BY ca.anio_inicio
    """)

    campanias = cursor.fetchall()

    limpiar_pantalla()

    print("\nCAMPAÑAS CON CASOS DESFAVORABLES\n")

    for numero, campania in enumerate(campanias, start=1):
        print(
            f"{numero}. "
            f"{campania[0]:<15}"
            f"{campania[1]} casos"
        )

    print()

    opcion_campania = input(
        "Seleccione una campaña o presione ENTER para volver: "
    )

    if opcion_campania == "":
        limpiar_pantalla()
        return

    if not opcion_campania.isdigit():
        print("\nOpción inválida.")
        input("\nPresione ENTER para volver...")
        limpiar_pantalla()
        return

    numero_campania = int(opcion_campania)

    if numero_campania < 1 or numero_campania > len(campanias):
        print("\nOpción inválida.")
        input("\nPresione ENTER para volver...")
        limpiar_pantalla()
        return

    campania_seleccionada = campanias[numero_campania - 1][0]

    limpiar_pantalla()

    ver_detalle_situacion_1(
        campania_seleccionada=campania_seleccionada
    )


# ============================================================
# RESUMEN - SITUACIÓN DESFAVORABLE 1
# Superficie no cosechada
# ============================================================

def consultar_resumen_situacion_1():

    cursor.execute("""
        SELECT
            r.region_nombre,
            c.cultivo_nombre,

            COUNT(DISTINCT ar.campania_id)
                AS campanias_desfavorables,

            SUM(s1.superficie_sembrada_ha)
                AS superficie_sembrada,

            SUM(s1.superficie_no_cosechada_ha)
                AS superficie_no_cosechada,

            ROUND(
                SUM(s1.superficie_no_cosechada_ha)
                / SUM(s1.superficie_sembrada_ha) * 100,
                0
            ) AS porcentaje_no_cosechado

        FROM situacion_desfavorable_1 s1

        JOIN analisis_regional ar
            ON s1.analisis_id = ar.analisis_id

        JOIN region r
            ON ar.region_id = r.region_id

        JOIN cultivo c
            ON ar.cultivo_id = c.cultivo_id

        WHERE s1.es_desfavorable = 'SI'

        GROUP BY
            r.region_nombre,
            c.cultivo_nombre

        ORDER BY
            r.region_nombre ASC,
            c.cultivo_nombre ASC
    """)

    resumen = cursor.fetchall()


    # --------------------------------------------------------
    # Resumen general
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            COUNT(*) AS casos_desfavorables,
            COUNT(DISTINCT ar.region_id) AS regiones_afectadas,
            MIN(ca.anio_inicio) AS anio_desde,
            MAX(ca.anio_inicio) AS anio_hasta

        FROM situacion_desfavorable_1 s1

        JOIN analisis_regional ar
            ON s1.analisis_id = ar.analisis_id

        JOIN campania ca
            ON ar.campania_id = ca.campania_id

        WHERE s1.es_desfavorable = 'SI'
    """)

    resumen_general = cursor.fetchone()

    limpiar_pantalla()

    anio_desde = resumen_general[2]
    anio_hasta = resumen_general[3]

    print("\nRESUMEN GENERAL\n")

    print(
        "Casos desfavorables encontrados:",
        resumen_general[0]
    )

    print(
        "Regiones afectadas:",
        resumen_general[1]
    )

    print(
        f"Período analizado: "
        f"{anio_desde}/{anio_desde + 1} - "
        f"{anio_hasta}/{anio_hasta + 1}"
    )


    # --------------------------------------------------------
    # Tabla resumen
    # --------------------------------------------------------

    print("\n" + "=" * 100)

    print(
        "RESUMEN - SITUACIÓN DESFAVORABLE 1".center(100)
    )

    print("=" * 100)

    print(
        f"{'REGIÓN':<18}"
        f"{'CULTIVO':<20}"
        f"{'CAMPAÑAS':>10}"
        f"{'SEMBRADA':>16}"
        f"{'NO COSECH.':>16}"
        f"{'% NO COSECH.':>16}"
    )

    print("-" * 100)

    region_anterior = None

    for fila in resumen:

        region = fila[0]

        if (
            region_anterior is not None
            and region != region_anterior
        ):
            print()

        region_anterior = region

        cultivo = fila[1]
        campanias = fila[2]

        sembrada = int(
            round(float(fila[3]))
        )

        no_cosechada = int(
            round(float(fila[4]))
        )

        porcentaje = int(
            round(float(fila[5]))
        )

        print(
            f"{region:<18}"
            f"{cultivo:<20}"
            f"{campanias:>10}"
            f"{format(sembrada, ',').replace(',', '.'):>16}"
            f"{format(no_cosechada, ',').replace(',', '.'):>16}"
            f"{porcentaje:>14} %"
        )


    # --------------------------------------------------------
    # Submenú
    # --------------------------------------------------------

    while True:

        print()
        print()
        print("=" * 100)
        print("Menú de consulta detallada:")
        print("=" * 100)

        print()
        print("1. Ver detalle por región")
        print("2. Ver detalle por cultivo")
        print("3. Ver detalle por campaña")
        print("4. Ver todos los casos")
        print("5. Volver al menú principal")

        opcion_detalle = input(
            "\nSeleccione una opción: "
        )


        if opcion_detalle == "1":

            limpiar_pantalla()

            ver_detalle_por_region_situacion_1()


        elif opcion_detalle == "2":

            limpiar_pantalla()

            ver_detalle_por_cultivo_situacion_1()


        elif opcion_detalle == "3":

            limpiar_pantalla()

            ver_detalle_por_campania_situacion_1()


        elif opcion_detalle == "4":

            limpiar_pantalla()

            ver_detalle_situacion_1()


        elif opcion_detalle == "5":

            limpiar_pantalla()

            return


        else:

            print(
                "\nOpción inválida. "
                "Ingrese una opción entre 1 y 5."
            )


# ============================================================
# DETALLE DE SITUACIÓN DESFAVORABLE 1
# Puede filtrar por región, cultivo o campaña
# ============================================================

def ver_detalle_situacion_1(
    region_seleccionada=None,
    cultivo_seleccionado=None,
    campania_seleccionada=None
):

    cursor.execute("""
        SELECT
            r.region_nombre,
            c.cultivo_nombre,
            ca.campania,
            s1.superficie_sembrada_ha,
            s1.superficie_cosechada_ha,
            s1.superficie_no_cosechada_ha,
            s1.porcentaje_no_cosechado

        FROM situacion_desfavorable_1 s1

        JOIN analisis_regional ar
            ON s1.analisis_id = ar.analisis_id

        JOIN region r
            ON ar.region_id = r.region_id

        JOIN cultivo c
            ON ar.cultivo_id = c.cultivo_id

        JOIN campania ca
            ON ar.campania_id = ca.campania_id

        WHERE s1.es_desfavorable = 'SI'

            AND (
                %s IS NULL
                OR r.region_nombre = %s
            )

            AND (
                %s IS NULL
                OR c.cultivo_nombre = %s
            )

            AND (
                %s IS NULL
                OR ca.campania = %s
            )

        ORDER BY
            r.region_nombre,
            c.cultivo_nombre,
            ca.anio_inicio

    """, (
        region_seleccionada,
        region_seleccionada,
        cultivo_seleccionado,
        cultivo_seleccionado,
        campania_seleccionada,
        campania_seleccionada
    ))

    resultados = cursor.fetchall()


    # --------------------------------------------------------
    # Encabezado
    # --------------------------------------------------------

    print("\n" + "=" * 110)

    print(
        "SITUACIÓN DESFAVORABLE 1 - SUPERFICIE NO COSECHADA".center(110)
    )

    print("=" * 110)

    print(
        f"{'REGIÓN':<18}"
        f"{'CULTIVO':<20}"
        f"{'CAMPAÑA':<14}"
        f"{'SEMBRADA':>14}"
        f"{'COSECHADA':>14}"
        f"{'NO COSECH.':>14}"
        f"{'% NO COSECH.':>14}"
    )

    print("-" * 110)


    # --------------------------------------------------------
    # Acumuladores
    # --------------------------------------------------------

    region_actual = None
    cultivo_actual = None

    total_sembrada = 0
    total_cosechada = 0
    total_no_cosechada = 0


    # --------------------------------------------------------
    # Función para subtotal
    # --------------------------------------------------------

    def imprimir_subtotal(
        region,
        cultivo,
        sembrada,
        cosechada,
        no_cosechada
    ):

        if sembrada > 0:

            porcentaje_subtotal = int(
                round(
                    (no_cosechada / sembrada)
                    * 100
                )
            )

        else:

            porcentaje_subtotal = 0


        etiqueta = (
            f"SUBTOTAL CASOS DESFAVORABLES - "
            f"{region} / {cultivo}"
        )

        print("-" * 110)

        print(
            f"{etiqueta:<52}"
            f"{format(sembrada, ',').replace(',', '.'):>14}"
            f"{format(cosechada, ',').replace(',', '.'):>14}"
            f"{format(no_cosechada, ',').replace(',', '.'):>14}"
            f"{porcentaje_subtotal:>12} %"
        )

        print("-" * 110)


    # --------------------------------------------------------
    # Impresión del detalle
    # --------------------------------------------------------

    for fila in resultados:

        region = fila[0]
        cultivo = fila[1]

        sembrada = int(
            round(float(fila[3]))
        )

        cosechada = int(
            round(float(fila[4]))
        )

        no_cosechada = int(
            round(float(fila[5]))
        )

        porcentaje = int(
            round(float(fila[6]))
        )


        # Si cambia región o cultivo,
        # imprime subtotal del grupo anterior.

        if (
            campania_seleccionada is None
            and region_actual is not None
            and (
                region != region_actual
                or cultivo != cultivo_actual
            )
        ):

            imprimir_subtotal(
                region_actual,
                cultivo_actual,
                total_sembrada,
                total_cosechada,
                total_no_cosechada
            )

            total_sembrada = 0
            total_cosechada = 0
            total_no_cosechada = 0


        region_actual = region
        cultivo_actual = cultivo


        # Detalle por campaña

        print(
            f"{region:<18}"
            f"{cultivo:<20}"
            f"{fila[2]:<14}"
            f"{format(sembrada, ',').replace(',', '.'):>14}"
            f"{format(cosechada, ',').replace(',', '.'):>14}"
            f"{format(no_cosechada, ',').replace(',', '.'):>14}"
            f"{porcentaje:>12} %"
        )


        total_sembrada += sembrada
        total_cosechada += cosechada
        total_no_cosechada += no_cosechada


    # --------------------------------------------------------
    # Último subtotal
    # --------------------------------------------------------

    if (
        campania_seleccionada is None
        and region_actual is not None
    ):

        imprimir_subtotal(
            region_actual,
            cultivo_actual,
            total_sembrada,
            total_cosechada,
            total_no_cosechada
        )


    print("-" * 110)

    print(
        "Casos desfavorables encontrados:",
        len(resultados)
    )

    input(
        "\nPresione ENTER para volver "
        "al menú de consulta detallada..."
    )

    limpiar_pantalla()



# ============================================================
# OPCIÓN 5 - FOCOS CRÍTICOS
# Consulta de la VIEW vw_foco_critico
# ============================================================

def menu_focos_criticos():

    limpiar_pantalla()

    cursor.execute("""
        SELECT
            region,
            cultivo,
            campania,
            porcentaje_no_cosechado,
            rendimiento_regional_kgxha,
            rendimiento_nacional_kgxha,
            variacion_produccion_pct,
            caidas_consecutivas

        FROM vw_foco_critico

        ORDER BY
            region,
            cultivo,
            campania
    """)

    resultados = cursor.fetchall()

    print("\n" + "=" * 120)
    print("FOCOS CRÍTICOS".center(120))
    print("=" * 120)

    if len(resultados) == 0:

        print(
            "\nNo se detectaron casos en los que coincidan "
            "las tres situaciones desfavorables."
        )

    else:

        print(
            f"{'REGIÓN':<18}"
            f"{'CULTIVO':<20}"
            f"{'CAMPAÑA':<14}"
            f"{'% NO COSECH.':>14}"
            f"{'REND. REG.':>14}"
            f"{'REND. NAC.':>14}"
            f"{'VAR. PROD.':>14}"
            f"{'CAÍDAS':>10}"
        )

        print("-" * 120)

        for fila in resultados:

            porcentaje_no_cosechado = int(
                round(float(fila[3]))
            )

            rendimiento_regional = int(
                round(float(fila[4]))
            )

            rendimiento_nacional = int(
                round(float(fila[5]))
            )

            variacion_produccion = round(
                float(fila[6]),
                1
            )

            caidas = fila[7]

            print(
                f"{fila[0]:<18}"
                f"{fila[1]:<20}"
                f"{fila[2]:<14}"
                f"{porcentaje_no_cosechado:>12} %"
                f"{format(rendimiento_regional, ',').replace(',', '.'):>14}"
                f"{format(rendimiento_nacional, ',').replace(',', '.'):>14}"
                f"{variacion_produccion:>12.1f} %"
                f"{caidas:>10}"
            )

        print("-" * 120)

        print(
            "Focos críticos encontrados:",
            len(resultados)
        )

    input(
        "\nPresione ENTER para volver al menú principal..."
    )

    limpiar_pantalla()


# ============================================================
# OPCIÓN 6 - BÚSQUEDA POR REGIÓN
# ============================================================

def menu_busqueda_por_region():

    limpiar_pantalla()

    cursor.execute("""
        SELECT region_nombre
        FROM region
        ORDER BY region_nombre
    """)

    regiones = cursor.fetchall()

    print("\nBÚSQUEDA POR REGIÓN\n")

    for numero, region in enumerate(regiones, start=1):
        print(
            f"{numero}. {region[0]}"
        )

    print()

    opcion_region = input(
        "Seleccione una región o presione ENTER para volver: "
    )

    if opcion_region == "":
        return

    if not opcion_region.isdigit():
        print("\nOpción inválida.")
        input("\nPresione ENTER para volver...")
        return

    numero_region = int(opcion_region)

    if numero_region < 1 or numero_region > len(regiones):
        print("\nOpción inválida.")
        input("\nPresione ENTER para volver...")
        return

    region_seleccionada = regiones[numero_region - 1][0]

    resultados = buscar_por_region(
        region_seleccionada
    )

    limpiar_pantalla()

    print("\n" + "=" * 85)
    print(
        f"RESULTADOS DESFAVORABLES - {region_seleccionada}".center(85)
    )
    print("=" * 85)

    print(
        f"{'REGIÓN':<18}"
        f"{'CULTIVO':<20}"
        f"{'CAMPAÑA':<15}"
        f"{'S1':>8}"
        f"{'S2':>8}"
        f"{'S3':>8}"
    )

    print("-" * 85)

    for fila in resultados:

        print(
            f"{fila[0]:<18}"
            f"{fila[1]:<20}"
            f"{fila[2]:<15}"
            f"{str(fila[3]):>8}"
            f"{str(fila[4]):>8}"
            f"{str(fila[5]):>8}"
        )

    print("-" * 85)

    print(
        "Casos encontrados:",
        len(resultados)
    )

    input(
        "\nPresione ENTER para volver al menú principal..."
    )

    limpiar_pantalla()


# ============================================================
# OPCIÓN 7 - BÚSQUEDA POR CULTIVO Y CAMPAÑA
# ============================================================

def menu_busqueda_por_cultivo_campania():

    limpiar_pantalla()

    cursor.execute("""
        SELECT cultivo_nombre
        FROM cultivo
        ORDER BY cultivo_nombre
    """)

    cultivos = cursor.fetchall()

    print("\nBÚSQUEDA POR CULTIVO Y CAMPAÑA\n")

    print("CULTIVOS\n")

    for numero, cultivo in enumerate(cultivos, start=1):
        print(
            f"{numero}. {cultivo[0]}"
        )

    print()

    opcion_cultivo = input(
        "Seleccione un cultivo o presione ENTER para volver: "
    )

    if opcion_cultivo == "":
        return

    if not opcion_cultivo.isdigit():
        print("\nOpción inválida.")
        input("\nPresione ENTER para volver...")
        return

    numero_cultivo = int(opcion_cultivo)

    if numero_cultivo < 1 or numero_cultivo > len(cultivos):
        print("\nOpción inválida.")
        input("\nPresione ENTER para volver...")
        return

    cultivo_seleccionado = cultivos[numero_cultivo - 1][0]


    # --------------------------------------------------------
    # Selección de campaña
    # --------------------------------------------------------

    limpiar_pantalla()

    cursor.execute("""
        SELECT campania
        FROM campania
        ORDER BY anio_inicio
    """)

    campanias = cursor.fetchall()

    print(
        f"\nCULTIVO SELECCIONADO: {cultivo_seleccionado}\n"
    )

    print("CAMPAÑAS\n")

    for numero, campania in enumerate(campanias, start=1):
        print(
            f"{numero}. {campania[0]}"
        )

    print()

    opcion_campania = input(
        "Seleccione una campaña o presione ENTER para volver: "
    )

    if opcion_campania == "":
        return

    if not opcion_campania.isdigit():
        print("\nOpción inválida.")
        input("\nPresione ENTER para volver...")
        return

    numero_campania = int(opcion_campania)

    if numero_campania < 1 or numero_campania > len(campanias):
        print("\nOpción inválida.")
        input("\nPresione ENTER para volver...")
        return

    campania_seleccionada = campanias[numero_campania - 1][0]


    # --------------------------------------------------------
    # Consulta
    # --------------------------------------------------------

    resultados = buscar_por_cultivo_campania(
        cultivo_seleccionado,
        campania_seleccionada
    )

    limpiar_pantalla()

    print("\n" + "=" * 85)

    print(
        (
            f"{cultivo_seleccionado} - "
            f"CAMPAÑA {campania_seleccionada}"
        ).center(85)
    )

    print("=" * 85)

    print(
        f"{'CULTIVO':<20}"
        f"{'CAMPAÑA':<15}"
        f"{'REGIÓN':<20}"
        f"{'S1':>8}"
        f"{'S2':>8}"
        f"{'S3':>8}"
    )

    print("-" * 85)

    for fila in resultados:

        print(
            f"{fila[0]:<20}"
            f"{fila[1]:<15}"
            f"{fila[2]:<20}"
            f"{str(fila[3]):>8}"
            f"{str(fila[4]):>8}"
            f"{str(fila[5]):>8}"
        )

    print("-" * 85)

    print(
        "Regiones encontradas:",
        len(resultados)
    )

    input(
        "\nPresione ENTER para volver al menú principal..."
    )

    limpiar_pantalla()


# ============================================================
# OPCIÓN 8 - GESTIÓN DE PARÁMETROS
# CRUD
# ============================================================

def menu_gestion_parametros():

    while True:

        limpiar_pantalla()

        print("\n" + "=" * 80)
        print("GESTIÓN DE PARÁMETROS".center(80))
        print("=" * 80)

        print("\n1. Ver parámetros")
        print("2. Modificar parámetro")
        print("3. Volver al menú principal")

        opcion_parametro = input(
            "\nSeleccione una opción: "
        )


        # ----------------------------------------------------
        # READ
        # ----------------------------------------------------

        if opcion_parametro == "1":

            limpiar_pantalla()

            parametros = ParametroAnalisis.listar()

            print("\nPARÁMETROS DE ANÁLISIS\n")

            print(
                f"{'N°':<5}"
                f"{'NOMBRE':<30}"
                f"{'VALOR':>12}"
                f"{'OBLIGATORIO':>15}"
            )

            print("-" * 65)

            for numero, parametro in enumerate(
                parametros,
                start=1
            ):

                print(
                    f"{numero:<5}"
                    f"{parametro.nombre:<30}"
                    f"{str(parametro.valor):>12}"
                    f"{parametro.es_obligatorio:>15}"
                )

            input(
                "\nPresione ENTER para volver..."
            )


        # ----------------------------------------------------
        # UPDATE
        # ----------------------------------------------------

        elif opcion_parametro == "2":

            limpiar_pantalla()

            parametros = ParametroAnalisis.listar()

            print("\nMODIFICAR PARÁMETRO\n")

            for numero, parametro in enumerate(
                parametros,
                start=1
            ):

                print(
                    f"{numero}. "
                    f"{parametro.nombre:<30}"
                    f"Valor actual: {parametro.valor}"
                )

            print()

            opcion = input(
                "Seleccione un parámetro o presione ENTER para volver: "
            )

            if opcion == "":
                continue

            if not opcion.isdigit():
                input(
                    "\nOpción inválida. Presione ENTER..."
                )
                continue

            numero = int(opcion)

            if numero < 1 or numero > len(parametros):
                input(
                    "\nOpción inválida. Presione ENTER..."
                )
                continue

            parametro = parametros[numero - 1]

            nuevo_valor = input(
                f"\nNuevo valor para {parametro.nombre}: "
            )

            try:

                nuevo_valor = float(nuevo_valor)

                parametro.modificar(
                    nuevo_valor
                )

                print(
                    "\nParámetro modificado correctamente."
                )

                print(
                    "El nuevo valor se aplicará "
                    "al volver a ejecutar los análisis."
                )

            except ValueError:

                print(
                    "\nEl valor ingresado debe ser numérico."
                )

            input(
                "\nPresione ENTER para continuar..."
            )


        # ----------------------------------------------------
        # VOLVER
        # ----------------------------------------------------

        elif opcion_parametro == "3":

            limpiar_pantalla()

            return


        else:

            input(
                "\nOpción inválida. Presione ENTER..."
            )


# ============================================================
# ÚLTIMO AÑO DE CAMPAÑA CARGADO
# ============================================================

def obtener_ultimo_anio_cargado():

    cursor.execute("""
        SELECT MAX(ca.anio_inicio)
        FROM estimacion e
        JOIN campania ca
            ON e.campania_id = ca.campania_id
    """)

    resultado = cursor.fetchone()

    return resultado[0]


# ============================================================
# DETECCIÓN DE REGISTROS DE CAMPAÑAS NUEVAS
# ============================================================

def contar_registros_nuevos():

    ultimo_anio = obtener_ultimo_anio_cargado()

    cursor.execute("""
        SELECT
            COUNT(*) AS cantidad,
            MIN(CAST(SUBSTRING_INDEX(TRIM(campania), '/', 1) AS UNSIGNED)),
            MAX(CAST(SUBSTRING_INDEX(TRIM(campania), '/', 1) AS UNSIGNED))
        FROM estimaciones_csv
        WHERE CAST(
            SUBSTRING_INDEX(TRIM(campania), '/', 1)
            AS UNSIGNED
        ) > %s
    """, (ultimo_anio,))

    resultado = cursor.fetchone()

    return ultimo_anio, resultado













# ============================================================
# GESTIÓN DE ESTIMACIONES
# ============================================================

# ============================================================
# SELECCIÓN DE ARCHIVO CSV
# ============================================================

def seleccionar_archivo_csv():

    ventana = Tk()
    ventana.withdraw()
    ventana.attributes("-topmost", True)

    ruta_csv = filedialog.askopenfilename(
        title="Seleccionar nuevo archivo de estimaciones",
        filetypes=[("Archivos CSV", "*.csv")]
    )

    ventana.destroy()

    return ruta_csv

# ============================================================
# CARGA DEL NUEVO CSV EN TABLA CRUDA
# ============================================================

def cargar_csv_actualizacion(ruta_csv):

    try:

        # Vacía la tabla dentro de la misma transacción
        cursor.execute("DELETE FROM estimaciones_csv")

        # Carga el nuevo archivo seleccionado
        cursor.execute("""
            LOAD DATA LOCAL INFILE %s
            INTO TABLE estimaciones_csv
            CHARACTER SET utf8mb4
            FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
            LINES TERMINATED BY '\r\n'
            IGNORE 1 LINES
            (
                cultivo,
                anio,
                campania,
                provincia,
                provincia_id,
                departamento,
                departamento_id,
                superficie_sembrada_ha,
                superficie_cosechada_ha,
                produccion_tm,
                rendimiento_kgxha
            )
        """, (ruta_csv,))

        # Confirma los cambios solo si todo salió bien
        conexion.commit()

        cursor.execute("SELECT COUNT(*) FROM estimaciones_csv")
        cantidad = cursor.fetchone()[0]

        return cantidad

    except Exception:

        # Si falla la carga, restaura el contenido anterior
        conexion.rollback()

        raise


# ============================================================
# PREPARACIÓN DE STAGING PARA CAMPAÑAS NUEVAS
# ============================================================

def preparar_stg_estimaciones_nuevas(ultimo_anio):

    # Vacía staging solamente cuando existen registros nuevos
    cursor.execute("DELETE FROM stg_estimaciones")

    # Carga únicamente campañas posteriores al último año cargado
    cursor.execute("""
        INSERT INTO stg_estimaciones (
            cultivo,
            campania,
            anio_inicio,
            provincia,
            provincia_id,
            departamento,
            departamento_id,
            region,
            superficie_sembrada_ha,
            superficie_cosechada_ha,
            produccion_tm,
            rendimiento_kgxha
        )
        SELECT
            COALESCE(
                CONVERT(
                    CAST(CONVERT(TRIM(cultivo) USING latin1) AS BINARY)
                    USING utf8mb4
                ),
                TRIM(cultivo)
            ),

            TRIM(campania),

            CAST(
                SUBSTRING_INDEX(campania, '/', 1)
                AS UNSIGNED
            ),

            COALESCE(
                CONVERT(
                    CAST(CONVERT(TRIM(provincia) USING latin1) AS BINARY)
                    USING utf8mb4
                ),
                TRIM(provincia)
            ),

            NULLIF(provincia_id, '') + 0,

            COALESCE(
                CONVERT(
                    CAST(
                        CONVERT(TRIM(departamento) USING latin1)
                        AS BINARY
                    )
                    USING utf8mb4
                ),
                TRIM(departamento)
            ),

            NULLIF(departamento_id, '') + 0,

            CASE NULLIF(provincia_id, '') + 0
                WHEN 10 THEN 'NOA'
                WHEN 38 THEN 'NOA'
                WHEN 66 THEN 'NOA'
                WHEN 86 THEN 'NOA'
                WHEN 90 THEN 'NOA'
                WHEN 22 THEN 'NEA'
                WHEN 18 THEN 'NEA'
                WHEN 30 THEN 'NEA'
                WHEN 34 THEN 'NEA'
                WHEN 54 THEN 'NEA'
                WHEN 82 THEN 'NEA'
                WHEN 6  THEN 'Centro'
                WHEN 14 THEN 'Centro'
                WHEN 50 THEN 'Cuyo'
                WHEN 70 THEN 'Cuyo'
                WHEN 46 THEN 'Cuyo'
                WHEN 74 THEN 'Cuyo'
                WHEN 42 THEN 'Patagonia Norte'
                WHEN 58 THEN 'Patagonia Norte'
                WHEN 62 THEN 'Patagonia Norte'
                WHEN 26 THEN 'Patagonia Sur'
                WHEN 78 THEN 'Patagonia Sur'
                WHEN 94 THEN 'Patagonia Sur'
                ELSE NULL
            END,

            NULLIF(superficie_sembrada_ha, '') + 0,
            NULLIF(superficie_cosechada_ha, '') + 0,
            NULLIF(produccion_tm, '') + 0,
            NULLIF(rendimiento_kgxha, '') + 0

        FROM estimaciones_csv

        WHERE CAST(
            SUBSTRING_INDEX(TRIM(campania), '/', 1)
            AS UNSIGNED
        ) > %s
    """, (ultimo_anio,))

    # Mismas reglas básicas de limpieza
    cursor.execute("""
        DELETE FROM stg_estimaciones
        WHERE provincia_id IS NULL
           OR cultivo IS NULL
           OR cultivo = ''
           OR campania IS NULL
           OR campania = ''
    """)

    cursor.execute("""
        UPDATE stg_estimaciones
        SET rendimiento_kgxha = NULL
        WHERE rendimiento_kgxha < 0
    """)

    conexion.commit()



# ============================================================
# VIEW - INCONSISTENCIAS PENDIENTES DE ACTUALIZACIÓN
# ============================================================

def crear_view_inconsistencias_actualizacion():

        cursor.execute("""
        CREATE OR REPLACE VIEW vw_inconsistencias_actualizacion AS

        WITH cultivos_totales AS (

            SELECT DISTINCT
                TRIM(cultivo) AS cultivo_total,
                TRIM(
                    LEFT(
                        TRIM(cultivo),
                        CHAR_LENGTH(TRIM(cultivo))
                        - CHAR_LENGTH(' total')
                    )
                ) AS cultivo_base

            FROM stg_estimaciones

            WHERE LOWER(TRIM(cultivo)) LIKE '% total'
        ),

        comparacion_departamental AS (

            SELECT
                ct.cultivo_base,
                ct.cultivo_total,
                s.campania,
                s.provincia,
                s.provincia_id,
                s.departamento,
                s.departamento_id,

                SUM(
                    CASE
                        WHEN LOWER(TRIM(s.cultivo)) = LOWER(ct.cultivo_total)
                        THEN 1
                        ELSE 0
                    END
                ) AS registros_total,

                SUM(
                    CASE
                        WHEN LOWER(TRIM(s.cultivo)) <> LOWER(ct.cultivo_total)
                        THEN 1
                        ELSE 0
                    END
                ) AS registros_componentes,

                SUM(
                    CASE
                        WHEN LOWER(TRIM(s.cultivo)) = LOWER(ct.cultivo_total)
                        THEN s.superficie_sembrada_ha
                        ELSE 0
                    END
                ) AS sembrada_total,

                SUM(
                    CASE
                        WHEN LOWER(TRIM(s.cultivo)) <> LOWER(ct.cultivo_total)
                        THEN s.superficie_sembrada_ha
                        ELSE 0
                    END
                ) AS sembrada_componentes,

                SUM(
                    CASE
                        WHEN LOWER(TRIM(s.cultivo)) = LOWER(ct.cultivo_total)
                        THEN s.superficie_cosechada_ha
                        ELSE 0
                    END
                ) AS cosechada_total,

                SUM(
                    CASE
                        WHEN LOWER(TRIM(s.cultivo)) <> LOWER(ct.cultivo_total)
                        THEN s.superficie_cosechada_ha
                        ELSE 0
                    END
                ) AS cosechada_componentes,

                SUM(
                    CASE
                        WHEN LOWER(TRIM(s.cultivo)) = LOWER(ct.cultivo_total)
                        THEN s.produccion_tm
                        ELSE 0
                    END
                ) AS produccion_total,

                SUM(
                    CASE
                        WHEN LOWER(TRIM(s.cultivo)) <> LOWER(ct.cultivo_total)
                        THEN s.produccion_tm
                        ELSE 0
                    END
                ) AS produccion_componentes

            FROM cultivos_totales ct

            JOIN stg_estimaciones s
                ON LOWER(TRIM(s.cultivo)) = LOWER(ct.cultivo_total)
                OR LOWER(TRIM(s.cultivo))
                   LIKE CONCAT(LOWER(ct.cultivo_base), ' %')

            GROUP BY
                ct.cultivo_base,
                ct.cultivo_total,
                s.campania,
                s.provincia,
                s.provincia_id,
                s.departamento,
                s.departamento_id
        ),

        diferencias_departamentales AS (

            SELECT
                *,
                sembrada_total - sembrada_componentes
                    AS diferencia_sembrada,
                cosechada_total - cosechada_componentes
                    AS diferencia_cosechada,
                produccion_total - produccion_componentes
                    AS diferencia_produccion

            FROM comparacion_departamental
        ),

        revision_departamental AS (

            SELECT *

            FROM diferencias_departamentales

            WHERE registros_total > 0
              AND registros_componentes > 0

              AND (
                     ABS(diferencia_sembrada)
                     > GREATEST(1, ABS(sembrada_total) * 0.001)

                  OR ABS(diferencia_cosechada)
                     > GREATEST(1, ABS(cosechada_total) * 0.001)

                  OR ABS(diferencia_produccion)
                     > GREATEST(1, ABS(produccion_total) * 0.001)
              )

              AND NOT (
                     sembrada_total >= sembrada_componentes
                 AND cosechada_total >= cosechada_componentes
                 AND produccion_total >= produccion_componentes
              )
        ),

        resumen_provincial AS (

            SELECT
                cultivo_base,
                campania,
                provincia,
                provincia_id,

                SUM(sembrada_total)
                    AS sembrada_total_provincia,

                SUM(sembrada_componentes)
                    AS sembrada_componentes_provincia,

                SUM(cosechada_total)
                    AS cosechada_total_provincia,

                SUM(cosechada_componentes)
                    AS cosechada_componentes_provincia,

                SUM(produccion_total)
                    AS produccion_total_provincia,

                SUM(produccion_componentes)
                    AS produccion_componentes_provincia

            FROM diferencias_departamentales

            GROUP BY
                cultivo_base,
                campania,
                provincia,
                provincia_id
        )

        SELECT
            rd.cultivo_base,
            rd.campania,
            rd.provincia,
            rd.provincia_id,

            COUNT(*) AS departamentos_en_revision,

            ROUND(
                rp.sembrada_total_provincia
                - rp.sembrada_componentes_provincia,
                2
            ) AS diferencia_provincial_sembrada,

            ROUND(
                rp.cosechada_total_provincia
                - rp.cosechada_componentes_provincia,
                2
            ) AS diferencia_provincial_cosechada,

            ROUND(
                rp.produccion_total_provincia
                - rp.produccion_componentes_provincia,
                2
            ) AS diferencia_provincial_produccion

        FROM revision_departamental rd

        JOIN resumen_provincial rp
            ON rp.cultivo_base = rd.cultivo_base
           AND rp.campania = rd.campania
           AND rp.provincia_id = rd.provincia_id

        WHERE NOT (

            ABS(
                rp.sembrada_total_provincia
                - rp.sembrada_componentes_provincia
            )
            <= GREATEST(
                1,
                ABS(rp.sembrada_total_provincia) * 0.001
            )

            AND ABS(
                rp.cosechada_total_provincia
                - rp.cosechada_componentes_provincia
            )
            <= GREATEST(
                1,
                ABS(rp.cosechada_total_provincia) * 0.001
            )

            AND ABS(
                rp.produccion_total_provincia
                - rp.produccion_componentes_provincia
            )
            <= GREATEST(
                1,
                ABS(rp.produccion_total_provincia) * 0.001
            )
        )

        AND NOT (
               rp.sembrada_total_provincia
                    >= rp.sembrada_componentes_provincia
           AND rp.cosechada_total_provincia
                    >= rp.cosechada_componentes_provincia
           AND rp.produccion_total_provincia
                    >= rp.produccion_componentes_provincia
        )

        GROUP BY
            rd.cultivo_base,
            rd.campania,
            rd.provincia,
            rd.provincia_id,
            rp.sembrada_total_provincia,
            rp.sembrada_componentes_provincia,
            rp.cosechada_total_provincia,
            rp.cosechada_componentes_provincia,
            rp.produccion_total_provincia,
            rp.produccion_componentes_provincia
    """)

conexion.commit()


# ============================================================
# CONTROL DE INCONSISTENCIAS PENDIENTES
# ============================================================

def contar_inconsistencias_actualizacion():

    cursor.execute("""
        SELECT COUNT(*)
        FROM vw_inconsistencias_actualizacion
    """)

    cantidad = cursor.fetchone()[0]

    return cantidad


# ============================================================
# DEPURACIÓN DE REGISTROS NUEVOS
# ============================================================

def preparar_stg_estimaciones_depuradas():

    # Vacía la tabla depurada anterior
    cursor.execute("""
        DELETE FROM stg_estimaciones_depuradas
    """)

    # Aplica el mismo tratamiento de cultivos agregados
    # y componentes definido en el proceso original
    cursor.execute("""
        INSERT INTO stg_estimaciones_depuradas (
            cultivo,
            campania,
            anio_inicio,
            provincia,
            provincia_id,
            departamento,
            departamento_id,
            region,
            superficie_sembrada_ha,
            superficie_cosechada_ha,
            produccion_tm,
            rendimiento_kgxha
        )

        WITH cultivos_totales AS (

            SELECT DISTINCT
                TRIM(cultivo) AS cultivo_total,

                TRIM(
                    LEFT(
                        TRIM(cultivo),
                        CHAR_LENGTH(TRIM(cultivo))
                        - CHAR_LENGTH(' total')
                    )
                ) AS cultivo_base

            FROM stg_estimaciones

            WHERE LOWER(TRIM(cultivo)) LIKE '% total'
        ),

        totales_disponibles AS (

            SELECT DISTINCT
                ct.cultivo_base,
                ct.cultivo_total,
                s.campania,
                s.provincia_id

            FROM cultivos_totales ct

            JOIN stg_estimaciones s
                ON LOWER(TRIM(s.cultivo))
                   = LOWER(ct.cultivo_total)
        ),

        filas_clasificadas AS (

            SELECT
                s.*,
                ct.cultivo_base,
                ct.cultivo_total

            FROM stg_estimaciones s

            LEFT JOIN cultivos_totales ct
                ON LOWER(TRIM(s.cultivo))
                   = LOWER(ct.cultivo_total)

                OR LOWER(TRIM(s.cultivo))
                   = LOWER(ct.cultivo_base)

                OR LOWER(TRIM(s.cultivo))
                   LIKE CONCAT(
                       LOWER(ct.cultivo_base),
                       ' %'
                   )
        )

        SELECT
            COALESCE(
                f.cultivo_base,
                f.cultivo
            ) AS cultivo,

            f.campania,
            f.anio_inicio,
            f.provincia,
            f.provincia_id,
            f.departamento,
            f.departamento_id,
            f.region,
            f.superficie_sembrada_ha,
            f.superficie_cosechada_ha,
            f.produccion_tm,
            f.rendimiento_kgxha

        FROM filas_clasificadas f

        LEFT JOIN totales_disponibles td
            ON LOWER(td.cultivo_base)
               = LOWER(f.cultivo_base)

           AND td.campania = f.campania
           AND td.provincia_id = f.provincia_id

        WHERE
              f.cultivo_base IS NULL

           OR LOWER(TRIM(f.cultivo))
              = LOWER(f.cultivo_total)

           OR td.cultivo_total IS NULL
    """)

    conexion.commit()


# ============================================================
# CONTROL DE PROVINCIAS DESCONOCIDAS
# ============================================================

def buscar_provincias_desconocidas():

    cursor.execute("""
        SELECT
            s.provincia_id,
            MAX(s.provincia) AS provincia

        FROM stg_estimaciones_depuradas s

        LEFT JOIN provincia p
            ON p.provincia_id = s.provincia_id

        WHERE p.provincia_id IS NULL

        GROUP BY
            s.provincia_id

        ORDER BY
            provincia
    """)

    return cursor.fetchall()


# ============================================================
# ACTUALIZACIÓN DE CULTIVOS Y CAMPAÑAS
# ============================================================

def actualizar_dimensiones_nuevas():

    # Incorpora únicamente cultivos que todavía no existen
    cursor.execute("""
        INSERT IGNORE INTO cultivo (cultivo_nombre)
        SELECT DISTINCT cultivo
        FROM stg_estimaciones_depuradas
        WHERE cultivo IS NOT NULL
          AND cultivo <> ''
    """)

    # Incorpora únicamente campañas que todavía no existen
    cursor.execute("""
        INSERT IGNORE INTO campania (campania, anio_inicio)
        SELECT
            campania,
            MAX(anio_inicio)
        FROM stg_estimaciones_depuradas
        WHERE campania IS NOT NULL
          AND campania <> ''
        GROUP BY campania
    """)

# ============================================================
# CARGA DE NUEVAS ESTIMACIONES
# ============================================================

def insertar_estimaciones_nuevas():

    cursor.execute("""
        INSERT INTO estimacion (
            cultivo_id,
            campania_id,
            provincia_id,
            region_id,
            superficie_sembrada_ha,
            superficie_cosechada_ha,
            produccion_tm,
            rendimiento_kgxha
        )

        SELECT
            c.cultivo_id,
            ca.campania_id,
            s.provincia_id,
            r.region_id,

            SUM(s.superficie_sembrada_ha),
            SUM(s.superficie_cosechada_ha),
            SUM(s.produccion_tm),

            CASE
                WHEN SUM(s.superficie_cosechada_ha) > 0
                THEN ROUND(
                    SUM(s.produccion_tm) * 1000
                    / SUM(s.superficie_cosechada_ha),
                    2
                )
                ELSE NULL
            END

        FROM stg_estimaciones_depuradas s

        JOIN cultivo c
            ON c.cultivo_nombre = s.cultivo

        JOIN campania ca
            ON ca.campania = s.campania

        JOIN region r
            ON r.region_nombre = s.region

        GROUP BY
            c.cultivo_id,
            ca.campania_id,
            s.provincia_id,
            r.region_id
    """)
































# ============================================================
# MENÚ DE GESTIÓN DE ESTIMACIONES
# Permite acceder a las opciones relacionadas con la
# actualización y mantenimiento de la base de estimaciones.
# ============================================================

def menu_gestion_estimaciones():

    os.system("cls" if os.name == "nt" else "clear")

    while True:

        print("\n" + "=" * ANCHO)
        print("GESTIÓN DE ESTIMACIONES".center(ANCHO))
        print("=" * ANCHO)

        print("\n1. Actualizar base desde nuevo archivo CSV")
        print("2. Volver al menú principal")

        opcion = input("\nIngrese una opción: ")

        if opcion == "1":

            ruta_csv = seleccionar_archivo_csv()

            if ruta_csv:

                print("\nArchivo seleccionado:")
                print(ruta_csv)

                confirmacion = input(
                    "\nATENCIÓN: se vaciará la tabla estimaciones_csv "
                    "para cargar el nuevo archivo.\n"
                    "¿Desea continuar? (S/N): "
                ).strip().upper()

                if confirmacion == "S":

                    cantidad = cargar_csv_actualizacion(ruta_csv)

                    print("\nArchivo cargado correctamente.")
                    print(f"Registros cargados en estimaciones_csv: {cantidad}")

                    ultimo_anio, resultado = contar_registros_nuevos()

                    cantidad_nuevos = resultado[0]
                    anio_min_nuevo = resultado[1]
                    anio_max_nuevo = resultado[2]

                    print(f"\nÚltimo año actualmente cargado en estimacion: {ultimo_anio}")
                    print(f"Registros correspondientes a años posteriores: {cantidad_nuevos}")

                    if cantidad_nuevos > 0:
                        print(f"Rango de años nuevos detectado: {anio_min_nuevo} - {anio_max_nuevo}")

                        preparar_stg_estimaciones_nuevas(ultimo_anio)

                        print("\nRegistros nuevos preparados en stg_estimaciones.")
                            # Crea/actualiza la VIEW con las inconsistencias pendientes
                        crear_view_inconsistencias_actualizacion()

                        # Consulta cuántos casos requieren revisión
                        cantidad_inconsistencias = contar_inconsistencias_actualizacion()

                        if cantidad_inconsistencias > 0:

                            print(
                                f"\nATENCIÓN: se detectaron "
                                f"{cantidad_inconsistencias} inconsistencias que requieren revisión."
                            )

                            print(
                                "La actualización fue detenida. "
                                "No se modificaron las tablas finales."
                            )

                            input("\nPresione ENTER para continuar...")

                            continue

                        else:

                            print(
                                "\nControl de inconsistencias superado. "
                                "No quedan casos pendientes de revisión."
                            )
                            confirmar_actualizacion = input(
                                "\nEl control fue superado. "
                                "¿Desea continuar con la actualización de la base? (S/N): "
                            ).strip().upper()

                            if confirmar_actualizacion != "S":

                                print(
                                    "\nActualización cancelada. "
                                    "No se modificaron las tablas finales."
                                )

                                input("\nPresione ENTER para continuar...")

                                continue
                            preparar_stg_estimaciones_depuradas()

                            print(
                                "\nRegistros nuevos depurados correctamente "
                                "en stg_estimaciones_depuradas."
                            )

                            provincias_desconocidas = buscar_provincias_desconocidas()

                            if provincias_desconocidas:

                                print(
                                    "\nATENCIÓN: se detectaron provincias no reconocidas "
                                    "en los registros nuevos."
                                )

                                for provincia_id, provincia in provincias_desconocidas:
                                    print(f"- ID {provincia_id}: {provincia}")

                                print(
                                    "\nLa actualización fue detenida. "
                                    "No se modificaron las tablas finales."
                                )

                                input("\nPresione ENTER para continuar...")

                                continue
                            # --------------------------------------------------------
                            # INCORPORACIÓN DEFINITIVA DE LOS REGISTROS NUEVOS
                            # --------------------------------------------------------

                            try:

                                # Agrega cultivos y campañas que todavía no existan
                                actualizar_dimensiones_nuevas()

                                # Incorpora las nuevas estimaciones
                                insertar_estimaciones_nuevas()

                                # Confirma todo junto
                                conexion.commit()

                                print(
                                    "\nActualización realizada correctamente."
                                )

                            except mysql.connector.Error as error:

                                # Si falla alguna parte, revierte cultivos,
                                # campañas y estimaciones insertadas
                                conexion.rollback()

                                print(
                                    "\nERROR: no se pudo completar la actualización."
                                )

                                print(error)
                            

                    else:
                        print("No se detectaron campañas posteriores para actualizar.")

                else:

                    print("\nActualización cancelada. No se modificó la tabla.")

            else:

                print("\nNo se seleccionó ningún archivo.")

            input("\nPresione ENTER para continuar...")

        elif opcion == "2":
            break

        else:
            print("\nOpción inválida.")
















# ============================================================
# MENÚ PRINCIPAL
# ============================================================

def mostrar_menu_principal():

    # Formatos para la terminal
    NEGRITA = "\033[1m"
    CURSIVA = "\033[3m"
    TENUE = "\033[2m"
    NORMAL = "\033[0m"


    # --------------------------------------------------------
    # Función para mostrar textos centrados
    # --------------------------------------------------------

    def mostrar_texto_centrado(texto, ancho_texto=78):

        lineas = textwrap.wrap(
            texto,
            width=ancho_texto
        )

        for linea in lineas:

            print(
                linea.center(ANCHO)
            )


    # --------------------------------------------------------
    # Función para mostrar cada situación
    # --------------------------------------------------------

    def mostrar_descripcion(titulo, descripcion):

        print()

        print(
            NEGRITA
            + ("* " + titulo).center(ANCHO)
            + NORMAL
        )

        lineas = textwrap.wrap(
            descripcion,
            width=76
        )

        for linea in lineas:

            print(
                CURSIVA
                + TENUE
                + linea.center(ANCHO)
                + NORMAL
            )


    # --------------------------------------------------------
    # Período disponible en la base
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            MIN(ca.anio_inicio),
            MAX(ca.anio_inicio)
        FROM estimacion e
        JOIN campania ca
            ON e.campania_id = ca.campania_id
    """)

    periodo = cursor.fetchone()

    anio_desde = periodo[0]
    anio_hasta = periodo[1]

    rango_campanias = (
        f"{anio_desde}/{anio_desde + 1} - "
        f"{anio_hasta}/{anio_hasta + 1}"
    )



    # ========================================================
    # ENCABEZADO
    # ========================================================

    print(
        "\n"
        + "=" * ANCHO
    )

    print(
        NEGRITA
        + "MINISTERIO DE AGRICULTURA, GANADERÍA Y PESCA".center(ANCHO)
        + NORMAL
    )

    print(
        "Estadística agrícola por cultivo, campaña, provincia y departamento".center(ANCHO)
    )

    print(
        f"de la República Argentina | Campañas {rango_campanias}".center(ANCHO)
        )

    print(
        "=" * ANCHO
    )


    # ========================================================
    # PRESENTACIÓN DEL SISTEMA
    # ========================================================

    print()

    mostrar_texto_centrado(
        "El sistema contiene información estadística agrícola correspondiente "
        "a cultivos y campañas de la República Argentina, con datos de "
        "superficie sembrada, superficie cosechada, producción y rendimiento."
    )

    print()

    print(
        NEGRITA
        + "A partir de esta información permite detectar:".center(ANCHO)
        + NORMAL
    )


    # --------------------------------------------------------
    # Situación desfavorable 1
    # --------------------------------------------------------

    mostrar_descripcion(
        "Situación desfavorable 1 - Superficie no cosechada",

        "Identifica regiones, cultivos y campañas con una tasa de superficie "
        "no cosechada superior al umbral establecido."
    )


    # --------------------------------------------------------
    # Situación desfavorable 2
    # --------------------------------------------------------

    mostrar_descripcion(
        "Situación desfavorable 2 - Bajo rendimiento",

        "Identifica regiones cuyo rendimiento resulta inferior al rendimiento "
        "nacional del mismo cultivo y campaña."
    )


    # --------------------------------------------------------
    # Situación desfavorable 3
    # --------------------------------------------------------

    mostrar_descripcion(
        "Situación desfavorable 3 - Caída sostenida de la producción",

        "Identifica regiones y cultivos que presentan tres o más caídas "
        "consecutivas de producción."
    )


    # --------------------------------------------------------
    # Análisis de incidencia
    # --------------------------------------------------------

    mostrar_descripcion(
        "Análisis de incidencia en la caída de producción",

        "Evalúa, dentro de las caídas sostenidas detectadas, el comportamiento "
        "de la superficie cosechada y del rendimiento."
    )


    # --------------------------------------------------------
    # Focos críticos
    # --------------------------------------------------------

    mostrar_descripcion(
        "Focos críticos",

        "Identifica los casos en los que coinciden simultáneamente las tres "
        "situaciones desfavorables."
    )


    # ========================================================
    # OPCIONES DEL MENÚ
    # ========================================================

    print()

    print(
        "-" * ANCHO
    )

    print(
        NEGRITA
        + "INGRESE LA OPCIÓN QUE DESEA CONSULTAR".center(ANCHO)
        + NORMAL
    )

    print(
        "-" * ANCHO
    )

    print(
        SANGRIA_MENU
        + "1. Situación desfavorable 1 - Superficie no cosechada"
    )

    print(
        SANGRIA_MENU
        + "2. Situación desfavorable 2 - Bajo rendimiento"
    )

    print(
        SANGRIA_MENU
        + "3. Situación desfavorable 3 - Caída sostenida de la producción"
    )

    print(
        SANGRIA_MENU
        + "4. Análisis de incidencia en la caída de producción"
    )

    print(
        SANGRIA_MENU
        + "5. Focos críticos"
    )

    print(
        SANGRIA_MENU
        + "6. Búsqueda por región"
    )

    print(
        SANGRIA_MENU
        + "7. Búsqueda por cultivo y campaña"
    )

    print(
    SANGRIA_MENU
    + "8. Gestión de parámetros"
)

    print(
        SANGRIA_MENU
        + "9. Gestión de estimaciones"
    )

    print(
        SANGRIA_MENU
        + "10. Salir"
    )
    

    print(
        "-" * ANCHO
    )
















# ============================================================
# EJECUCIÓN DEL MENÚ PRINCIPAL
# ============================================================

while True:

    mostrar_menu_principal()

    opcion = input(
        SANGRIA_MENU
        + "Seleccione una opción: "
    )


    # --------------------------------------------------------
    # Opción 1 - Situación desfavorable 1
    # --------------------------------------------------------

    if opcion == "1":

        consultar_resumen_situacion_1()


    # --------------------------------------------------------
    # Opción 2 - Situación desfavorable 2
    # --------------------------------------------------------

    elif opcion == "2":

        print(
            "\nConsulta Situación Desfavorable 2"
        )


    # --------------------------------------------------------
    # Opción 3 - Situación desfavorable 3
    # --------------------------------------------------------

    elif opcion == "3":

        print(
            "\nConsulta Situación Desfavorable 3"
        )


    # --------------------------------------------------------
    # Opción 4 - Análisis de incidencia
    # --------------------------------------------------------

    elif opcion == "4":

        print(
            "\nConsulta Análisis de incidencia"
        )


    # --------------------------------------------------------
    # Opción 5 - Focos críticos
    # --------------------------------------------------------

    elif opcion == "5":

        menu_focos_criticos()


        # --------------------------------------------------------
    # Opción 6 - Búsqueda por región
    # --------------------------------------------------------

    elif opcion == "6":

        menu_busqueda_por_region()


    # --------------------------------------------------------
    # Opción 7 - Búsqueda por cultivo y campaña
    # --------------------------------------------------------

    elif opcion == "7":

        menu_busqueda_por_cultivo_campania()


    # --------------------------------------------------------
    # Opción 8 - Gestión de parámetros
    # --------------------------------------------------------

    elif opcion == "8":

        menu_gestion_parametros()


    # --------------------------------------------------------
    # Opción 9 - Gestión de Estimaciones
    # --------------------------------------------------------

    elif opcion == "9":

        menu_gestion_estimaciones()

    # --------------------------------------------------------
    # Opción 10 - Salir
    # --------------------------------------------------------

    elif opcion == "10":

        print("\nPrograma finalizado.")

        break


    # --------------------------------------------------------
    # Control de opción incorrecta
    # --------------------------------------------------------

    else:

        print(
            "\nOpción inválida. "
            "Ingrese una opción entre 1 y 9."
        )



