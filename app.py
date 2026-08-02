import io
import os
import re
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Gestión Integral de Estación", page_icon="⛽", layout="wide"
)

st.sidebar.markdown("---")
st.sidebar.markdown("🛠️ **Creado por Lucas-Farmex 2026**")

URL_NUBE = "https://script.google.com/macros/s/AKfycbxwiBHLjt-sIi74cHB8C9H3ibI-0HY4j_SJ4rmJx1hqiQqylgn3x8BYHmFUykU3KabU/exec"

st.sidebar.markdown("---")
st.sidebar.header("☁️ Nube Automática")
st.sidebar.success("✅ Google Sheets Sincronizado")

if "datos_2026" not in st.session_state:
    st.session_state.datos_2026 = {}
if "turnos_2026" not in st.session_state:
    st.session_state.turnos_2026 = {}
if "full_2026" not in st.session_state:
    st.session_state.full_2026 = {}
if "boxes_2026" not in st.session_state:
    st.session_state.boxes_2026 = {}

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
        return df_concatenado.drop_duplicates().reset_index(drop=True)
    return pd.DataFrame()


def procesar_generico(archivos):
    lista_dfs = []
    for archivo in archivos:
        try:
            df = pd.read_excel(archivo)
            lista_dfs.append(df)
        except Exception as e:
            st.warning(f"Error al leer {archivo.name}: {e}")
    if lista_dfs:
        return pd.concat(lista_dfs, ignore_index=True).drop_duplicates()
    return pd.DataFrame()


# ==========================================
# MENÚ 1: VENTAS 2026 (PLAYA)
# ==========================================
if menu_principal == "Ventas 2026":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Seleccionar Mes a Ver")
    mes_seleccionado = st.sidebar.selectbox(
        "Mes de Trabajo", meses_lista, key="mes_trabajo"
    )

    # DESCARGA AUTOMÁTICA DESDE GOOGLE SHEETS AL CAMBIAR DE MES
    try:
        resp = requests.get(f"{URL_NUBE}?month={mes_seleccionado}", timeout=5)
        data = resp.json()
        if data and len(data) > 1:
            headers = data[0]
            rows = data[1:]
            df_recuperado = pd.DataFrame(rows, columns=headers)

            if "Volumen" in df_recuperado.columns:
                df_recuperado["Volumen"] = pd.to_numeric(
                    df_recuperado["Volumen"], errors="coerce"
                ).fillna(0)
            if "Monto" in df_recuperado.columns:
                df_recuperado["Monto"] = pd.to_numeric(
                    df_recuperado["Monto"], errors="coerce"
                ).fillna(0)

            st.session_state.datos_2026[mes_seleccionado] = df_recuperado
    except Exception:
        pass

    # PANEL EXCLUSIVO PARA EL ADMINISTRADOR (OCULTO PARA EMPLEADOS)
    with st.sidebar.expander("🔐 Panel de Administración (Subir Excel)"):
        st.markdown(
            "*(Solo para cargar nuevos archivos a la nube del mes seleccionado)*"
        )
        archivos_playa_26 = st.file_uploader(
            f"Subir Excel - {mes_seleccionado}",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            key=f"uploader_playa_26_{mes_seleccionado}",
        )

        if archivos_playa_26:
            df_detalle_26 = procesar_archivos_playa_detalle(archivos_playa_26)
            if not df_detalle_26.empty:
                st.session_state.datos_2026[mes_seleccionado] = df_detalle_26
                try:
                    payload = {
                        "month": mes_seleccionado,
                        "headers": df_detalle_26.columns.tolist(),
                        "rows": df_detalle_26.astype(str).values.tolist(),
                    }
                    requests.post(URL_NUBE, json=payload, timeout=5)
                    st.success("¡Subido y guardado en la nube con éxito!")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

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
            df_display = df_2026_detalle.copy()
            df_display.index = df_display.index + 1
            st.dataframe(df_display, use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_2026_detalle.to_excel(
                writer, sheet_name="Detalle Ventas", index=False
            )
            df_mix_agrupado.to_excel(
                writer, sheet_name="Mix Productos", index=False
            )

        st.markdown("---")
        st.download_button(
            label=f"📥 Descargar Reporte Completo ({mes_seleccionado})",
            data=output.getvalue(),
            file_name=f"ventas_playa_{mes_seleccionado}_2026.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info(
            f"No hay registros cargados todavía para el mes de **{mes_seleccionado}**."
        )


# ==========================================
# MENÚ 2: TURNOS POR DÍA
# ==========================================
elif menu_principal == "🌙 Turnos por Día":
    st.subheader("🌙 Control de Turnos por Día")
    df_t_activo = st.session_state.turnos_2026.get("general", pd.DataFrame())
    if not df_t_activo.empty:
        st.dataframe(df_t_activo, use_container_width=True)
    else:
        st.info("No hay información de turnos disponible.")


# ==========================================
# MENÚ 3: TIENDA FULL
# ==========================================
elif menu_principal == "🛒 Tienda Full":
    st.subheader("🛒 Gestión y Ventas - Tienda Full")
    df_f_activo = st.session_state.full_2026.get("general", pd.DataFrame())
    if not df_f_activo.empty:
        st.dataframe(df_f_activo, use_container_width=True)
    else:
        st.info("No hay información de Tienda Full disponible.")


# ==========================================
# MENÚ 4: BOXES
# ==========================================
elif menu_principal == "📦 BOXES":
    st.subheader("📦 Control de Servicios - BOXES")
    df_b_activo = st.session_state.boxes_2026.get("general", pd.DataFrame())
    if not df_b_activo.empty:
        st.dataframe(df_b_activo, use_container_width=True)
    else:
        st.info("No hay información de BOXES disponible.")
