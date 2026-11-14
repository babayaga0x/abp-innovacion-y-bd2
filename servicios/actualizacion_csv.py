# ============================================================
# ALTA: ACTUALIZACIÓN INCREMENTAL DESDE UN NUEVO CSV
# ============================================================
# Flujo:
#
#   CSV completo
#       ↓
#   Python lee el archivo y detecta campañas posteriores
#       ↓
#   si existen campañas nuevas
#       ↓
#   se reemplaza el contenido de estimaciones_csv
#   únicamente con los registros de esas campañas
#       ↓
#   stg_estimaciones
#       ↓
#   control de inconsistencias
#       ↓
#   stg_estimaciones_depuradas
#       ↓
#   cultivo / campania / estimacion
#
# La aplicación compara las campañas del CSV con el último
# anio_inicio cargado en estimacion antes de modificar la base.
#
# Si no existen campañas nuevas, estimaciones_csv no se modifica.
# Si existen, se carga únicamente el subconjunto nuevo detectado
# por Python. La limpieza y transformación continúan en SQL.
#
# Cada etapa se ejecuta de forma independiente y las
# confirmaciones del usuario se manejan desde ui/menu_gestion.py.
# ============================================================

import csv

from db.conexion import (
    consultar,
    ejecutar,
    ejecutar_varios,
    confirmar,
    revertir
)
from modelos.estimacion import Estimacion

# ============================================================
# 1. LECTURA Y DETECCIÓN DE CAMPAÑAS NUEVAS
# ============================================================

def leer_registros_nuevos(ruta_csv):
    """
    Lee el CSV completo desde Python y conserva en memoria
    únicamente los registros pertenecientes a campañas
    posteriores a la última ya cargada en estimacion.

    En esta etapa no se modifica ninguna tabla de MySQL.
    """

    ultimo_anio = Estimacion.ultimo_anio_cargado()

    columnas_esperadas = [
        "cultivo",
        "anio",
        "campania",
        "provincia",
        "provincia_id",
        "departamento",
        "departamento_id",
        "superficie_sembrada_ha",
        "superficie_cosechada_ha",
        "produccion_tm",
        "rendimiento_kgxha"
    ]

    registros_nuevos = []
    anios_nuevos = []

    for codificacion in ("utf-8-sig", "latin-1"):

        try:

            # Si el primer intento falló durante la lectura,
            # se eliminan los registros parciales antes de reintentar.
            registros_nuevos.clear()
            anios_nuevos.clear()

            with open(
                ruta_csv,
                "r",
                encoding=codificacion,
                newline=""
            ) as archivo:

                lector = csv.DictReader(archivo)

                columnas_archivo = set(lector.fieldnames or [])

                columnas_faltantes = [
                    columna
                    for columna in columnas_esperadas
                    if columna not in columnas_archivo
                ]

                if columnas_faltantes:
                    raise ValueError(
                        "El archivo CSV no contiene todas las columnas requeridas. "
                        f"Faltan: {', '.join(columnas_faltantes)}"
                    )

                for numero_fila, fila in enumerate(lector, start=2):

                    campania = (fila["campania"] or "").strip()

                    if "/" not in campania:
                        raise ValueError(
                            f"Fila {numero_fila}: formato de campaña inválido: "
                            f"'{campania}'. Se esperaba un formato como 2025/2026."
                        )

                    try:
                        anio_inicio = int(
                            campania.split("/", 1)[0].strip()
                        )
                    except ValueError:
                        raise ValueError(
                            f"Fila {numero_fila}: formato de campaña inválido: "
                            f"'{campania}'. No se pudo identificar el año de inicio."
                        ) from None

                    if anio_inicio > ultimo_anio:

                        registros_nuevos.append(
                            tuple(
                                fila[columna]
                                for columna in columnas_esperadas
                            )
                        )

                        anios_nuevos.append(anio_inicio)

                # Si llegó hasta acá, el archivo pudo leerse correctamente.
                break

        except UnicodeDecodeError:

            # Si UTF-8 falla, vuelve a intentar con Latin-1.
            if codificacion == "latin-1":
                raise
    anio_min = min(anios_nuevos) if anios_nuevos else None
    anio_max = max(anios_nuevos) if anios_nuevos else None

    return ultimo_anio, registros_nuevos, anio_min, anio_max

# ============================================================
# 2. CARGA DE LOS REGISTROS NUEVOS EN LA TABLA CRUDA
# ============================================================

def cargar_registros_nuevos(registros_nuevos):
    """
    Reemplaza el contenido de estimaciones_csv únicamente cuando
    Python detectó registros correspondientes a campañas nuevas.

    Los datos se cargan en estado crudo. La limpieza y las
    transformaciones posteriores continúan realizándose en SQL.
    """

    if not registros_nuevos:
        return 0

    try:

        ejecutar("DELETE FROM estimaciones_csv")

        ejecutar_varios("""
            INSERT INTO estimaciones_csv (
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
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
        """, registros_nuevos)

        confirmar()

    except Exception:
        revertir()
        raise

    return len(registros_nuevos)


