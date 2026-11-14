# ============================================================
# GESTIÓN (opciones 8 y 9 del menú principal)
# ============================================================
# Operaciones CRUD:
#
#   Alta          Actualización incremental desde un nuevo CSV
#   Baja          Baja lógica de una estimación (reversible)
#   Modificación  Valor de los parámetros de análisis
#   Consulta      Opciones de análisis y búsquedas
#
# Toda operación que cambia los datos o los parámetros vuelve
# a calcular las situaciones desfavorables al terminar.
# ============================================================

from tkinter import Tk, filedialog

from modelos.dimensiones import Cultivo, Campania
from modelos.estimacion import Estimacion
from modelos.parametro import ParametroAnalisis
from servicios import actualizacion_csv
from servicios.calculo_analisis import recalcular_analisis
from ui.consola import (
    limpiar_pantalla,
    pausar,
    titulo,
    miles,
    imprimir_tabla,
    elegir_de_lista,
    confirmar_accion
)


def recalcular_y_mostrar():

    print("\nRecalculando situaciones desfavorables...")

    casos = recalcular_analisis()

    print(
        f"Análisis actualizado: "
        f"S1 {casos['situacion_1']} casos | "
        f"S2 {casos['situacion_2']} casos | "
        f"S3 {casos['situacion_3']} casos | "
        f"{casos['rachas_3b']} rachas | "
        f"{casos['focos_criticos']} focos críticos"
    )


# ============================================================
# OPCIÓN 8 - GESTIÓN DE PARÁMETROS
# ============================================================

def menu_gestion_parametros():

    while True:

        limpiar_pantalla()
        titulo("GESTIÓN DE PARÁMETROS", 80)

        print("\n1. Ver parámetros")
        print("2. Modificar parámetro")
        print("3. Volver al menú principal")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "1":
            ver_parametros()

        elif opcion == "2":
            modificar_parametro()

        elif opcion == "3":
            limpiar_pantalla()
            return

        else:
            pausar("Opción inválida. Presione ENTER...")


def ver_parametros():

    limpiar_pantalla()

    columnas = [
        ("NOMBRE", 28, "<"),
        ("VALOR", 10, ">"),
        ("  DESCRIPCIÓN", 82, "<")
    ]

    filas = [
        (p.nombre, p.valor, "  " + (p.descripcion or ""))
        for p in ParametroAnalisis.listar()
    ]

    imprimir_tabla(columnas, filas, "PARÁMETROS DE ANÁLISIS")

    pausar("Presione ENTER para volver...")


def modificar_parametro():

    limpiar_pantalla()

    parametro = elegir_de_lista(
        ParametroAnalisis.listar(),
        mostrar=lambda p: f"{p.nombre:<30}Valor actual: {p.valor}",
        encabezado="MODIFICAR PARÁMETRO",
        nombre="un parámetro"
    )

    if parametro is None:
        return

    try:
        nuevo_valor = float(
            input(f"\nNuevo valor para {parametro.nombre}: ").replace(",", ".")
        )
    except ValueError:
        pausar("El valor ingresado debe ser numérico. Presione ENTER...")
        return

    error = parametro.validar(nuevo_valor)

    if error:
        pausar(f"{error} Presione ENTER...")
        return

    parametro.modificar(nuevo_valor)

    print("\nParámetro modificado correctamente.")

    recalcular_y_mostrar()

    pausar()


# ============================================================
# OPCIÓN 9 - GESTIÓN DE ESTIMACIONES
# ============================================================

def menu_gestion_estimaciones():

    while True:

        limpiar_pantalla()
        titulo("GESTIÓN DE ESTIMACIONES")

        conteo = Estimacion.contar_por_estado()

        print(
            f"\nEstimaciones activas: {conteo['SI']} | "
            f"dadas de baja: {conteo['NO']}"
        )

        print("\n1. Actualizar base desde nuevo archivo CSV (alta)")
        print("2. Dar de baja una estimación")
        print("3. Reactivar una estimación dada de baja")
        print("4. Ver estimaciones dadas de baja")
        print("5. Volver al menú principal")

        opcion = input("\nIngrese una opción: ").strip()

        if opcion == "1":
            actualizar_desde_csv()

        elif opcion == "2":
            dar_de_baja_estimacion()

        elif opcion == "3":
            reactivar_estimacion()

        elif opcion == "4":
            ver_estimaciones_inactivas()
            pausar()

        elif opcion == "5":
            limpiar_pantalla()
            return

        else:
            pausar("Opción inválida. Presione ENTER...")


