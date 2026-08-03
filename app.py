import io
import json
import os
import re
import urllib.parse
from bs4 import BeautifulSoup
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
if "full_2025" not in st.session_state:
    st.session_state.full_2025 = {}
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
            df = pd.read_excel(archivo, header=1)
            df.columns = [str(c).strip() for c in df.columns]
            lista_dfs.append(df)
        except Exception as e:
            try:
                df = pd.read_excel(archivo)
                lista_dfs.append(df)
            except Exception as e2:
                st.warning(f"Aviso al procesar {archivo.name}: {e2}")
    if lista_dfs:
        df_concatenado = pd.concat(lista_dfs, ignore_index=True)
        return df_concatenado.drop_duplicates().reset_index(drop=True)
    return pd.DataFrame()


def procesar_df_turnos_2026(df):
    if df.empty:
        return pd.DataFrame()
    cols = df.columns

    def buscar_columna(nombres_posibles):
        for col in cols:
            c_low = str(col).strip().lower()
            for nombre in nombres_posibles:
                if nombre in c_low:
                    return col
        return None

    col_fecha = buscar_columna(["fecha", "apertura"])
    col_super = buscar_columna(["súper", "super"])
    col_diesel = buscar_columna(["diesel 500", "d500", "diesel"])
    col_inf_nafta = buscar_columna(["infinia nafta", "inf. nafta"])
    col_inf_diesel = buscar_columna(["infinia diesel", "inf. diesel"])

    if not col_fecha and len(cols) > 0:
        col_fecha = cols[0]
    if not col_super and len(cols) > 1:
        col_super = cols[1]
    if not col_diesel and len(cols) > 2:
        col_diesel = cols[2]
    if not col_inf_nafta and len(cols) > 3:
        col_inf_nafta = cols[3]
    if not col_inf_diesel and len(cols) > 4:
        col_inf_diesel = cols[4]

    fechas_raw = (
        df[col_fecha]
        if col_fecha in df.columns
        else pd.Series([""] * len(df))
    )
    dias_map = {
        "Mon": "Lun",
        "Tue": "Mar",
        "Wed": "Mié",
        "Thu": "Jue",
        "Fri": "Vie",
        "Sat": "Sáb",
        "Sun": "Dom",
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miércoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sábado",
        "Sunday": "Domingo",
    }

    lista_fechas = []
    lista_turnos = []

    for val in fechas_raw:
        val_str = str(val).strip() if pd.notna(val) else ""
        if val_str.lower() in ["nan", "nat", "none"]:
            val_str = ""
        turno = "DESCONOCIDO"
        if "(1)" in val_str or val_str.endswith(" 1"):
            turno = "TURNO NOCHE"
        elif "(2)" in val_str or val_str.endswith(" 2"):
            turno = "TURNO MAÑANA"
        elif "(3)" in val_str or val_str.endswith(" 3"):
            turno = "TURNO TARDE"
        fecha_limpia = re.sub(r"\s*\([123]\)", "", val_str).strip()
        for eng, esp in dias_map.items():
            fecha_limpia = re.sub(
                r"\b" + eng + r"\b", esp, fecha_limpia, flags=re.IGNORECASE
            )
        lista_fechas.append(fecha_limpia)
        lista_turnos.append(turno)

    res = pd.DataFrame()
    res["Fecha"] = lista_fechas
    res["NAFTA SUPER"] = (
        limpiar_serie_numerica(df[col_super])
        if col_super and col_super in df.columns
        else 0.0
    )
    res["DIESEL 500"] = (
        limpiar_serie_numerica(df[col_diesel])
        if col_diesel and col_diesel in df.columns
        else 0.0
    )
    res["INFINIA NAFTA"] = (
        limpiar_serie_numerica(df[col_inf_nafta])
        if col_inf_nafta and col_inf_nafta in df.columns
        else 0.0
    )
    res["INFINIA DIESEL"] = (
        limpiar_serie_numerica(df[col_inf_diesel])
        if col_inf_diesel and col_inf_diesel in df.columns
        else 0.0
    )
    res["TOTAL"] = (
        res["NAFTA SUPER"]
        + res["DIESEL 500"]
        + res["INFINIA NAFTA"]
        + res["INFINIA DIESEL"]
    )
    res["Turno"] = lista_turnos

    if not res.empty:
        mask_basura = (
            res["Fecha"]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(["fecha apertura", "fecha", "apertura", "nan", ""])
        )
        res = res[~mask_basura].reset_index(drop=True)
    return res


