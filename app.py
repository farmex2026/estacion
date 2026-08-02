import io
import os
import re
import urllib.parse
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

if "datos_2025" not in st.session_state:
    st.session_state.datos_2025 = {}
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
    ["📊 Ventas (2025 vs 2026)", "🌙 Turnos por Día", "🛒 Tienda Full", "📦 BOXES"],
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


def cargar_desde_nube(mes, anio):
    sheet_name = f"{mes} {anio}"
    try:
        resp = requests.get(URL_NUBE, params={"month": sheet_name}, timeout=5)
        data = resp.json()
        if data and len(data) > 1:
            headers = data[0]
            rows = data[1:]
            df = pd.DataFrame(rows, columns=headers)
            if "Volumen" in df.columns:
                df["Volumen"] = pd.to_numeric(
                    df["Volumen"], errors="coerce"
                ).fillna(0)
            if "Monto" in df.columns:
                df["Monto"] = pd.to_numeric(
                    df["Monto"], errors="coerce"
                ).fillna(0)
            return df
    except Exception:
        pass
    return pd.DataFrame()


# ==========================================
# MENÚ 1: VENTAS (2025 vs 2026)
# ==========================================
if menu_principal == "📊 Ventas (2025 vs 2026)":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Seleccionar Mes a Ver")
    mes_seleccionado = st.sidebar.selectbox(
        "Mes de Trabajo", meses_lista, key="mes_trabajo"
    )

    # CORRECCIÓN CLAVE: Solo busca en la nube si todavía no tenemos datos guardados en memoria
    if (
        mes_seleccionado not in st.session_state.datos_2025
        or st.session_state.datos_2025[mes_seleccionado].empty
    ):
        df_nube_25 = cargar_desde_nube(mes_seleccionado, 2025)
        if not df_nube_25.empty:
            st.session_state.datos_2025[mes_seleccionado] = df_nube_25

    if (
        mes_seleccionado not in st.session_state.datos_2026
        or st.session_state.datos_2026[mes_seleccionado].empty
    ):
        df_nube_26 = cargar_desde_nube(mes_seleccionado, 2026)
        if not df_nube_26.empty:
            st.session_state.datos_2026[mes_seleccionado] = df_nube_26

    # PANEL ADMINISTRADOR
    with st.sidebar.expander("🔐 Panel de Administración (Subir Excel)"):
        anio_upload = st.selectbox("Año del Archivo", [2026, 2025], index=0)
        archivos_playa = st.file_uploader(
            f"Subir Excel - {mes_seleccionado} {anio_upload}",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            key=f"uploader_playa_{anio_upload}_{mes_seleccionado}",
        )

        if archivos_playa:
            df_detalle_procesado = procesar_archivos_playa_detalle(
                archivos_playa
            )
            if not df_detalle_procesado.empty:
                if anio_upload == 2025:
                    st.session_state.datos_2025[mes_seleccionado] = (
                        df_detalle_procesado
                    )
                else:
                    st.session_state.datos_2026[mes_seleccionado] = (
                        df_detalle_procesado
                    )

                try:
                    sheet_name = f"{mes_seleccionado} {anio_upload}"
                    payload = {
                        "month": sheet_name,
                        "headers": df_detalle_procesado.columns.tolist(),
                        "rows": df_detalle_procesado.astype(
                            str
                        ).values.tolist(),
                    }
                    requests.post(URL_NUBE, json=payload, timeout=5)
                    st.success(
                        f"¡Subido y guardado en la nube ({sheet_name}) con"
                        " éxito!"
                    )
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    df_25 = st.session_state.datos_2025.get(mes_seleccionado, pd.DataFrame())
    df_26 = st.session_state.datos_2026.get(mes_seleccionado, pd.DataFrame())

    if not df_25.empty or not df_26.empty:
        st.subheader(
            f"📈 Comparativa General - {mes_seleccionado} (2025 vs 2026)"
        )

        litros_25 = df_25["Volumen"].sum() if not df_25.empty else 0.0
        litros_26 = df_26["Volumen"].sum() if not df_26.empty else 0.0
        diff_litros = litros_26 - litros_25
        pct_litros = (
            (diff_litros / litros_25 * 100) if litros_25 > 0 else 0.0
        )

        desp_25 = len(df_25) if not df_25.empty else 0
        desp_26 = len(df_26) if not df_26.empty else 0
        diff_desp = desp_26 - desp_25
        pct_desp = ((diff_desp / desp_25 * 100) if desp_25 > 0 else 0.0)

        # MÉTRICAS GENERALES CLARAS
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(
                label="⛽ Total Litros Vendidos",
                value=f"2026: {fmt_litros(litros_26)}",
                delta=(
                    f"vs 2025 ({fmt_litros(litros_25)}) ->"
                    f" {pct_litros:+.2f}%"
                ),
            )
        with col_m2:
            st.metric(
                label="🧾 Total de Despachos",
                value=f"2026: {fmt_entero(desp_26)}",
                delta=f"vs 2025 ({fmt_entero(desp_25)}) -> {pct_desp:+.2f}%",
            )

        st.markdown("---")
        st.subheader("⛽ Versus de Combustibles (2025 vs 2026)")

        # Preparar mix de 2025
        if not df_25.empty:
            df_25["Producto_Upper"] = (
                df_25["Producto"].astype(str).str.strip().str.upper()
            )
            mix_25 = (
                df_25.groupby("Producto_Upper")
                .agg(
                    Litros_25=("Volumen", "sum"),
                    Despachos_25=("Volumen", "count"),
                )
                .reset_index()
            )
        else:
            mix_25 = pd.DataFrame(
                columns=["Producto_Upper", "Litros_25", "Despachos_25"]
            )

        # Preparar mix de 2026
        if not df_26.empty:
            df_26["Producto_Upper"] = (
                df_26["Producto"].astype(str).str.strip().str.upper()
            )
            mix_26 = (
                df_26.groupby("Producto_Upper")
                .agg(
                    Litros_26=("Volumen", "sum"),
                    Despachos_26=("Volumen", "count"),
                )
                .reset_index()
            )
        else:
            mix_26 = pd.DataFrame(
                columns=["Producto_Upper", "Litros_26", "Despachos_26"]
            )

        # Unir ambos años para hacer el versus por combustible
        if not mix_25.empty or not mix_26.empty:
            df_mix_vs = pd.merge(
                mix_25, mix_26, on="Producto_Upper", how="outer"
            ).fillna(0)
            df_mix_vs["Variación Litros (%)"] = df_mix_vs.apply(
                lambda row: (
                    (row["Litros_26"] - row["Litros_25"])
                    / row["Litros_25"]
                    * 100
                )
                if row["Litros_25"] > 0
                else 0.0,
                axis=1,
            )

            df_tabla_final = pd.DataFrame({
                "Combustible": df_mix_vs["Producto_Upper"],
                "Litros 2025": df_mix_vs["Litros_25"],
                "Litros 2026": df_mix_vs["Litros_26"],
                "Variación (%)": df_mix_vs["Variación Litros (%)"],
                "Despachos 2025": df_mix_vs["Despachos_25"],
                "Despachos 2026": df_mix_vs["Despachos_26"],
            })

            st.dataframe(
                df_tabla_final.style.format({
                    "Litros 2025": fmt_litros,
                    "Litros 2026": fmt_litros,
                    "Variación (%)": lambda x: f"{x:+.2f}%",
                    "Despachos 2025": fmt_entero,
                    "Despachos 2026": fmt_entero,
                }),
                use_container_width=True,
            )
        else:
            st.info(
                "No hay datos suficientes para generar el comparativo de"
                " combustibles."
            )

        with st.expander("🔍 Ver transacciones detalladas completas 2026"):
            if not df_26.empty:
                df_display = df_26.copy()
                df_display.index = df_display.index + 1
                st.dataframe(df_display, use_container_width=True)
            else:
                st.warning("No hay transacciones de 2026 para mostrar.")

        # Opción de descarga
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            if not df_26.empty:
                df_26.to_excel(
                    writer, sheet_name="Detalle 2026", index=False
                )
            if not df_25.empty:
                df_25.to_excel(
                    writer, sheet_name="Detalle 2025", index=False
                )

        st.markdown("---")
        st.download_button(
            label=f"📥 Descargar Reporte Comparativo ({mes_seleccionado})",
            data=output.getvalue(),
            file_name=f"comparativa_ventas_{mes_seleccionado}_2025_2026.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info(
            f"No hay registros cargados ni para 2025 ni para 2026 en el mes de"
            f" **{mes_seleccionado}**."
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