# ------------------------------------------------------------
# BAJA LÓGICA
# ------------------------------------------------------------

def mostrar_estimacion(estimacion):

    print()
    print(f"Cultivo:              {estimacion.cultivo_nombre}")
    print(f"Campaña:              {estimacion.campania}")
    print(f"Provincia / Región:   {estimacion.provincia_nombre} / {estimacion.region_nombre}")
    print(f"Superficie sembrada:  {miles(estimacion.superficie_sembrada_ha)} ha")
    print(f"Superficie cosechada: {miles(estimacion.superficie_cosechada_ha)} ha")
    print(f"Producción:           {miles(estimacion.produccion_tm)} t")
    print(f"Rendimiento:          {miles(estimacion.rendimiento_kgxha)} kg/ha")

    if not estimacion.esta_activa():
        print(f"Fecha de baja:        {estimacion.fecha_baja:%d/%m/%Y %H:%M}")
        print(f"Motivo de baja:       {estimacion.motivo_baja}")


def dar_de_baja_estimacion():

    limpiar_pantalla()

    cultivo = elegir_de_lista(
        Cultivo.listar(),
        encabezado="DAR DE BAJA UNA ESTIMACIÓN\n\nCULTIVOS",
        nombre="un cultivo"
    )

    if cultivo is None:
        return

    limpiar_pantalla()

    campania = elegir_de_lista(
        Campania.listar(),
        encabezado=f"CULTIVO: {cultivo}\n\nCAMPAÑAS",
        nombre="una campaña"
    )

    if campania is None:
        return

    limpiar_pantalla()

    estimacion = elegir_de_lista(
        Estimacion.listar_por_cultivo_campania(
            cultivo.cultivo_id,
            campania.campania_id
        ),
        mostrar=lambda e: (
            f"{e.provincia_nombre:<24}{e.region_nombre:<18}"
            f"producción {miles(e.produccion_tm):>12} t"
        ),
        encabezado=f"ESTIMACIONES ACTIVAS - {cultivo} {campania}",
        nombre="una estimación"
    )

    if estimacion is None:
        return

    limpiar_pantalla()
    titulo("ESTIMACIÓN SELECCIONADA")
    mostrar_estimacion(estimacion)

    print(
        "\nLa estimación no se elimina: queda marcada como inactiva, "
        "se excluye de los\nanálisis y puede reactivarse desde este mismo menú."
    )

    motivo = input("\nMotivo de la baja (obligatorio, ENTER para cancelar): ").strip()

    if not motivo:
        pausar("Baja cancelada. Presione ENTER...")
        return

    if not confirmar_accion("¿Confirma la baja de la estimación?"):
        pausar("Baja cancelada. Presione ENTER...")
        return

    estimacion.dar_de_baja(motivo[:255])

    print("\nEstimación dada de baja correctamente.")

    recalcular_y_mostrar()

    pausar()


def ver_estimaciones_inactivas():

    limpiar_pantalla()

    inactivas = Estimacion.listar_inactivas()

    columnas = [
        ("CULTIVO", 20, "<"),
        ("CAMPAÑA", 12, "<"),
        ("PROVINCIA", 22, "<"),
        ("PRODUCCIÓN (t)", 16, ">"),
        ("  FECHA BAJA", 20, "<"),
        ("MOTIVO", 40, "<")
    ]

    filas = [
        (
            e.cultivo_nombre,
            e.campania,
            e.provincia_nombre,
            miles(e.produccion_tm),
            f"  {e.fecha_baja:%d/%m/%Y %H:%M}",
            e.motivo_baja
        )
        for e in inactivas
    ]

    imprimir_tabla(columnas, filas, "ESTIMACIONES DADAS DE BAJA")

    print("Estimaciones dadas de baja:", len(inactivas))

    return inactivas


def reactivar_estimacion():

    inactivas = ver_estimaciones_inactivas()

    if not inactivas:
        pausar()
        return

    estimacion = elegir_de_lista(
        inactivas,
        mostrar=lambda e: f"{e.cultivo_nombre} {e.campania} - {e.provincia_nombre}",
        encabezado="REACTIVAR",
        nombre="una estimación"
    )

    if estimacion is None:
        return

    mostrar_estimacion(estimacion)

    if not confirmar_accion("¿Confirma la reactivación de la estimación?"):
        pausar("Reactivación cancelada. Presione ENTER...")
        return

    estimacion.reactivar()

    print("\nEstimación reactivada correctamente.")

    recalcular_y_mostrar()

    pausar()


# ------------------------------------------------------------
# ALTA: ACTUALIZACIÓN INCREMENTAL DESDE CSV
# ------------------------------------------------------------

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


