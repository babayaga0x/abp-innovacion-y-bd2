# ============================================================
# CALIDAD INICIAL DE LOS DATOS (CSV crudo)
# ============================================================
# Diagnóstico con pandas de la tabla estimaciones_csv, que
# guarda el archivo oficial tal como se descargó (todas las
# columnas como texto). Justifica las reglas de limpieza que
# se aplican en SQL antes de cargar el modelo normalizado.
# ============================================================

import numpy as np
import pandas as pd

from procesamiento.carga import a_dataframe


COLUMNAS_NUMERICAS = [
    "superficie_sembrada_ha",
    "superficie_cosechada_ha",
    "produccion_tm",
    "rendimiento_kgxha"
]


def cargar_csv_crudo():
    return a_dataframe("SELECT * FROM estimaciones_csv")


def diagnostico_calidad(crudo):

    # Valores faltantes: nulos o cadenas vacías
    vacios = crudo.replace(r"^\s*$", np.nan, regex=True)

    faltantes = pd.DataFrame({
        "faltantes": vacios.isna().sum(),
        "faltantes_pct": vacios.isna().mean() * 100
    })

    numericos = vacios[COLUMNAS_NUMERICAS].apply(pd.to_numeric, errors="coerce")

    no_numericos = (numericos.isna() & vacios[COLUMNAS_NUMERICAS].notna()).sum()

    # Campañas con formato "AAAA/AAAA"
    campania = vacios["campania"].str.strip()
    anio_campania = pd.to_numeric(campania.str[:4], errors="coerce")

    cultivo = vacios["cultivo"].str.strip().str.lower()

    claves = ["cultivo", "campania", "provincia_id", "departamento_id"]

    controles = {
        "Registros": len(crudo),
        "Filas duplicadas exactas": int(crudo.duplicated().sum()),
        "Duplicados lógicos (cultivo + campaña + departamento)":
            int(vacios.duplicated(subset=claves).sum()),
        "Registros 'total' (p. ej. 'soja total')": int(cultivo.str.endswith(" total").sum()),
        "Cultivos distintos (crudo)": int(cultivo.nunique()),
        "Superficie cosechada mayor que la sembrada":
            int((numericos["superficie_cosechada_ha"] > numericos["superficie_sembrada_ha"]).sum()),
        "Rendimiento negativo": int((numericos["rendimiento_kgxha"] < 0).sum()),
        "Producción con superficie cosechada 0":
            int(((numericos["superficie_cosechada_ha"] == 0) & (numericos["produccion_tm"] > 0)).sum()),
        "Año de inicio (campaña) distinto de la columna anio":
            int((anio_campania != pd.to_numeric(vacios["anio"], errors="coerce")).sum()),
        "Primera campaña": f"{int(anio_campania.min())}/{int(anio_campania.min()) + 1}",
        "Última campaña": f"{int(anio_campania.max())}/{int(anio_campania.max()) + 1}"
    }

    resumen = pd.Series(controles, name="valor").to_frame()

    return faltantes, no_numericos, resumen