# ============================================================
# 3. STAGING DE LOS REGISTROS NUEVOS
# ============================================================

def preparar_stg_estimaciones(ultimo_anio):

    ejecutar("DELETE FROM stg_estimaciones")

    ejecutar("""
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

            CAST(SUBSTRING_INDEX(campania, '/', 1) AS UNSIGNED),

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
                    CAST(CONVERT(TRIM(departamento) USING latin1) AS BINARY)
                    USING utf8mb4
                ),
                TRIM(departamento)
            ),

            NULLIF(departamento_id, '') + 0,

            -- Regionalización COFEMA según provincia_id
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

    # Mismas reglas básicas de limpieza de la carga inicial
    ejecutar("""
        DELETE FROM stg_estimaciones
        WHERE provincia_id IS NULL
           OR cultivo IS NULL
           OR cultivo = ''
           OR campania IS NULL
           OR campania = ''
    """)

    ejecutar("""
        UPDATE stg_estimaciones
        SET rendimiento_kgxha = NULL
        WHERE rendimiento_kgxha < 0
    """)

    confirmar()


# ============================================================
# 4. CONTROL DE INCONSISTENCIAS (VIEW)
# ============================================================
# Compara, por departamento, los registros "<cultivo> total"
# con la suma de sus componentes. Los casos fuera de tolerancia
# (máx. entre 1 unidad y 0,1 % del total) se reclasifican a
# nivel provincial; los que siguen fuera de tolerancia quedan en
# la VIEW como REQUIERE REVISIÓN y bloquean la actualización.
# ============================================================

def crear_view_inconsistencias():

    ejecutar("""
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

                SUM(CASE WHEN LOWER(TRIM(s.cultivo)) = LOWER(ct.cultivo_total)
                         THEN 1 ELSE 0 END) AS registros_total,

                SUM(CASE WHEN LOWER(TRIM(s.cultivo)) <> LOWER(ct.cultivo_total)
                         THEN 1 ELSE 0 END) AS registros_componentes,

                SUM(CASE WHEN LOWER(TRIM(s.cultivo)) = LOWER(ct.cultivo_total)
                         THEN s.superficie_sembrada_ha ELSE 0 END) AS sembrada_total,

                SUM(CASE WHEN LOWER(TRIM(s.cultivo)) <> LOWER(ct.cultivo_total)
                         THEN s.superficie_sembrada_ha ELSE 0 END) AS sembrada_componentes,

                SUM(CASE WHEN LOWER(TRIM(s.cultivo)) = LOWER(ct.cultivo_total)
                         THEN s.superficie_cosechada_ha ELSE 0 END) AS cosechada_total,

                SUM(CASE WHEN LOWER(TRIM(s.cultivo)) <> LOWER(ct.cultivo_total)
                         THEN s.superficie_cosechada_ha ELSE 0 END) AS cosechada_componentes,

                SUM(CASE WHEN LOWER(TRIM(s.cultivo)) = LOWER(ct.cultivo_total)
                         THEN s.produccion_tm ELSE 0 END) AS produccion_total,

                SUM(CASE WHEN LOWER(TRIM(s.cultivo)) <> LOWER(ct.cultivo_total)
                         THEN s.produccion_tm ELSE 0 END) AS produccion_componentes

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
                sembrada_total - sembrada_componentes AS diferencia_sembrada,
                cosechada_total - cosechada_componentes AS diferencia_cosechada,
                produccion_total - produccion_componentes AS diferencia_produccion

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

                SUM(sembrada_total) AS sembrada_total_provincia,
                SUM(sembrada_componentes) AS sembrada_componentes_provincia,
                SUM(cosechada_total) AS cosechada_total_provincia,
                SUM(cosechada_componentes) AS cosechada_componentes_provincia,
                SUM(produccion_total) AS produccion_total_provincia,
                SUM(produccion_componentes) AS produccion_componentes_provincia

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
                rp.sembrada_total_provincia - rp.sembrada_componentes_provincia,
                2
            ) AS diferencia_provincial_sembrada,

            ROUND(
                rp.cosechada_total_provincia - rp.cosechada_componentes_provincia,
                2
            ) AS diferencia_provincial_cosechada,

            ROUND(
                rp.produccion_total_provincia - rp.produccion_componentes_provincia,
                2
            ) AS diferencia_provincial_produccion

        FROM revision_departamental rd

        JOIN resumen_provincial rp
            ON rp.cultivo_base = rd.cultivo_base
           AND rp.campania = rd.campania
           AND rp.provincia_id = rd.provincia_id

        WHERE NOT (

            ABS(rp.sembrada_total_provincia - rp.sembrada_componentes_provincia)
            <= GREATEST(1, ABS(rp.sembrada_total_provincia) * 0.001)

            AND ABS(rp.cosechada_total_provincia - rp.cosechada_componentes_provincia)
            <= GREATEST(1, ABS(rp.cosechada_total_provincia) * 0.001)

            AND ABS(rp.produccion_total_provincia - rp.produccion_componentes_provincia)
            <= GREATEST(1, ABS(rp.produccion_total_provincia) * 0.001)
        )

        AND NOT (
               rp.sembrada_total_provincia >= rp.sembrada_componentes_provincia
           AND rp.cosechada_total_provincia >= rp.cosechada_componentes_provincia
           AND rp.produccion_total_provincia >= rp.produccion_componentes_provincia
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

    confirmar()


def listar_inconsistencias():

    return consultar("""
        SELECT
            cultivo_base,
            campania,
            provincia,
            departamentos_en_revision
        FROM vw_inconsistencias_actualizacion
        ORDER BY provincia, cultivo_base
    """)


# ============================================================
# 5. DEPURACIÓN DE LOS REGISTROS NUEVOS
# ============================================================
# Cuando coexisten "<cultivo> total" y sus componentes en la
# misma campaña y provincia, se conserva el total para evitar
# doble contabilización.
# ============================================================

def preparar_stg_estimaciones_depuradas():

    ejecutar("DELETE FROM stg_estimaciones_depuradas")

    ejecutar("""
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
                ON LOWER(TRIM(s.cultivo)) = LOWER(ct.cultivo_total)
        ),

        filas_clasificadas AS (

            SELECT
                s.*,
                ct.cultivo_base,
                ct.cultivo_total

            FROM stg_estimaciones s

            LEFT JOIN cultivos_totales ct
                ON LOWER(TRIM(s.cultivo)) = LOWER(ct.cultivo_total)
                OR LOWER(TRIM(s.cultivo)) = LOWER(ct.cultivo_base)
                OR LOWER(TRIM(s.cultivo))
                   LIKE CONCAT(LOWER(ct.cultivo_base), ' %')
        )

        SELECT
            COALESCE(f.cultivo_base, f.cultivo) AS cultivo,
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
            ON LOWER(td.cultivo_base) = LOWER(f.cultivo_base)
           AND td.campania = f.campania
           AND td.provincia_id = f.provincia_id

        WHERE f.cultivo_base IS NULL
           OR LOWER(TRIM(f.cultivo)) = LOWER(f.cultivo_total)
           OR td.cultivo_total IS NULL
    """)

    confirmar()


# ============================================================
# 6. CONTROL DE PROVINCIAS DESCONOCIDAS
# ============================================================

def buscar_provincias_desconocidas():

    return consultar("""
        SELECT
            s.provincia_id,
            MAX(s.provincia) AS provincia

        FROM stg_estimaciones_depuradas s

        LEFT JOIN provincia p
            ON p.provincia_id = s.provincia_id

        WHERE p.provincia_id IS NULL

        GROUP BY s.provincia_id

        ORDER BY provincia
    """)


# ============================================================
# 7. INCORPORACIÓN DEFINITIVA (una única transacción)
# ============================================================

def incorporar_estimaciones_nuevas():
    """
    Agrega cultivos y campañas nuevas y carga las estimaciones.
    Si falla cualquier paso se revierte todo.
    Devuelve (cultivos nuevos, campañas nuevas, estimaciones nuevas).
    """

    try:

        # Cultivos que todavía no existen
        cultivos_nuevos = ejecutar("""
            INSERT INTO cultivo (cultivo_nombre)
            SELECT DISTINCT s.cultivo
            FROM stg_estimaciones_depuradas s
            WHERE s.cultivo IS NOT NULL
              AND s.cultivo <> ''
              AND NOT EXISTS (
                  SELECT 1 FROM cultivo c
                  WHERE c.cultivo_nombre = s.cultivo
              )
        """)

        # Campañas que todavía no existen
        campanias_nuevas = ejecutar("""
            INSERT INTO campania (campania, anio_inicio)
            SELECT
                s.campania,
                MAX(s.anio_inicio)
            FROM stg_estimaciones_depuradas s
            WHERE s.campania IS NOT NULL
              AND s.campania <> ''
              AND NOT EXISTS (
                  SELECT 1 FROM campania ca
                  WHERE ca.campania = s.campania
              )
            GROUP BY s.campania
        """)

        # Estimaciones agregadas por cultivo + campaña + provincia
        estimaciones_nuevas = ejecutar("""
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

        confirmar()

    except Exception:

        revertir()
        raise

    return cultivos_nuevos, campanias_nuevas, estimaciones_nuevas