def actualizar_desde_csv(ruta_csv=None):

    limpiar_pantalla()
    titulo("ACTUALIZACIÓN DESDE NUEVO ARCHIVO CSV")

    ruta_csv = ruta_csv or seleccionar_archivo_csv()

    if not ruta_csv:
        pausar("No se seleccionó ningún archivo. Presione ENTER...")
        return

    print("\nArchivo seleccionado:")
    print(ruta_csv)

    # 1. Lectura del CSV y detección de campañas nuevas
    try:
        ultimo_anio, registros_nuevos, anio_min, anio_max = (
            actualizacion_csv.leer_registros_nuevos(ruta_csv)
        )

    except ValueError as error:
        pausar(
            f"\nNo se pudo procesar el archivo:\n{error}\n\n"
            "No se realizaron cambios en la base. "
            "Presione ENTER..."
        )
        return


    cantidad_nuevos = len(registros_nuevos)

    print(f"\n[1/6] Último año cargado en estimacion: {ultimo_anio}")
    print(f"      Registros nuevos detectados: {miles(cantidad_nuevos)}")


    if cantidad_nuevos == 0:
        pausar(
            "No se detectaron campañas posteriores para actualizar. "
            "No se realizaron cambios en la base. Presione ENTER..."
        )
        return


    print(f"      Rango de años nuevos detectado: {anio_min} - {anio_max}")


    if not confirmar_accion(
        "Se reemplazará el contenido de estimaciones_csv "
        "únicamente con los registros nuevos detectados.\n"
        "¿Desea continuar?"
    ):
        pausar(
            "Actualización cancelada. "
            "No se modificó la base. Presione ENTER..."
        )
        return


    # 2. Carga de los registros nuevos en la tabla cruda
    cantidad = actualizacion_csv.cargar_registros_nuevos(
        registros_nuevos
    )

    print("\n[2/6] Registros nuevos cargados correctamente.")
    print(
        f"      Registros cargados en estimaciones_csv: "
        f"{miles(cantidad)}"
    )

    # 3. Staging
    actualizacion_csv.preparar_stg_estimaciones(ultimo_anio)

    print("\n[3/6] Registros nuevos preparados en stg_estimaciones.")

    # 4. Control de inconsistencias
    actualizacion_csv.crear_view_inconsistencias()
    inconsistencias = actualizacion_csv.listar_inconsistencias()

    if inconsistencias:

        print(
            f"\n[4/6] ATENCIÓN: {len(inconsistencias)} casos requieren revisión "
            "(vw_inconsistencias_actualizacion):\n"
        )

        for cultivo, campania, provincia, departamentos in inconsistencias[:15]:
            print(f"      - {cultivo} {campania} - {provincia} ({departamentos} departamentos)")

        pausar(
            "La actualización fue detenida. No se modificaron las tablas finales. "
            "Presione ENTER..."
        )
        return

    print("\n[4/6] Control de inconsistencias superado. No quedan casos pendientes.")

    if not confirmar_accion("¿Desea continuar con la actualización de la base?"):
        pausar("Actualización cancelada. No se modificaron las tablas finales. Presione ENTER...")
        return

    # 5. Depuración y control de provincias
    actualizacion_csv.preparar_stg_estimaciones_depuradas()

    print("\n[5/6] Registros depurados en stg_estimaciones_depuradas.")

    provincias_desconocidas = actualizacion_csv.buscar_provincias_desconocidas()

    if provincias_desconocidas:

        print("\nATENCIÓN: se detectaron provincias no reconocidas:")

        for provincia_id, provincia in provincias_desconocidas:
            print(f"      - ID {provincia_id}: {provincia}")

        pausar(
            "La actualización fue detenida. No se modificaron las tablas finales. "
            "Presione ENTER..."
        )
        return

    # 6. Incorporación definitiva (una transacción)
    try:

        cultivos, campanias, estimaciones = (
            actualizacion_csv.incorporar_estimaciones_nuevas()
        )

    except Exception as error:

        print("\nERROR: no se pudo completar la actualización. Se revirtieron los cambios.")
        print(error)
        pausar()
        return

    print("\n[6/6] Actualización realizada correctamente.")
    print(f"      Cultivos nuevos: {cultivos}")
    print(f"      Campañas nuevas: {campanias}")
    print(f"      Estimaciones incorporadas: {estimaciones}")

    recalcular_y_mostrar()

    rango = Campania.rango_cargado()
    print(f"\nPeríodo disponible: {Campania.formatear_rango(*rango)}")

    pausar()
