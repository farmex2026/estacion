import io
import os
import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestión Integral de Estación", page_icon="⛽", layout="wide"
)

st.sidebar.markdown("---")
st.sidebar.markdown("🛠️ **Creado por Lucas-Farmex 2026**")

# Inicialización de Estados Globales estructurados por Mes
if "datos_2026" not in st.session_state:
    st.session_state.datos_2026 = {}  # {mes: df}
if "datos_2025" not in st.session_state:
    st.session_state.datos_2025 = {}  # {mes: df}
if "turnos_2026" not in st.session_state:
    st.session_state.turnos_2026 = {}  # {mes: df}
if "turnos_2025" not in st.session_state:
    st.session_state.turnos_2025 = {}  # {mes: df}
if "full_global" not in st.session_state:
    st.session_state.full_global = {}  # {mes: df}
if "boxes_global" not in st.session_state:
    st.session_state.boxes_global = {}  # {mes: df}

menu_principal = st.sidebar.selectbox(
    "📂 Menú Principal",
    ["Ventas 2026", "🌙 Turnos por Día", "🛒 Tienda Full", "📦 BOXES"],
)

meses_lista = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]


# Funciones de formato seguro estilo argentino (Punto para miles, Coma para decimales)
def fmt_litros(val):
    if pd.isna(val):
        return "0,00 L"
    partes = f"{val:,.2f}".split(".")
    enteros = partes[0].replace(",", ".")
    decimales = partes[1]
    return f"{enteros},{decimales} L"


def fmt_entero(val):
    if pd.isna(val):
        return "0"
    return f"{int(val):,}".replace(",", ".")


def fmt_porcentaje(val):
    if pd.isna(val):
        return "0,00%"
    partes = f"{val:,.2f}".split(".")
    enteros = partes[0].replace(",", ".")
    decimales = partes[1]
    return f"{enteros},{decimales}%"


def procesar_archivos_playa_detalle(archivos):
    lista_dfs = []
    for archivo in archivos:
        try:
            df_raw = pd.read_excel(archivo, header=None)
            if len(df_raw) > 7:
                df_detalles = pd.DataFrame()
                df_detalles["Fecha y Hora"] = df_raw.iloc[7:, 0]  # Columna A
                df_detalles["Surtidor/Manguera"] = df_raw.iloc[7:, 1]  # Columna B
                df_detalles["Producto"] = df_raw.iloc[7:, 3]  # Columna D
                df_detalles["Monto"] = (
                    pd.to_numeric(df_raw.iloc[7:, 6], errors="coerce")
                    .fillna(0)
                )  # Columna G
                df_detalles["Volumen"] = (
                    pd.to_numeric(df_raw.iloc[7:, 7], errors="coerce")
                    .fillna(0)
                )  # Columna H

                df_detalles = df_detalles.dropna(
                    subset=["Producto", "Volumen"], how="all"
                )

                # FILTRO ESTRICTO: Solo conservar filas cuya "Fecha y Hora" sea una fecha real.
                # Esto elimina automáticamente la fila de totales del final del Excel, textos y cabeceras sueltas.
                df_detalles["_fecha_dt"] = pd.to_datetime(
                    df_detalles["Fecha y Hora"], errors="coerce"
                )
                df_detalles = df_detalles.dropna(subset=["_fecha_dt"])
                df_detalles = df_detalles.drop(columns=["_fecha_dt"])

                # Filtro adicional de seguridad por si queda texto como "TOTAL" o "SUMA"
                mask_totales = (
                    df_detalles["Fecha y Hora"]
                    .astype(str)
                    .str.upper()
                    .str.contains("TOTAL|SUMA|SUBTOTAL", na=False)
                ) | (
                    df_detalles["Producto"]
                    .astype(str)
                    .str.upper()
                    .str.contains("TOTAL|SUMA|SUBTOTAL", na=False)
                )
                df_detalles = df_detalles[~mask_totales]

                lista_dfs.append(df_detalles)
        except Exception as e:
            st.warning(f"Aviso al procesar {archivo.name}: {e}")

    if lista_dfs:
        df_concatenado = pd.concat(lista_dfs, ignore_index=True)
        df_concatenado = df_concatenado.drop_duplicates().reset_index(
            drop=True
        )
        return df_concatenado
    return pd.DataFrame()


