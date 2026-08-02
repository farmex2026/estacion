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

URL_NUBE = "https://script.google.com/macros/s/AKfycbxUWd3i5utU7OeQcT462lTRi91aPRLBAH9E6lulLuV2W1FPn68wMaMfkS8RjdTnXPUd/exec"

st.sidebar.header("☁️ Nube Automática")
st.sidebar.success("✅ Google Sheets Sincronizado")

if "datos_2025" not in st.session_state:
    st.session_state.datos_2025 = {}
if "datos_2026" not in st.session_state:
    st.session_state.datos_2026 = {}
if "turnos_2025" not in st.session_state:
    st.session_state.turnos_2025 = {}
if "turnos_2026" not in st.session_state:
    st.session_state.turnos_2026 = {}
if "full_2026" not in st.session_state:
    st.session_state.full_2026 = {}
if "boxes_2026" not in st.session_state:
    st.session_state.boxes_2026 = {}

menu_principal = st.sidebar.selectbox(
    "📂 Menú Principal",
    [
        "📊 Ventas (2025 vs 2026)",
        "🌙 Ventas por Turnos",
        "🛒 Tienda Full",
        "📦 BOXES",
    ],
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


def limpiar_numerico(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s.lower() == "nan":
        return 0.0
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return 0.0


def limpiar_serie_numerica(serie):
    return serie.apply(limpiar_numerico)


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
                df_detalles["Monto"] = limpiar_serie_numerica(
                    df_raw.iloc[7:, 6]
                )
                
                vol_bruto = limpiar_serie_numerica(df_raw.iloc[7:, 7])
                df_detalles["Volumen"] = vol_bruto / 1000.0

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


def procesar_archivos_turnos(archivos):
    lista_dfs = []
    for archivo in archivos:
        try:
            df = pd.read_excel(archivo)
            for col in df.columns:
                c_low = str(col).lower()
                if any(
                    k in c_low
                    for k in [
                        "volumen",
                        "litro",
                        "monto",
                        "total",
                        "precio",
                        "cantidad",
                        "pesos",
                        "importe",
                    ]
                ):
                    df[col] = limpiar_serie_numerica(df[col])
            lista_dfs.append(df)
        except Exception as e:
            st.warning(f"Aviso al procesar {archivo.name}: {e}")
    if lista_dfs:
        df_concatenado = pd.concat(lista_dfs, ignore_index=True)
        return df_concatenado.drop_duplicates().reset_index(drop=True)
    return pd.DataFrame()


def procesar_df_turnos_para_comparativa(df):
    if df.empty:
        return pd.DataFrame(columns=["Turno", "Litros", "Monto"])
    cols_lower = [str(c).lower() for c in df.columns]
    
    col_t = next((df.columns[i] for i, c in enumerate(cols_lower) if any(k in c for k in ["turno", "nro", "shift", "caja"])), df.columns[0])
    col_v = next((df.columns[i] for i, c in enumerate(cols_lower) if any(k in c for k in ["volumen", "litro", "cantidad"])), None)
    col_m = next((df.columns[i] for i, c in enumerate(cols_lower) if any(k in c for k in ["monto", "total", "pesos", "importe"])), None)
    
    if not col_v:
        num_cols = [c for c in df.columns if c != col_t and pd.api.types.is_numeric_dtype(df[c])]
        col_v = num_cols[0] if num_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0]

    temp = pd.DataFrame()
    temp["Turno"] = df[col_t].astype(str).str.strip().str.upper()
    temp["Litros"] = limpiar_serie_numerica(df[col_v]) if col_v in df.columns else 0.0
    if col_m and col_m in df.columns:
        temp["Monto"] = limpiar_serie_numerica(df[col_m])
    else:
        temp["Monto"] = 0.0
        
    agrupado = temp.groupby("Turno").agg({"Litros": "sum", "Monto": "sum"}).reset_index()
    return agrupado


def cargar_desde_nube(sheet_name):
    try:
        resp = requests.get(URL_NUBE, params={"month": sheet_name}, timeout=60)

        if resp.status_code != 200:
            return pd.DataFrame()

        try:
            data = resp.json()
        except Exception:
            return pd.DataFrame()

        if isinstance(data, dict) and "error" in data:
            return pd.DataFrame()

        if data and len(data) > 1:
            headers = data[0]
            rows = data[1:]
            df = pd.DataFrame(rows, columns=headers)
            for col in df.columns:
                c_low = str(col).lower()
                if any(
                    k in c_low
                    for k in [
                        "volumen",
                        "litro",
                        "monto",
                        "total",
                        "precio",
                        "cantidad",
                        "pesos",
                        "importe",
                    ]
                ):
                    df[col] = limpiar_serie_numerica(df[col])
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

    if st.sidebar.button("🔄 Recargar datos desde la Nube"):
        st.session_state.datos_2025.pop(mes_seleccionado, None)
        st.session_state.datos_2026.pop(mes_seleccionado, None)
        st.rerun()

    sheet_25 = f"{mes_seleccionado} 2025"
    sheet_26 = f"{mes_seleccionado} 2026"

    if (
        mes_seleccionado not in st.session_state.datos_2025
        or st.session_state.datos_2025[mes_seleccionado].empty
    ):
        df_nube_25 = cargar_desde_nube(sheet_25)
        if not df_nube_25.empty:
            st.session_state.datos_2025[mes_seleccionado] = df_nube_25

    if (
        mes_seleccionado not in st.session_state.datos_2026
        or st.session_state.datos_2026[mes_seleccionado].empty
    ):
        df_nube_26 = cargar_desde_nube(sheet_26)
        if not df_nube_26.empty:
            st.session_state.datos_2026[mes_seleccionado] = df_nube_26

    with st.sidebar.expander("🔐 Panel de Administración (Subir Excel)"):
        st.markdown("1 - Informe Vox")
        anio_upload = st.selectbox("Año del Archivo", [2026, 2025], index=0)
        archivos_playa = st.file_uploader(
            mes_seleccionado,
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
                    sheet_name_target = sheet_25
                else:
                    st.session_state.datos_2026[mes_seleccionado] = (
                        df_detalle_procesado
                    )
                    sheet_name_target = sheet_26

                try:
                    df_detalle_nube = df_detalle_procesado.fillna("").astype(str)
                    payload = {
                        "month": sheet_name_target,
                        "headers": df_detalle_nube.columns.tolist(),
                        "rows": df_detalle_nube.values.tolist(),
                    }
                    requests.post(URL_NUBE, json=payload, timeout=60)
                    st.success(
                        f"¡Subido y guardado en la nube ({sheet_name_target}) con"
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

        if litros_25 > litros_26:
            st.info(
                f"💡 **Lectura de ventas ({mes_seleccionado}):** Se vendió"
                f" **más en 2025** ({fmt_litros(litros_25)}) que en **2026**"
                f" ({fmt_litros(litros_26)}). La variación es de"
                f" **{pct_litros:+.2f}%**."
            )
        elif litros_26 > litros_25:
            st.success(
                f"💡 **Lectura de ventas ({mes_seleccionado}):** Se vendió"
                f" **más en 2026** ({fmt_litros(litros_26)}) que en **2025**"
                f" ({fmt_litros(litros_25)}). La variación es de"
                f" **{pct_litros:+.2f}%**."
            )

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(
                label="⛽ Total Litros Vendidos (2026)",
                value=fmt_litros(litros_26),
                delta=f"{pct_litros:+.2f}% respecto a 2025 ({fmt_litros(litros_25)})",
            )
        with col_m2:
            st.metric(
                label="🧾 Total de Despachos (2026)",
                value=fmt_entero(desp_26),
                delta=f"{pct_desp:+.2f}% respecto a 2025 ({fmt_entero(desp_25)})",
            )

        st.markdown("---")
        st.subheader("⛽ Versus de Combustibles (2025 vs 2026)")

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

        if not mix_25.empty or not mix_26.empty:
            df_mix_vs = pd.merge(
                mix_25, mix_26, on="Producto_Upper", how="outer"
            ).fillna(0)

            total_litros_25_mix = df_mix_vs["Litros_25"].sum()
            total_litros_26_mix = df_mix_vs["Litros_26"].sum()

            df_mix_vs["Mix_25"] = df_mix_vs.apply(
                lambda row: (row["Litros_25"] / total_litros_25_mix * 100)
                if total_litros_25_mix > 0
                else 0.0,
                axis=1,
            )
            df_mix_vs["Mix_26"] = df_mix_vs.apply(
                lambda row: (row["Litros_26"] / total_litros_26_mix * 100)
                if total_litros_26_mix > 0
                else 0.0,
                axis=1,
            )

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
                "Mix 2025": df_mix_vs["Mix_25"],
                "Mix 2026": df_mix_vs["Mix_26"],
                "Despachos 2025": df_mix_vs["Despachos_25"],
                "Despachos 2026": df_mix_vs["Despachos_26"],
            })

            st.dataframe(
                df_tabla_final.style.format({
                    "Litros 2025": fmt_litros,
                    "Litros 2026": fmt_litros,
                    "Variación (%)": lambda x: f"{x:+.2f}%",
                    "Mix 2025": lambda x: f"{x:.2f}%",
                    "Mix 2026": lambda x: f"{x:.2f}%",
                    "Despachos 2025": fmt_entero,
                    "Despachos 2026": fmt_entero,
                }),
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("🔍 Ver transacciones detalladas completas 2026"):
            if not df_26.empty:
                st.dataframe(df_26, use_container_width=True, hide_index=True)
            else:
                st.warning("No hay transacciones de 2026 para mostrar.")

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
# MENÚ 2: VENTAS POR TURNOS (2025 vs 2026)
# ==========================================
elif menu_principal == "🌙 Ventas por Turnos":
    st.subheader("🌙 Control de Ventas por Turnos (2025 vs 2026)")

    st.sidebar.markdown("---")
    st.sidebar.header("📂 Seleccionar Mes (Turnos)")
    mes_turno = st.sidebar.selectbox(
        "Mes de Turnos", meses_lista, key="mes_turno_trabajo"
    )

    if st.sidebar.button("🔄 Recargar Turnos desde la Nube"):
        st.session_state.turnos_2025.pop(mes_turno, None)
        st.session_state.turnos_2026.pop(mes_turno, None)
        st.rerun()

    # Nombres de solapa sin espacios personalizados (ej: turnojulio2025)
    sheet_t_25 = f"turno{mes_turno.lower()}2025"
    sheet_t_26 = f"turno{mes_turno.lower()}2026"

    if (
        mes_turno not in st.session_state.turnos_2025
        or st.session_state.turnos_2025[mes_turno].empty
    ):
        df_nube_t25 = cargar_desde_nube(sheet_t_25)
        if not df_nube_t25.empty:
            st.session_state.turnos_2025[mes_turno] = df_nube_t25

    if (
        mes_turno not in st.session_state.turnos_2026
        or st.session_state.turnos_2026[mes_turno].empty
    ):
        df_nube_t26 = cargar_desde_nube(sheet_t_26)
        if not df_nube_t26.empty:
            st.session_state.turnos_2026[mes_turno] = df_nube_t26

    with st.sidebar.expander("🔐 Panel Admin (Subir Excel Turnos)"):
        anio_upload_t = st.selectbox("Año del Archivo de Turnos", [2026, 2025], index=0, key="anio_turnos_up")
        archivos_turnos = st.file_uploader(
            f"Subir Excel Turnos - {mes_turno}",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            key=f"uploader_turnos_{anio_upload_t}_{mes_turno}",
        )

        if archivos_turnos:
            df_turnos_proc = procesar_archivos_turnos(archivos_turnos)
            if not df_turnos_proc.empty:
                if anio_upload_t == 2025:
                    st.session_state.turnos_2025[mes_turno] = df_turnos_proc
                    sheet_target_t = sheet_t_25
                else:
                    st.session_state.turnos_2026[mes_turno] = df_turnos_proc
                    sheet_target_t = sheet_t_26

                try:
                    df_para_nube = df_turnos_proc.fillna("").astype(str)
                    payload = {
                        "month": sheet_target_t,
                        "headers": df_para_nube.columns.tolist(),
                        "rows": df_para_nube.values.tolist(),
                    }
                    requests.post(URL_NUBE, json=payload, timeout=60)
                    st.success(
                        f"¡Turnos subidos y guardados en ({sheet_target_t})!"
                    )
                except Exception as e:
                    st.error(f"Error al guardar turnos: {e}")

    df_t_25 = st.session_state.turnos_2025.get(mes_turno, pd.DataFrame())
    df_t_26 = st.session_state.turnos_2026.get(mes_turno, pd.DataFrame())

    res_t_25 = procesar_df_turnos_para_comparativa(df_t_25) if not df_t_25.empty else pd.DataFrame(columns=["Turno", "Litros", "Monto"])
    res_t_26 = procesar_df_turnos_para_comparativa(df_t_26) if not df_t_26.empty else pd.DataFrame(columns=["Turno", "Litros", "Monto"])

    if not res_t_25.empty or not res_t_26.empty:
        st.markdown(f"### 📋 Comparativa de Ventas por Turnos - {mes_turno} (2025 vs 2026)")

        df_turnos_vs = pd.merge(res_t_25, res_t_26, on="Turno", how="outer", suffixes=("_25", "_26")).fillna(0)

        tot_litros_25 = df_turnos_vs["Litros_25"].sum()
        tot_litros_26 = df_turnos_vs["Litros_26"].sum()
        diff_t_litros = tot_litros_26 - tot_litros_25
        pct_t_litros = (diff_t_litros / tot_litros_25 * 100) if tot_litros_25 > 0 else 0.0

        if tot_litros_25 > tot_litros_26:
            st.info(
                f"💡 **Lectura de turnos ({mes_turno}):** Se vendió"
                f" **más en 2025** ({fmt_litros(tot_litros_25)}) que en **2026**"
                f" ({fmt_litros(tot_litros_26)}). La variación es de"
                f" **{pct_t_litros:+.2f}%**."
            )
        elif tot_litros_26 > tot_litros_25:
            st.success(
                f"💡 **Lectura de turnos ({mes_turno}):** Se vendió"
                f" **más en 2026** ({fmt_litros(tot_litros_26)}) que en **2025**"
                f" ({fmt_litros(tot_litros_25)}). La variación es de"
                f" **{pct_t_litros:+.2f}%**."
            )

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.metric(
                label="⛽ Total Litros Turnos (2026)",
                value=fmt_litros(tot_litros_26),
                delta=f"{pct_t_litros:+.2f}% respecto a 2025 ({fmt_litros(tot_litros_25)})",
            )
        with col_t2:
            tot_monto_26 = df_turnos_vs["Monto_26"].sum()
            tot_monto_25 = df_turnos_vs["Monto_25"].sum()
            diff_monto = tot_monto_26 - tot_monto_25
            pct_monto = (diff_monto / tot_monto_25 * 100) if tot_monto_25 > 0 else 0.0
            st.metric(
                label="💰 Total Monto Turnos (2026)",
                value=f"${fmt_entero(tot_monto_26)}",
                delta=f"{pct_monto:+.2f}% respecto a 2025",
            )

        st.markdown("---")

        df_turnos_vs["Mix_25"] = df_turnos_vs.apply(lambda r: (r["Litros_25"] / tot_litros_25 * 100) if tot_litros_25 > 0 else 0.0, axis=1)
        df_turnos_vs["Mix_26"] = df_turnos_vs.apply(lambda r: (r["Litros_26"] / tot_litros_26 * 100) if tot_litros_26 > 0 else 0.0, axis=1)
        df_turnos_vs["Variación (%)"] = df_turnos_vs.apply(lambda r: ((r["Litros_26"] - r["Litros_25"]) / r["Litros_25'] * 100) if r["Litros_25"] > 0 else 0.0, axis=1)

        df_tabla_turnos_final = pd.DataFrame({
            "Turno": df_turnos_vs["Turno"],
            "Litros 2025": df_turnos_vs["Litros_25"],
            "Litros 2026": df_turnos_vs["Litros_26"],
            "Variación (%)": df_turnos_vs["Variación (%)"],
            "Mix 2025": df_turnos_vs["Mix_25"],
            "Mix 2026": df_turnos_vs["Mix_26"],
        })

        st.dataframe(
            df_tabla_turnos_final.style.format({
                "Litros 2025": fmt_litros,
                "Litros 2026": fmt_litros,
                "Variación (%)": lambda x: f"{x:+.2f}%",
                "Mix 2025": lambda x: f"{x:.2f}%",
                "Mix 2026": lambda x: f"{x:.2f}%",
            }),
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("🔍 Ver registros detallados de Turnos 2026"):
            if not df_t_26.empty:
                st.dataframe(df_t_26, use_container_width=True, hide_index=True)
            else:
                st.warning("No hay registros de turnos de 2026 para mostrar.")

        output_t = io.BytesIO()
        with pd.ExcelWriter(output_t, engine="openpyxl") as writer:
            if not df_t_26.empty:
                df_t_26.to_excel(writer, sheet_name="Turnos 2026", index=False)
            if not df_t_25.empty:
                df_t_25.to_excel(writer, sheet_name="Turnos 2025", index=False)

        st.markdown("---")
        st.download_button(
            label=f"📥 Descargar Reporte Comparativo de Turnos ({mes_turno})",
            data=output_t.getvalue(),
            file_name=f"comparativa_turnos_{mes_turno}_2025_2026.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info(
            f"No hay registros de ventas por turnos cargados ni para 2025 ni para 2026 en el mes de **{mes_turno}**."
        )


# ==========================================
# MENÚ 3: TIENDA FULL
# ==========================================
elif menu_principal == "🛒 Tienda Full":
    st.subheader("🛒 Gestión y Ventas - Tienda Full")
    df_f_activo = st.session_state.full_2026.get("general", pd.DataFrame())
    if not df_f_activo.empty:
        st.dataframe(df_f_activo, use_container_width=True, hide_index=True)
    else:
        st.info("No hay información de Tienda Full disponible.")


# ==========================================
# MENÚ 4: BOXES
# ==========================================
elif menu_principal == "📦 BOXES":
    st.subheader("📦 Control de Servicios - BOXES")
    df_b_activo = st.session_state.boxes_2026.get("general", pd.DataFrame())
    if not df_b_activo.empty:
        st.dataframe(df_b_activo, use_container_width=True, hide_index=True)
    else:
        st.info("No hay información de BOXES disponible.")

# ==========================================
# PIE DE PÁGINA DE LA BARRA LATERAL (CENTRADO)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.9em;'>"
    "Desarrollado por Lucas Sellecchia<br><b>Farmex SAIC</b>"
    "</div>",
    unsafe_allow_html=True,
)
