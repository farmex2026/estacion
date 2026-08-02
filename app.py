import io
import os
import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestión Integral de Estación", page_icon="⛽", layout="wide"
)

st.sidebar.markdown("---")
st.sidebar.markdown("🛠️ **Creado por Lucas-Farmex 2026 (Online)**")

# Inicialización de Estados Globales estructurados por Mes
if "datos_2026" not in st.session_state:
    st.session_state.datos_2026 = {}
if "datos_2025" not in st.session_state:
    st.session_state.datos_2025 = {}
if "turnos_2026" not in st.session_state:
    st.session_state.turnos_2026 = {}
if "turnos_2025" not in st.session_state:
    st.session_state.turnos_2025 = {}

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
                df_detalles["Fecha y Hora"] = df_raw.iloc[7:, 0]
                df_detalles["Surtidor/Manguera"] = df_raw.iloc[7:, 1]
                df_detalles["Producto"] = df_raw.iloc[7:, 3]
                df_detalles["Monto"] = (
                    pd.to_numeric(df_raw.iloc[7:, 6], errors="coerce")
                    .fillna(0)
                )
                df_detalles["Volumen"] = (
                    pd.to_numeric(df_raw.iloc[7:, 7], errors="coerce")
                    .fillna(0)
                )

                df_detalles = df_detalles.dropna(
                    subset=["Producto", "Volumen"], how="all"
                )

                df_detalles["_fecha_dt"] = pd.to_datetime(
                    df_detalles["Fecha y Hora"], errors="coerce"
                )
                df_detalles = df_detalles.dropna(subset=["_fecha_dt"])
                df_detalles = df_detalles.drop(columns=["_fecha_dt"])

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


# ----------------------------------------------------
# SECCIÓN DE SINCRONIZACIÓN / BASE CONSOLIDADA (MULTI-PC)
# ----------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🌐 Sincronización Multi-PC")

archivo_maestro = st.sidebar.file_uploader(
    "🔄 Subir Base Consolidada (.xlsx)",
    type=["xlsx"],
    key="uploader_maestro",
)
if archivo_maestro:
    try:
        excel_file = pd.ExcelFile(archivo_maestro)
        for sheet_name in excel_file.sheet_names:
            df_sh = pd.read_excel(excel_file, sheet_name=sheet_name)
            if sheet_name.startswith("2026_"):
                mes_key = sheet_name.replace("2026_", "")
                if mes_key in meses_lista:
                    st.session_state.datos_2026[mes_key] = df_sh
        st.sidebar.success(
            "¡Base consolidada cargada con éxito en la nube!"
        )
    except Exception as e:
        st.sidebar.error(f"Error al leer el archivo maestro: {e}")

if st.sidebar.button("💾 Generar Respaldo Consolidado"):
    output_master = io.BytesIO()
    with pd.ExcelWriter(output_master, engine="openpyxl") as writer:
        for mes, df in st.session_state.datos_2026.items():
            if not df.empty:
                df.to_excel(writer, sheet_name=f"2026_{mes}", index=False)

    st.sidebar.download_button(
        label="📥 Descargar Archivo Maestro (.xlsx)",
        data=output_master.getvalue(),
        file_name="base_consolidada_estacion.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_descargar_maestro",
    )


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

    if archivos_playa_26:
        df_detalle_26 = procesar_archivos_playa_detalle(archivos_playa_26)
        if not df_detalle_26.empty:
            st.session_state.datos_2026[mes_seleccionado] = df_detalle_26

    df_2026_detalle = st.session_state.datos_2026.get(
        mes_seleccionado, pd.DataFrame()
    )

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

        with st.expander("🔍 Ver transacciones detalladas completas"):
            df_detalle_display = df_2026_detalle.copy()
            df_detalle_display.index = df_detalle_display.index + 1
            st.dataframe(df_detalle_display, use_container_width=True)
    else:
        st.info(
            f"👈 Sube tus archivos Excel detallados de Ventas 2026 para **{mes_seleccionado}** (o carga tu Base Consolidada arriba)."
        )

elif menu_principal == "🌙 Turnos por Día":
    pass
elif menu_principal == "🛒 Tienda Full":
    pass
elif menu_principal == "📦 BOXES":
    pass