def procesar_archivos_playa(archivos):
    datos_acumulados = []
    for archivo in archivos:
        nombre_archivo = os.path.splitext(archivo.name)[0]
        try:
            num_dia = int(str(nombre_archivo).split("-")[0].strip())
        except:
            num_dia = 999

        df_diario = pd.read_excel(archivo)

        if (
            "Descripción Producto" in df_diario.columns
            and "Venta Informada" in df_diario.columns
        ):

            def limpiar_nombre(texto):
                if pd.isna(texto):
                    return ""
                limpio = re.sub(r"\s*\(.*?\)", "", str(texto))
                return limpio.strip().upper()

            df_diario["Producto_Limpio"] = df_diario[
                "Descripción Producto"
            ].apply(limpiar_nombre)
            df_unificado = (
                df_diario.groupby("Producto_Limpio")["Venta Informada"]
                .sum()
                .reset_index()
            )

            datos_fila = {
                "_orden": num_dia,
                "Día": str(nombre_archivo).zfill(2)
                if num_dia != 999
                else nombre_archivo,
            }

            for _, row in df_unificado.iterrows():
                datos_fila[row["Producto_Limpio"]] = round(
                    row["Venta Informada"]
                )

            datos_acumulados.append(datos_fila)

    if datos_acumulados:
        df_final = pd.DataFrame(datos_acumulados)
        df_final = df_final.sort_values(by="_orden").reset_index(drop=True)
        df_final = df_final.drop(columns=["_orden"])
        df_final = df_final.fillna(0)
        return df_final
    return pd.DataFrame()


def procesar_archivos_turnos(archivos):
    lista_turnos = []
    traduccion_dias = {
        "MON": "LUN",
        "TUE": "MAR",
        "WED": "MIÉ",
        "THU": "JUE",
        "FRI": "VIE",
        "SAT": "SÁB",
        "SUN": "DOM",
        "MONDAY": "LUN",
        "TUESDAY": "MAR",
        "WEDNESDAY": "MIÉ",
        "THURSDAY": "JUE",
        "FRIDAY": "VIE",
        "SATURDAY": "SÁB",
        "SUNDAY": "DOM",
    }

    for archivo in archivos:
        nombre_archivo = os.path.splitext(archivo.name)[0]
        try:
            df_t = pd.read_excel(archivo, header=None)
            for index, row in df_t.iterrows():
                texto_fila = ""
                for col_idx in range(len(row)):
                    val = str(row.iloc[col_idx])
                    if (
                        any(dia in val.upper() for dia in traduccion_dias.keys())
                        and "(" in val
                    ):
                        texto_fila = val
                        break

                if not texto_fila:
                    texto_fila = nombre_archivo

                patron = r"([A-Za-z]+)\s*(\d{2}/\d{2}/\d{4})\s*\((\d)\)"
                match = re.search(patron, texto_fila)

                if match:
                    dia_ing = match.group(1).upper()
                    fecha = match.group(2)
                    num_turno = match.group(3)
                    dia_esp = traduccion_dias.get(dia_ing, dia_ing)

                    if num_turno == "1":
                        sigla_turno = "Turno Noche"
                    elif num_turno == "2":
                        sigla_turno = "Turno Mañana"
                    elif num_turno == "3":
                        sigla_turno = "Turno Tarde"
                    else:
                        sigla_turno = "Turno Noche"

                    info_dia_encontrada = f"{dia_esp} {fecha} ({num_turno})"
                    match_fecha = re.search(r"(\d{2})/(\d{2})/(\d{4})", fecha)
                    if match_fecha:
                        dd, mm, aaaa = match_fecha.groups()
                        clave_orden_mes_dia = f"{mm}-{dd}"
                        dia_mes_simple = f"{dd}/{mm}"
                    else:
                        clave_orden_mes_dia = fecha
                        dia_mes_simple = fecha

                    def safe_val(idx, default=0):
                        if len(row) > idx:
                            v = row.iloc[idx]
                            return round(v) if pd.notna(v) else default
                        return default

                    fila_dict = {
                        "_clave_mes_dia": clave_orden_mes_dia,
                        "Fecha / Día": dia_mes_simple,
                        "Fecha Apertura Completa": info_dia_encontrada,
                        "TOTALES": safe_val(5),
                        "NAFTA SUPER": safe_val(1),
                        "DIESEL 500": safe_val(2),
                        "INFINIA NAFTA": safe_val(3),
                        "INFINIA DIESEL": safe_val(4),
                        "Turno": sigla_turno,
                    }
                    lista_turnos.append(pd.DataFrame([fila_dict]))
        except Exception as e:
            st.warning(f"Aviso en archivo {archivo.name}: {e}")

    if lista_turnos:
        return pd.concat(lista_turnos, ignore_index=True)
    return pd.DataFrame()


