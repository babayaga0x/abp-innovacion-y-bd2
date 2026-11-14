# ============================================================
# APLICACIÓN DE GESTIÓN Y ANÁLISIS DE ESTIMACIONES AGRÍCOLAS
# ABP - Innovación en Gestión de Datos - Grupo META 7
# ============================================================
# Punto de entrada. Ejecutar desde la carpeta abp3:
#
#     python main.py
#
# 1. Conecta con MySQL.
# 2. Verifica el esquema (tablas de análisis, baja lógica, VIEW).
# 3. Recalcula las situaciones desfavorables.
# 4. Abre el menú principal.
# ============================================================

from db.conexion import obtener_conexion, cerrar
from db.esquema import asegurar_esquema
from servicios.calculo_analisis import recalcular_analisis
from ui.menu_principal import ejecutar_menu_principal


def main():

    obtener_conexion()
    print("Conexión exitosa")

    asegurar_esquema()
    print("Esquema verificado")

    casos = recalcular_analisis()
    print(
        f"Análisis calculado: "
        f"S1 {casos['situacion_1']} | S2 {casos['situacion_2']} | "
        f"S3 {casos['situacion_3']} | rachas {casos['rachas_3b']} | "
        f"focos críticos {casos['focos_criticos']}"
    )

    try:
        ejecutar_menu_principal()
    finally:
        cerrar()


if __name__ == "__main__":
    main()