def procesar_archivo_full_html(archivo):
    """Procesa los archivos HTML de Cierre de Caja de Tienda Full (solo cantidades)."""
    try:
        content = archivo.read()
        try:
            html_text = content.decode("windows-1252")
        except:
            html_text = content.decode("utf-8", errors="ignore")

        soup = BeautifulSoup(html_text, "html.parser")
        texto_plano = soup.get_text()
        lineas = [
            line.strip() for line in texto_plano.split("\n") if line.strip()
        ]

        cierre_nro = ""
        rubros_data = []
        capturando_rubros = False

        for i, linea in enumerate(lineas):
            if "CIERRE DE CAJA NRO:" in linea:
                cierre_nro = linea
            if "RUBRO                  CANTIDAD  IMPORTE" in linea:
                capturando_rubros = True
                continue
            if capturando_rubros:
                if (
                    "TOTAL PERCEPCIONES" in linea
                    or "----------------" in linea
                    or "TOTAL A RENDIR" in linea
                ):
                    capturando_rubros = False
                else:
                    match = re.match(
                        r"^([0-9\-]+)\s+(.+?)\s+([0-9\-\.,]+)\s+([0-9\-\.,]+)$",
                        linea,
                    )
                    if match:
                        cod, desc, cant, imp = match.groups()
                        rubros_data.append({
                            "Codigo": cod,
                            "Rubro": desc.strip(),
                            "Cantidad": limpiar_numerico(cant),
                        })

        fecha_str = archivo.name.replace(".htm", "").replace(".html", "")

        return {
            "archivo": archivo.name,
            "cierre": cierre_nro,
            "fecha": fecha_str,
            "rubros": rubros_data,
        }
    except Exception as e:
        st.error(f"Error al procesar archivo Full {archivo.name}: {e}")
        return None


def cargar_desd_nube(sheet_name):
    try:
        resp = requests.get(URL_NUBE, params={"month": sheet_name}, timeout=60)
        if resp.status_code != 200:
            return pd.DataFrame()
        data = resp.json()
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
                        "cantidad",
                        "super",
                        "diesel",
                        "infinia",
                        "total",
                    ]
                ):
                    df[col] = limpiar_serie_numerica(df[col])
            return df
    except Exception:
        pass
    return pd.DataFrame()


