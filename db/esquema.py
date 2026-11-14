# ============================================================
# ESQUEMA DE LA BASE
# ============================================================
# Garantiza que existan las tablas que crea la aplicación
# (parámetros y resultados de análisis), las columnas de baja
# lógica de estimacion y la VIEW de focos críticos.
#
# Las tablas del modelo normalizado (region, provincia,
# cultivo, campania, estimacion) y las de staging se crean en
# el script SQL de la base (Evidencia 1).
#
# Todas las sentencias son idempotentes: se puede ejecutar en
# cada inicio sin alterar datos existentes.
# ============================================================

from db.conexion import consultar, consultar_uno, ejecutar, confirmar


PARAMETROS_INICIALES = [
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


# ============================================================
# PARÁMETROS DE ANÁLISIS
# ============================================================

def crear_tabla_parametros():

    ejecutar("""
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

    # Solo se insertan los parámetros que todavía no existen.
    # (INSERT IGNORE consumía un valor de AUTO_INCREMENT en
    # cada ejecución aunque no insertara nada.)
    existentes = {
        fila[0]
        for fila in consultar("SELECT nombre FROM parametro_analisis")
    }

    for nombre, valor, descripcion, obligatorio in PARAMETROS_INICIALES:

        if nombre not in existentes:

            ejecutar("""
                INSERT INTO parametro_analisis
                    (nombre, valor, descripcion, es_obligatorio)
                VALUES (%s, %s, %s, %s)
            """, (nombre, valor, descripcion, obligatorio))


# ============================================================
# BAJA LÓGICA DE ESTIMACIONES
# ============================================================
# activa = 'SI'  → la estimación participa de los análisis.
# activa = 'NO'  → fue dada de baja; se conserva el registro
#                  con la fecha y el motivo, y puede
#                  reactivarse.
# ============================================================

COLUMNAS_BAJA_LOGICA = [
    ("activa", "CHAR(2) NOT NULL DEFAULT 'SI'"),
    ("fecha_baja", "DATETIME NULL"),
    ("motivo_baja", "VARCHAR(255) NULL")
]


def existe_columna(tabla, columna):

    fila = consultar_uno("""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
    """, (tabla, columna))

    return fila[0] > 0


def agregar_columnas_baja_logica():

    for columna, definicion in COLUMNAS_BAJA_LOGICA:

        if not existe_columna("estimacion", columna):

            ejecutar(
                f"ALTER TABLE estimacion ADD COLUMN {columna} {definicion}"
            )


# ============================================================
# TABLAS DE ANÁLISIS
# ============================================================

def crear_tablas_analisis():

    ejecutar("""
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

    ejecutar("""
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

    ejecutar("""
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

    ejecutar("""
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

    ejecutar("""
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

            FOREIGN KEY (cultivo_id) REFERENCES cultivo(cultivo_id),
            FOREIGN KEY (region_id) REFERENCES region(region_id),
            FOREIGN KEY (analisis_id_inicio)
                REFERENCES analisis_regional(analisis_id),
            FOREIGN KEY (analisis_id_fin)
                REFERENCES analisis_regional(analisis_id)
        )
    """)


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

def crear_view_foco_critico():

    ejecutar("""
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


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

def asegurar_esquema():

    crear_tabla_parametros()
    agregar_columnas_baja_logica()
    crear_tablas_analisis()
    crear_view_foco_critico()

    confirmar()