if menu_principal == "Ventas 2026":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Selección de Mes")
    mes_seleccionado = st.sidebar.selectbox(
        "Mes de Trabajo", meses_lista, key="mes_ventas_playa"
    )

    st.sidebar.markdown("---")
    st.sidebar.header(f"📥 Carga - Playa Detallada 2026 ({mes_seleccionado})")
    archivos_playa_26 = st.sidebar.file_uploader(
        f"Sube archivos Excel Detallados 2026 - {mes_seleccionado}",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        key=f"uploader_playa_26_{mes_seleccionado}",
    )

    st.sidebar.markdown("---")
    st.sidebar.header(f"📥 Carga - Playa 2025 ({mes_seleccionado})")
    archivos_playa_25 = st.sidebar.file_uploader(
        f"Sube archivos Excel Playa 2025 - {mes_seleccionado}",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        key=f"uploader_playa_25_{mes_seleccionado}",
    )

    if archivos_playa_26:
        df_detalle_26 = procesar_archivos_playa_detalle(archivos_playa_26)
        if not df_detalle_26.empty:
            st.session_state.datos_2026[mes_seleccionado] = df_detalle_26

    if archivos_playa_25:
        df_proc_25 = procesar_archivos_playa(archivos_playa_25)
        if not df_proc_25.empty:
            st.session_state.datos_2025[mes_seleccionado] = df_proc_25

    df_2026_detalle = st.session_state.datos_2026.get(
        mes_seleccionado, pd.DataFrame()
    )
    df_2025 = st.session_state.datos_2025.get(mes_seleccionado, pd.DataFrame())

    if not df_2026_detalle.empty:
        st.subheader(f"📋 Detalle de Transacciones - {mes_seleccionado} 2026")

        total_litros_26 = df_2026_detalle["Volumen"].sum()
        total_despachos_26 = len(df_2026_detalle)

        col_m1, col_m2 = st.columns(2)
        col_m1.metric(
            "Litros Vendidos Totales", fmt_litros(total_litros_26)
        )
        col_m2.metric(
            "Cantidad de Despachos", fmt_entero(total_despachos_26)
        )

        st.markdown("---")
        st.subheader("⛽ Análisis de Mix de Productos")

        df_2026_detalle["Producto_Upper"] = (
            df_2026_detalle["Producto"].astype(str).str.strip().str.upper()
        )

        df_mix_agrupado = (
            df_2026_detalle.groupby("Producto_Upper")
            .agg(
                Litros=("Volumen", "sum"),
                Despachos=("Volumen", "count"),
            )
            .reset_index()
        )

        st.dataframe(
            df_mix_agrupado.style.format({
                "Litros": fmt_litros,
                "Despachos": fmt_entero,
            }),
            use_container_width=True,
        )

        col_mix1, col_mix2 = st.columns(2)

        with col_mix1:
            st.markdown("##### 🟢 Mix Naftas: Súper (NS XXI) vs Infinia")
            mask_naftas = df_2026_detalle["Producto_Upper"].str.contains(
                "NS XXI|SUPER|INFINIA", regex=True
            )
            df_naftas = df_2026_detalle[mask_naftas]

            def categorizar_nafta(prod):
                if "NS XXI" in prod or "SUPER" in prod:
                    return "Nafta Súper (NS XXI)"
                elif "INFINIA" in prod and "DIESEL" not in prod:
                    return "Nafta Infinia"
                return None

            df_naftas["Categoria_Mix"] = df_naftas["Producto_Upper"].apply(
                categorizar_nafta
            )
            resumen_naftas = (
                df_naftas.groupby("Categoria_Mix")["Volumen"].sum().reset_index()
            )

            if not resumen_naftas.empty:
                total_naftas = resumen_naftas["Volumen"].sum()
                resumen_naftas["Participación (%)"] = (
                    resumen_naftas["Volumen"] / total_naftas * 100
                ).fillna(0)
                st.dataframe(
                    resumen_naftas.style.format({
                        "Volumen": fmt_litros,
                        "Participación (%)": fmt_porcentaje,
                    }),
                    use_container_width=True,
                )
            else:
                st.info(
                    "No se encontraron registros de naftas con las etiquetas"
                    " esperadas."
                )

        with col_mix2:
            st.markdown("##### 🛢️ Mix Gasoil: Diesel 500 vs Infinia Diesel")
            mask_gasoil = df_2026_detalle["Producto_Upper"].str.contains(
                "DIESEL|500", regex=True
            )
            df_gasoil = df_2026_detalle[mask_gasoil]

            def categorizar_gasoil(prod):
                if (
                    "DIESEL 500" in prod
                    or "D. DIESEL 500" in prod
                    or "500" in prod
                ):
                    return "Diesel 500"
                elif "INFINIA DIESEL" in prod or "GO-INFINIA" in prod:
                    return "Infinia Diesel"
                return None

            df_gasoil["Categoria_Mix"] = df_gasoil["Producto_Upper"].apply(
                categorizar_gasoil
            )
            resumen_gasoil = (
                df_gasoil.groupby("Categoria_Mix")["Volumen"].sum().reset_index()
            )

            if not resumen_gasoil.empty:
                total_gasoil = resumen_gasoil["Volumen"].sum()
                resumen_gasoil["Participación (%)"] = (
                    resumen_gasoil["Volumen"] / total_gasoil * 100
                ).fillna(0)
                st.dataframe(
                    resumen_gasoil.style.format({
                        "Volumen": fmt_litros,
                        "Participación (%)": fmt_porcentaje,
                    }),
                    use_container_width=True,
                )
            else:
                st.info(
                    "No se encontraron registros de gasoil con las etiquetas"
                    " esperadas."
                )

        with st.expander("🔍 Ver transacciones detalladas completas"):
            df_detalle_display = df_2026_detalle.copy()
            df_detalle_display.index = df_detalle_display.index + 1
            st.dataframe(df_detalle_display, use_container_width=True)

        output_detalles = io.BytesIO()
        with pd.ExcelWriter(output_detalles, engine="openpyxl") as writer:
            df_2026_detalle.to_excel(
                writer,
                sheet_name=f"Detalle Ventas {mes_seleccionado}",
                index=False,
            )
            df_mix_agrupado.to_excel(
                writer, sheet_name="Resumen por Producto", index=False
            )

        st.markdown("---")
        st.download_button(
            label=f"Descargar Reporte Detallado y Mix ({mes_seleccionado}) en Excel (.xlsx)",
            data=output_detalles.getvalue(),
            file_name=f"reporte_detallado_ventas_{mes_seleccionado}_2026.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info(
            f"👈 Sube tus archivos Excel detallados de Ventas 2026 para **{mes_seleccionado}**."
        )

elif menu_principal == "🌙 Turnos por Día":
    pass
elif menu_principal == "🛒 Tienda Full":
    pass
elif menu_principal == "📦 BOXES":
    pass