cargar_desde_nube = cargar_desd_nube


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

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(
                label="⛽ Total Litros Vendidos (2026)",
                value=fmt_litros(litros_26),
                delta=(
                    f"{pct_litros:+.2f}% respecto a 2025"
                    f" ({fmt_litros(litros_25)})"
                    if not df_25.empty
                    else "Sin datos 2025"
                ),
            )
        with col_m2:
            st.metric(
                label="🧾 Total de Despachos (2026)",
                value=fmt_entero(desp_26),
                delta=(
                    f"{pct_desp:+.2f}% respecto a 2025 ({fmt_entero(desp_25)})"
                    if not df_25.empty
                    else "Sin datos 2025"
                ),
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
    else:
        st.info(
            f"No hay registros cargados ni para 2025 ni para 2026 en el mes de"
            f" **{mes_seleccionado}**."
        )


# ==========================================
# MENÚ 2: VENTAS POR TURNOS (2025 vs 2026)
# ==========================================
elif menu_principal == "🌙 Ventas por Turnos":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Seleccionar Mes (Turnos)")
    mes_seleccionado_turno = st.sidebar.selectbox(
        "Mes de Turnos", meses_lista, key="mes_turno_trabajo"
    )

    if st.sidebar.button("🔄 Recargar Turnos desde la Nube"):
        st.session_state.turnos_2025.pop(mes_seleccionado_turno, None)
        st.session_state.turnos_2026.pop(mes_seleccionado_turno, None)
        st.rerun()

    sheet_t_25 = f"turno{mes_seleccionado_turno.lower()}2025"
    sheet_t_26 = f"turno{mes_seleccionado_turno.lower()}2026"

    if (
        mes_seleccionado_turno not in st.session_state.turnos_2025
        or st.session_state.turnos_2025[mes_seleccionado_turno].empty
    ):
        df_nube_t25 = cargar_desde_nube(sheet_t_25)
        if not df_nube_t25.empty:
            st.session_state.turnos_2025[mes_seleccionado_turno] = df_nube_t25

    if (
        mes_seleccionado_turno not in st.session_state.turnos_2026
        or st.session_state.turnos_2026[mes_seleccionado_turno].empty
    ):
        df_nube_t26 = cargar_desde_nube(sheet_t_26)
        if not df_nube_t26.empty:
            st.session_state.turnos_2026[mes_seleccionado_turno] = df_nube_t26

    with st.sidebar.expander("🔐 Panel Admin (Subir Excel Turnos)"):
        anio_upload_turno = st.selectbox(
            "Año del Archivo (Turnos)", [2026, 2025], index=0, key="anio_up_t"
        )
        archivos_turnos = st.file_uploader(
            f"Subir Excel Turnos {anio_upload_turno}",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            key=f"uploader_turnos_{anio_upload_turno}_{mes_seleccionado_turno}",
        )
        if archivos_turnos:
            df_t_raw = procesar_archivos_turnos(archivos_turnos)
            if not df_t_raw.empty:
                df_t_res = procesar_df_turnos_2026(df_t_raw)
                if not df_t_res.empty:
                    if anio_upload_turno == 2025:
                        st.session_state.turnos_2025[mes_seleccionado_turno] = (
                            df_t_res
                        )
                        sheet_target = sheet_t_25
                    else:
                        st.session_state.turnos_2026[mes_seleccionado_turno] = (
                            df_t_res
                        )
                        sheet_target = sheet_t_26
                    try:
                        df_para_nube = df_t_res.fillna("").astype(str)
                        payload = {
                            "month": sheet_target,
                            "headers": df_para_nube.columns.tolist(),
                            "rows": df_para_nube.values.tolist(),
                        }
                        requests.post(URL_NUBE, json=payload, timeout=60)
                        st.success(
                            f"¡Turnos {anio_upload_turno} sincronizados!"
                        )
                    except Exception as e:
                        st.error(f"Error al guardar turnos: {e}")

    df_t25_raw = st.session_state.turnos_2025.get(
        mes_seleccionado_turno, pd.DataFrame()
    )
    df_t26_raw = st.session_state.turnos_2026.get(
        mes_seleccionado_turno, pd.DataFrame()
    )
    df_t_25 = (
        df_t25_raw
        if ("Turno" in df_t25_raw.columns or df_t25_raw.empty)
        else procesar_df_turnos_2026(df_t25_raw)
    )
    df_t_26 = (
        df_t26_raw
        if ("Turno" in df_t26_raw.columns or df_t26_raw.empty)
        else procesar_df_turnos_2026(df_t26_raw)
    )

    st.subheader(
        f"🌙 Comparativa de Ventas por Turnos - {mes_seleccionado_turno} (2025"
        " vs 2026)"
    )

    if not df_t_25.empty or not df_t_26.empty:
        total_litros_t25 = df_t_25["TOTAL"].sum() if not df_t_25.empty else 0.0
        total_litros_t26 = df_t_26["TOTAL"].sum() if not df_t_26.empty else 0.0
        diff_litros_t = total_litros_t26 - total_litros_t25
        pct_litros_t = (
            (diff_litros_t / total_litros_t25 * 100)
            if total_litros_t25 > 0
            else 0.0
        )

        st.metric(
            label="⛽ Total Litros por Turnos (2026)",
            value=fmt_litros(total_litros_t26),
            delta=(
                f"{pct_litros_t:+.2f}% respecto a 2025"
                f" ({fmt_litros(total_litros_t25)})"
                if not df_t_25.empty
                else "Sin datos 2025"
            ),
        )

        st.markdown("---")
        st.subheader("📊 Versus de Ventas por Turno (2025 vs 2026)")
        resumen_t25 = (
            df_t_25.groupby("Turno")["TOTAL"].sum().reset_index()
            if not df_t_25.empty
            else pd.DataFrame(columns=["Turno", "TOTAL"])
        )
        resumen_t25.rename(columns={"TOTAL": "Litros 2025"}, inplace=True)
        resumen_t26 = (
            df_t_26.groupby("Turno")["TOTAL"].sum().reset_index()
            if not df_t_26.empty
            else pd.DataFrame(columns=["Turno", "TOTAL"])
        )
        resumen_t26.rename(columns={"TOTAL": "Litros 2026"}, inplace=True)

        resumen_turnos_vs = pd.merge(
            resumen_t25, resumen_t26, on="Turno", how="outer"
        ).fillna(0)
        resumen_turnos_vs["Variación (%)"] = resumen_turnos_vs.apply(
            lambda row: (
                (row["Litros 2026"] - row["Litros 2025"]) / row["Litros 2025"]
                * 100
            )
            if row["Litros 2025"] > 0
            else 0.0,
            axis=1,
        )

        st.dataframe(
            resumen_turnos_vs.style.format({
                "Litros 2025": fmt_litros,
                "Litros 2026": fmt_litros,
                "Variación (%)": lambda x: f"{x:+.2f}%",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            f"No hay registros de turnos cargados para {mes_seleccionado_turno}."
        )


# ==========================================
# MENÚ 3: TIENDA FULL (Con persistencia en la Nube)
# ==========================================
elif menu_principal == "🛒 Tienda Full":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Seleccionar Mes (Tienda Full)")
    mes_seleccionado_full = st.sidebar.selectbox(
        "Mes Tienda Full", meses_lista, key="mes_full_trabajo"
    )

    sheet_full_26 = f"full_{mes_seleccionado_full.lower()}_2026"

    if (
        mes_seleccionado_full not in st.session_state.full_2026
        or st.session_state.full_2026[mes_seleccionado_full].empty
    ):
        df_nube_full = cargar_desd_nube(sheet_full_26)
        if not df_nube_full.empty:
            if "rubros" in df_nube_full.columns:
                df_nube_full["rubros"] = df_nube_full["rubros"].apply(
                    lambda x: json.loads(x)
                    if isinstance(x, str) and x.startswith("[")
                    else []
                )
            st.session_state.full_2026[mes_seleccionado_full] = df_nube_full

    if st.sidebar.button("🔄 Recargar Tienda Full desde la Nube"):
        st.session_state.full_2026.pop(mes_seleccionado_full, None)
        df_nube_full = cargar_desd_nube(sheet_full_26)
        if not df_nube_full.empty:
            if "rubros" in df_nube_full.columns:
                df_nube_full["rubros"] = df_nube_full["rubros"].apply(
                    lambda x: json.loads(x)
                    if isinstance(x, str) and x.startswith("[")
                    else []
                )
            st.session_state.full_2026[mes_seleccionado_full] = df_nube_full
        st.rerun()

    with st.sidebar.expander("🔐 Panel Admin (Subir Cierres Full)"):
        archivos_full = st.file_uploader(
            f"Subir Planillas Full (2026)",
            type=["htm", "html"],
            accept_multiple_files=True,
            key=f"uploader_full_2026_{mes_seleccionado_full}",
        )

        if archivos_full:
            nuevos_registros = []
            for arq in archivos_full:
                if arq.name.endswith((".htm", ".html")):
                    res_html = procesar_archivo_full_html(arq)
                    if res_html:
                        nuevos_registros.append(res_html)

            if nuevos_registros:
                df_actual = st.session_state.full_2026.get(
                    mes_seleccionado_full, pd.DataFrame()
                )
                df_nuevos = pd.DataFrame(nuevos_registros)
                df_concatenado = (
                    pd.concat([df_actual, df_nuevos], ignore_index=True)
                    .drop_duplicates(subset=["archivo"])
                    .reset_index(drop=True)
                )
                st.session_state.full_2026[mes_seleccionado_full] = (
                    df_concatenado
                )

                try:
                    df_para_nube = df_concatenado.copy()
                    if "rubros" in df_para_nube.columns:
                        df_para_nube["rubros"] = df_para_nube["rubros"].apply(
                            lambda x: json.dumps(x)
                        )
                    df_para_nube = df_para_nube.fillna("").astype(str)
                    payload = {
                        "month": sheet_full_26,
                        "headers": df_para_nube.columns.tolist(),
                        "rows": df_para_nube.values.tolist(),
                    }
                    requests.post(URL_NUBE, json=payload, timeout=60)
                    st.success(
                        f"¡{len(nuevos_registros)} archivos de Tienda Full"
                        " procesados y guardados en la nube!"
                    )
                except Exception as e:
                    st.error(f"Error al guardar en la nube: {e}")

    df_f26 = st.session_state.full_2026.get(
        mes_seleccionado_full, pd.DataFrame()
    )

    st.subheader(
        f"🛒 Cantidades Vendidas Tienda Full - {mes_seleccionado_full} (2026)"
    )

    if not df_f26.empty:
        st.success(
            f"✅ Cierres de Tienda Full cargados: {len(df_f26)} archivos"
        )
        st.markdown("---")

        todos_rubros_26 = []
        for lst in df_f26.get("rubros", []):
            if isinstance(lst, list):
                todos_rubros_26.extend(lst)

        if todos_rubros_26:
            df_rubros_26 = pd.DataFrame(todos_rubros_26)
            df_rubros_sum = (
                df_rubros_26.groupby("Rubro")
                .agg({"Cantidad": "sum"})
                .reset_index()
            )

            st.subheader(
                "🍔 Resumen de Unidades: Comidas y Bebidas Calientes"
            )

            mask_comidas = (
                df_rubros_sum["Rubro"].str.upper().str.contains("COMIDA")
            )
            df_comidas_detalle = df_rubros_sum[mask_comidas]
            total_cant_comidas = (
                df_comidas_detalle["Cantidad"].sum()
                if not df_comidas_detalle.empty
                else 0.0
            )

            mask_bebidas_cal = (
                df_rubros_sum["Rubro"].str.upper().str.contains("CALIENTE")
                | df_rubros_sum["Rubro"].str.upper().str.contains("CAFE")
                | df_rubros_sum["Rubro"].str.upper().str.contains("TÉ")
                | df_rubros_sum["Rubro"].str.upper().str.contains("TE")
                | df_rubros_sum["Rubro"].str.upper().str.contains("CAFETERIA")
            )
            df_bebidas_cal_detalle = df_rubros_sum[mask_bebidas_cal]
            total_cant_bebidas_cal = (
                df_bebidas_cal_detalle["Cantidad"].sum()
                if not df_bebidas_cal_detalle.empty
                else 0.0
            )

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.metric(
                    label="🍲 Total Unidades Comidas (Comidas + Elaboradas)",
                    value=fmt_entero(total_cant_comidas),
                )
                if not df_comidas_detalle.empty:
                    st.dataframe(
                        df_comidas_detalle.style.format(
                            {"Cantidad": fmt_entero}
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
            with col_c2:
                st.metric(
                    label="☕ Total Unidades Bebidas Calientes",
                    value=fmt_entero(total_cant_bebidas_cal),
                )
                if not df_bebidas_cal_detalle.empty:
                    st.dataframe(
                        df_bebidas_cal_detalle.style.format(
                            {"Cantidad": fmt_entero}
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("Sin registros de Bebidas Calientes.")

            st.markdown("---")
            st.subheader("📋 Detalle Completo de Unidades por Rubro (2026)")
            st.dataframe(
                df_rubros_sum.style.format({"Cantidad": fmt_entero}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(
                "No hay datos de rubros detallados en los archivos HTML"
                " cargados."
            )

        st.markdown("---")
        st.subheader("📋 Listado de Cierres Diarios")
        df_mostrar_26 = df_f26[["archivo", "cierre"]].copy()
        df_mostrar_26.columns = ["Archivo", "Cierre Nro"]
        st.dataframe(
            df_mostrar_26, use_container_width=True, hide_index=True
        )
    else:
        st.info(
            f"No hay registros de Tienda Full cargados para el mes de"
            f" **{mes_seleccionado_full}** en 2026."
        )


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
# PIE DE PÁGINA
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.9em;'>"
    "Desarrollado por Lucas Sellecchia<br><b>Farmex SAIC</b>"
    "</div>",
    unsafe_allow_html=True,
)
