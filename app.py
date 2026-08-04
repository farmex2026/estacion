import streamlit as st
import pandas as pd
import requests
import json
from bs4 import BeautifulSoup
import io

# Configuración inicial de la página
st.set_page_config(page_title="Gestión Estación YPF (Modo Lectura Nube)", layout="wide")

# Inicialización de session_state para 2025 y 2026
for anio in [2025, 2026]:
    if f"full_{anio}" not in st.session_state:
        st.session_state[f"full_{anio}"] = {}
    if f"boxes_{anio}" not in st.session_state:
        st.session_state[f"boxes_{anio}"] = {}
    if f"combustibles_{anio}" not in st.session_state:
        st.session_state[f"combustibles_{anio}"] = {}

meses_lista = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# URL de Google Apps Script actualizada
URL_NUBE = "https://script.google.com/macros/s/AKfycbxKBg59r94ZC8hK4VmrmN3SWx6rg1lIvfcAiLf4KxFYzDcUut54KBPPvO9sRf6akwUQ/exec"

# Función para limpiar y evitar nombres de columnas duplicados (vital para Arrow/Streamlit)
def limpiar_columnas(df):
    if df.empty:
        return df
    cols_limpias = []
    conteo = {}
    for c in df.columns:
        c_str = str(c).strip()
        if not c_str or c_str.lower() == "nan" or c_str == "None":
            c_str = "Columna"
        if c_str in conteo:
            conteo[c_str] += 1
            cols_limpias.append(f"{c_str}_{conteo[c_str]}")
        else:
            conteo[c_str] = 0
            cols_limpias.append(c_str)
    df.columns = cols_limpias
    return df

# Función robusta con caché corto para lectura desde la nube
@st.cache_data(ttl=5, show_spinner="Sincronizando con la nube...")
def cargar_desde_nube(sheet_name):
    try:
        if URL_NUBE:
            res = requests.get(f"{URL_NUBE}?month={sheet_name}", timeout=15)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, dict):
                    rows = data.get("rows", data.get("data", []))
                    headers = data.get("headers", data.get("columns", []))
                    if rows and headers:
                        df = pd.DataFrame(rows, columns=headers)
                        return limpiar_columnas(df)
                    elif rows and not headers:
                        df = pd.DataFrame(rows)
                        return limpiar_columnas(df)
                elif isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data)
                    return limpiar_columnas(df)
    except Exception as e:
        st.warning(f"No se pudo conectar con la nube: {e}")
    return pd.DataFrame()

# Función para enviar datos a Google Sheets
def guardar_en_nube(sheet_name, df):
    try:
        if URL_NUBE and not df.empty:
            df_limpio = df.copy()
            df_limpio = df_limpio.astype(object).where(pd.notnull(df_limpio), "")
            
            for col in df_limpio.columns:
                df_limpio[col] = df_limpio[col].apply(lambda x: str(x) if x != "" else "")

            records = df_limpio.to_dict(orient="records")
            payload = {
                "sheet": sheet_name,
                "data": records
            }
            res = requests.post(URL_NUBE, json=payload, timeout=20)
            if res.status_code == 200:
                return True
    except Exception as e:
        st.error(f"Error al guardar en la nube: {e}")
    return False

# Lector robusto de tablas .HTM sin dependencias externas
def leer_tabla_htm_directo(archivo):
    try:
        contenido = archivo.getvalue().decode("utf-8", errors="ignore")
        soup = BeautifulSoup(contenido, "html.parser")
        tabla = soup.find("table")
        if not tabla:
            return pd.DataFrame()
        
        rows = []
        for tr in tabla.find_all("tr"):
            cols = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if cols:
                rows.append(cols)
        
        if not rows:
            return pd.DataFrame()
            
        max_len = max(len(r) for r in rows)
        rows_padded = [r + [""] * (max_len - len(r)) for r in rows]
        df = pd.DataFrame(rows_padded[1:], columns=rows_padded[0])
        return limpiar_columnas(df)
    except Exception as e:
        st.error(f"Error al procesar el archivo HTML: {e}")
        return pd.DataFrame()

# Formateador de números estilo argentino
def formato_arg(val, decimales=0):
    try:
        if decimales > 0:
            s = f"{val:,.{decimales}f}"
        else:
            s = f"{val:,.0f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(val)

# Menú principal en la barra lateral
menu_principal = st.sidebar.selectbox(
    "Menú Principal", 
    ["📊 DASHBOARD", "⛽ COMBUSTIBLES", "🛒 TIENDA FULL", "📦 BOXES", "🎯 +YPF"]
)

# ==========================================
# 1. DASHBOARD
# ==========================================
if menu_principal == "📊 DASHBOARD":
    st.title("📊 Dashboard General (Comparativa 2026 vs 2025)")
    st.info("Panel de control centralizado de la estación con comparativa interanual.")

# ==========================================
# 2. COMBUSTIBLES (INTACTO)
# ==========================================
elif menu_principal == "⛽ COMBUSTIBLES":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Seleccionar Mes y Año")
    mes_seleccionado_comb = st.sidebar.selectbox("Mes Combustibles", meses_lista)

    st.sidebar.markdown("---")
    st.sidebar.header("📥 Carga Manual de Archivo")
    anio_subida = st.sidebar.selectbox("Año destino del archivo", [2026, 2025], index=0)
    archivo_subido = st.sidebar.file_uploader(f"Subir Excel/CSV - {mes_seleccionado_comb} ({anio_subida})", type=["csv", "xlsx", "xls"], key=f"uploader_comb_{anio_subida}_{mes_seleccionado_comb}")
    
    sheet_comb_2026 = f"combustibles_{mes_seleccionado_comb.lower()}_2026"
    sheet_comb_2025 = f"combustibles_{mes_seleccionado_comb.lower()}_2025"
    sheet_activa = sheet_comb_2026 if anio_subida == 2026 else sheet_comb_2025

    if archivo_subido is not None:
        try:
            if archivo_subido.name.endswith('.csv'):
                df_subido = pd.read_csv(archivo_subido)
            else:
                df_subido = pd.read_excel(archivo_subido)
            
            df_subido = limpiar_columnas(df_subido)
            if not df_subido.empty:
                st.session_state[f"combustibles_{anio_subida}"][mes_seleccionado_comb] = df_subido
                st.sidebar.success(f"¡Archivo leído correctamente para {anio_subida}!")
                
                if st.sidebar.button("💾 Guardar permanentemente en la Nube", key=f"btn_guardar_{anio_subida}_{mes_seleccionado_comb}"):
                    with st.spinner("Guardando en Google Sheets..."):
                        exito = guardar_en_nube(sheet_activa, df_subido)
                        if exito:
                            st.sidebar.success("¡Guardado en la nube con éxito!")
                            st.cache_data.clear()
                        else:
                            st.sidebar.error("No se pudo guardar en la nube.")
        except Exception as e:
            st.sidebar.error(f"Error al leer el archivo: {e}")

    if mes_seleccionado_comb not in st.session_state["combustibles_2026"] or st.session_state["combustibles_2026"][mes_seleccionado_comb].empty:
        df_nube_2026 = cargar_desde_nube(sheet_comb_2026)
        if not df_nube_2026.empty:
            st.session_state["combustibles_2026"][mes_seleccionado_comb] = df_nube_2026

    if mes_seleccionado_comb not in st.session_state["combustibles_2025"] or st.session_state["combustibles_2025"][mes_seleccionado_comb].empty:
        df_nube_2025 = cargar_desde_nube(sheet_comb_2025)
        if not df_nube_2025.empty:
            st.session_state["combustibles_2025"][mes_seleccionado_comb] = df_nube_2025

    if st.sidebar.button("🔄 Actualizar Datos desde la Nube"):
        st.cache_data.clear()
        st.session_state["combustibles_2026"].pop(mes_seleccionado_comb, None)
        st.session_state["combustibles_2025"].pop(mes_seleccionado_comb, None)
        st.rerun()

    df_2026 = st.session_state["combustibles_2026"].get(mes_seleccionado_comb, pd.DataFrame())
    df_2025 = st.session_state["combustibles_2025"].get(mes_seleccionado_comb, pd.DataFrame())

    st.subheader(f"⛽ COMBUSTIBLES - {mes_seleccionado_comb} (2026 vs 2025)")

    vol_2026, desp_2026 = 0, 0
    if not df_2026.empty:
        if len(df_2026) > 0 and any("fecha" in str(v).lower() for v in df_2026.iloc[0].values):
            df_2026.columns = df_2026.iloc[0].astype(str).str.strip()
            df_2026 = df_2026.iloc[1:].reset_index(drop=True)
        df_2026 = limpiar_columnas(df_2026)
        c_vol_26 = "Volumen" if "Volumen" in df_2026.columns else df_2026.columns[3]
        df_2026[c_vol_26] = pd.to_numeric(df_2026[c_vol_26], errors='coerce').fillna(0)
        vol_2026 = df_2026[c_vol_26].sum()
        desp_2026 = len(df_2026)

    vol_2025, desp_2025 = 0, 0
    if not df_2025.empty:
        if len(df_2025) > 0 and any("fecha" in str(v).lower() for v in df_2025.iloc[0].values):
            df_2025.columns = df_2025.iloc[0].astype(str).str.strip()
            df_2025 = df_2025.iloc[1:].reset_index(drop=True)
        df_2025 = limpiar_columnas(df_2025)
        c_vol_25 = "Volumen" if "Volumen" in df_2025.columns else df_2025.columns[3]
        df_2025[c_vol_25] = pd.to_numeric(df_2025[c_vol_25], errors='coerce').fillna(0)
        vol_2025 = df_2025[c_vol_25].sum()
        desp_2025 = len(df_2025)

    col1, col2 = st.columns(2)
    with col1:
        diff_vol = ((vol_2026 - vol_2025) / vol_2025 * 100) if vol_2025 > 0 else 0
        st.metric("📦 Volumen Total (L) 2026", f"{formato_arg(vol_2026, 0)} L", delta=f"{diff_vol:+.2f}% vs 2025 ({formato_arg(vol_2025, 0)} L)")
    with col2:
        diff_desp = ((desp_2026 - desp_2025) / desp_2025 * 100) if desp_2025 > 0 else 0
        st.metric("🔢 Despachos 2026", formato_arg(desp_2026), delta=f"{diff_desp:+.2f}% vs 2025 ({formato_arg(desp_2025)})")

    st.markdown("---")

    def calcular_mix_datos(df):
        if df.empty:
            return 0, 0, 0, 0, 0, 0
        c_prod = "Producto" if "Producto" in df.columns else df.columns[2]
        c_vol = "Volumen" if "Volumen" in df.columns else df.columns[3]
        df_temp = df.copy()
        df_temp['prod_lower'] = df_temp[c_prod].astype(str).str.lower()
        
        vs = df_temp[df_temp['prod_lower'].str.contains('super|ns xxi', case=False, na=False)][c_vol].sum()
        vin = df_temp[df_temp['prod_lower'].str.contains('infinia', case=False, na=False) & ~df_temp['prod_lower'].str.contains('diesel', case=False, na=False)][c_vol].sum()
        tot_naf = vs + vin

        vd500 = df_temp[df_temp['prod_lower'].str.contains('500|d500|diesel 500', case=False, na=False)][c_vol].sum()
        vind = df_temp[df_temp['prod_lower'].str.contains('infinia diesel|diesel infinia|go', case=False, na=False)][c_vol].sum()
        tot_die = vd500 + vind
        return vs, vin, tot_naf, vd500, vind, tot_die

    vs_26, vin_26, tot_naf_26, vd500_26, vind_26, tot_die_26 = calcular_mix_datos(df_2026)
    vs_25, vin_25, tot_naf_25, vd500_25, vind_25, tot_die_25 = calcular_mix_datos(df_2025)

    st.markdown("### 📊 Mix de Ventas por Producto")
    col_mix1, col_mix2 = st.columns(2)

    with col_mix1:
        st.markdown("#### 🟢 Mix Naftas (Super / NS XXI vs Infinia)")
        if tot_naf_26 > 0 or tot_naf_25 > 0:
            pct_s_26 = (vs_26 / tot_naf_26 * 100) if tot_naf_26 > 0 else 0
            pct_i_26 = (vin_26 / tot_naf_26 * 100) if tot_naf_26 > 0 else 0
            pct_s_25 = (vs_25 / tot_naf_25 * 100) if tot_naf_25 > 0 else 0
            pct_i_25 = (vin_25 / tot_naf_25 * 100) if tot_naf_25 > 0 else 0

            df_mix_naftas_comp = pd.DataFrame({
                "Producto": ["Super / NS XXI", "Infinia"],
                "Volumen 2026 (L)": [f"{formato_arg(vs_26, 2)} L", f"{formato_arg(vin_26, 2)} L"],
                "Volumen 2025 (L)": [f"{formato_arg(vs_25, 2)} L", f"{formato_arg(vin_25, 2)} L"],
                "Mix 2026 (%)": [f"{pct_s_26:.2f}%", f"{pct_i_26:.2f}%"],
                "Mix 2025 (%)": [f"{pct_s_25:.2f}%", f"{pct_i_25:.2f}%"]
            })
            st.dataframe(df_mix_naftas_comp, use_container_width=True, hide_index=True)
        else:
            st.info("Sin datos suficientes para mix de naftas.")

    with col_mix2:
        st.markdown("#### 🛢️ Mix Diésel (GO - Infinia Diesel vs D. Diesel 500)")
        if tot_die_26 > 0 or tot_die_25 > 0:
            pct_d_26 = (vd500_26 / tot_die_26 * 100) if tot_die_26 > 0 else 0
            pct_id_26 = (vind_26 / tot_die_26 * 100) if tot_die_26 > 0 else 0
            pct_d_25 = (vd500_25 / tot_die_25 * 100) if tot_die_25 > 0 else 0
            pct_id_25 = (vind_25 / tot_die_25 * 100) if tot_die_25 > 0 else 0

            df_mix_diesel_comp = pd.DataFrame({
                "Producto": ["D. Diesel 500", "GO - Infinia Diesel"],
                "Volumen 2026 (L)": [f"{formato_arg(vd500_26, 2)} L", f"{formato_arg(vind_26, 2)} L"],
                "Volumen 2025 (L)": [f"{formato_arg(vd500_25, 2)} L", f"{formato_arg(vind_25, 2)} L"],
                "Mix 2026 (%)": [f"{pct_d_26:.2f}%", f"{pct_id_26:.2f}%"],
                "Mix 2025 (%)": [f"{pct_d_25:.2f}%", f"{pct_id_25:.2f}%"]
            })
            st.dataframe(df_mix_diesel_comp, use_container_width=True, hide_index=True)
        else:
            st.info("Sin datos suficientes para mix de diésel.")

    st.markdown("---")

    with st.expander(f"📂 Ver Detalle de Cargas del año 2026 ({mes_seleccionado_comb})", expanded=True):
        if not df_2026.empty:
            cols_a_excluir_26 = [c for c in df_2026.columns if str(c).startswith('_') or c == 'prod_lower' or 'venta' in str(c).lower()]
            df_mostrar_26 = df_2026.drop(columns=cols_a_excluir_26, errors='ignore')
            st.dataframe(df_mostrar_26, use_container_width=True, hide_index=True)
        else:
            st.info(f"No hay registros en la nube para Combustibles 2026 - {mes_seleccionado_comb}.")

    with st.expander(f"📂 Ver Detalle de Cargas del año 2025 ({mes_seleccionado_comb})"):
        if not df_2025.empty:
            cols_a_excluir_25 = [c for c in df_2025.columns if str(c).startswith('_') or c == 'prod_lower' or 'venta' in str(c).lower()]
            df_mostrar_25 = df_2025.drop(columns=cols_a_excluir_25, errors='ignore')
            st.dataframe(df_mostrar_25, use_container_width=True, hide_index=True)
        else:
            st.info(f"No hay registros en la nube para Combustibles 2025 - {mes_seleccionado_comb}.")

# ==========================================
# 3. TIENDA FULL
# ==========================================
elif menu_principal == "🛒 TIENDA FULL":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Seleccionar Mes y Año")
    mes_seleccionado_full = st.sidebar.selectbox("Mes Full", meses_lista)
    anio_full = st.sidebar.selectbox("Año Full", [2026, 2025], index=0, key="anio_full_sel")
    
    st.sidebar.markdown("---")
    st.sidebar.header("📥 Carga de Reportes .HTM (Turnos)")
    turno_subida = st.sidebar.selectbox("Seleccionar Turno", ["Mañana", "Tarde"], key="turno_full_htm")
    
    archivos_htm = st.sidebar.file_uploader(
        f"Subir archivos .HTM ({turno_subida}) - {mes_seleccionado_full} {anio_full}", 
        type=["htm", "html"], 
        accept_multiple_files=True,
        key=f"uploader_full_htm_{anio_full}_{mes_seleccionado_full}"
    )

    sheet_full_2026 = f"full_{mes_seleccionado_full.lower()}_2026"
    sheet_full_2025 = f"full_{mes_seleccionado_full.lower()}_2025"
    sheet_full_activa = sheet_full_2026 if anio_full == 2026 else sheet_full_2025

    if archivos_htm:
        for archivo_subido in archivos_htm:
            df_subido = leer_tabla_htm_directo(archivo_subido)
            if not df_subido.empty:
                df_subido["Turno"] = turno_subida
                df_subido["Archivo_Origen"] = archivo_subido.name
                
                key_state = f"full_{anio_full}"
                if mes_seleccionado_full not in st.session_state[key_state]:
                    st.session_state[key_state][mes_seleccionado_full] = pd.DataFrame()
                
                df_actual = st.session_state[key_state][mes_seleccionado_full]
                if df_actual.empty:
                    st.session_state[key_state][mes_seleccionado_full] = df_subido
                else:
                    # Alineamos columnas y concatenamos de manera segura
                    df_actual = limpiar_columnas(df_actual)
                    df_subido = limpiar_columnas(df_subido)
                    st.session_state[key_state][mes_seleccionado_full] = pd.concat([df_actual, df_subido], ignore_index=True)
                
                st.sidebar.success(f"¡Archivo {archivo_subido.name} ({turno_subida}) procesado!")

        if st.sidebar.button("💾 Guardar Tienda Full en la Nube", key=f"btn_guardar_full_{anio_full}_{mes_seleccionado_full}"):
            df_a_guardar = st.session_state[f"full_{anio_full}"].get(mes_seleccionado_full, pd.DataFrame())
            if not df_a_guardar.empty:
                with st.spinner("Guardando Tienda Full en Google Sheets..."):
                    exito = guardar_en_nube(sheet_full_activa, df_a_guardar)
                    if exito:
                        st.sidebar.success("¡Tienda Full guardada en la nube con éxito!")
                        st.cache_data.clear()
                    else:
                        st.sidebar.error("No se pudo guardar en la nube.")

    if mes_seleccionado_full not in st.session_state["full_2026"] or st.session_state["full_2026"][mes_seleccionado_full].empty:
        df_nube_full_26 = cargar_desde_nube(sheet_full_2026)
        if not df_nube_full_26.empty:
            st.session_state["full_2026"][mes_seleccionado_full] = df_nube_full_26

    if mes_seleccionado_full not in st.session_state["full_2025"] or st.session_state["full_2025"][mes_seleccionado_full].empty:
        df_nube_full_25 = cargar_desde_nube(sheet_full_2025)
        if not df_nube_full_25.empty:
            st.session_state["full_2025"][mes_seleccionado_full] = df_nube_full_25

    if st.sidebar.button("🔄 Actualizar Full desde la Nube", key="btn_actualizar_full_nube"):
        st.cache_data.clear()
        st.session_state["full_2026"].pop(mes_seleccionado_full, None)
        st.session_state["full_2025"].pop(mes_seleccionado_full, None)
        st.rerun()

    st.title(f"🛒 Tienda Full - {mes_seleccionado_full} (2026 vs 2025)")
    df_rubros_26 = limpiar_columnas(st.session_state["full_2026"].get(mes_seleccionado_full, pd.DataFrame()))
    df_rubros_25 = limpiar_columnas(st.session_state["full_2025"].get(mes_seleccionado_full, pd.DataFrame()))

    st.markdown(f"### 📋 Tienda Full - 2026")
    if not df_rubros_26.empty:
        st.dataframe(df_rubros_26, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros de Tienda Full en la nube para 2026 - {mes_seleccionado_full}.")

    with st.expander(f"📂 Ver Tienda Full del año 2025 ({mes_seleccionado_full})"):
        if not df_rubros_25.empty:
            st.dataframe(df_rubros_25, use_container_width=True, hide_index=True)
        else:
            st.info(f"No hay registros de Tienda Full en la nube para 2025 - {mes_seleccionado_full}.")

# ==========================================
# 4. BOXES
# ==========================================
elif menu_principal == "📦 BOXES":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Seleccionar Mes")
    mes_seleccionado_boxes = st.sidebar.selectbox("Mes Boxes", meses_lista)

    sheet_boxes_2026 = f"boxes_{mes_seleccionado_boxes.lower()}_2026"
    sheet_boxes_2025 = f"boxes_{mes_seleccionado_boxes.lower()}_2025"

    if mes_seleccionado_boxes not in st.session_state["boxes_2026"] or st.session_state["boxes_2026"][mes_seleccionado_boxes].empty:
        df_nube_boxes_26 = cargar_desde_nube(sheet_boxes_2026)
        if not df_nube_boxes_26.empty:
            st.session_state["boxes_2026"][mes_seleccionado_boxes] = df_nube_boxes_26

    if mes_seleccionado_boxes not in st.session_state["boxes_2025"] or st.session_state["boxes_2025"][mes_seleccionado_boxes].empty:
        df_nube_boxes_25 = cargar_desde_nube(sheet_boxes_2025)
        if not df_nube_boxes_25.empty:
            st.session_state["boxes_2025"][mes_seleccionado_boxes] = df_nube_boxes_25

    if st.sidebar.button("🔄 Actualizar Boxes desde la Nube"):
        st.cache_data.clear()
        st.session_state["boxes_2026"].pop(mes_seleccionado_boxes, None)
        st.session_state["boxes_2025"].pop(mes_seleccionado_boxes, None)
        st.rerun()

    df_b_26 = limpiar_columnas(st.session_state["boxes_2026"].get(mes_seleccionado_boxes, pd.DataFrame()))
    df_b_25 = limpiar_columnas(st.session_state["boxes_2025"].get(mes_seleccionado_boxes, pd.DataFrame()))

    st.subheader(f"📦 BOXES - {mes_seleccionado_boxes} (2026 vs 2025)")

    st.markdown(f"### 📋 Boxes - 2026")
    if not df_b_26.empty:
        st.dataframe(df_b_26, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros de Boxes en la nube para 2026 - {mes_seleccionado_boxes}.")

    with st.expander(f"📂 Ver Boxes del año 2025 ({mes_seleccionado_boxes})"):
        if not df_b_25.empty:
            st.dataframe(df_b_25, use_container_width=True, hide_index=True)
        else:
            st.info(f"No hay registros de Boxes en la nube para 2025 - {mes_seleccionado_boxes}.")

# ==========================================
# 5. TABLERO YPF
# ==========================================
elif menu_principal == "🎯 +YPF":
    st.sidebar.markdown("---")
    st.sidebar.header("🎯 Configuración YPF")
    mes_seleccionado_ypf = st.sidebar.selectbox("Mes YPF", meses_lista)

    st.subheader(f"🎯 Tablero de Exigencias YPF - {mes_seleccionado_ypf} (2026)")

    datos_ypf_base = [
        {"Concepto": "Volumen Diesel m3 (Infinia Diesel + D500)", "Objetivo mínimo": 59700.0, "Objetivo máximo": 69700.0, "Real": 59394.0, "Puntos posibles": 20},
        {"Concepto": "Volumen nafta m3 (Infinia + Super)", "Objetivo mínimo": 427000.0, "Objetivo máximo": 498100.0, "Real": 424652.0, "Puntos posibles": 25},
        {"Concepto": "Mix nafta infinia", "Objetivo mínimo": 30.70, "Objetivo máximo": 35.80, "Real": 35.98, "Puntos posibles": 10},
        {"Concepto": "Volumen lubricante m3 (trimestral)", "Objetivo mínimo": 2610.0, "Objetivo máximo": 2900.0, "Real": 2052.0, "Puntos posibles": 10},
        {"Concepto": "Crosselling", "Objetivo mínimo": 30.70, "Objetivo máximo": 37.60, "Real": 31.45, "Puntos posibles": 5},
        {"Concepto": "Unidades totales (sin tabaco)", "Objetivo mínimo": 9264.0, "Objetivo máximo": 10808.0, "Real": 9582.0, "Puntos posibles": 10},
        {"Concepto": "Unidades Comida y Cafetería", "Objetivo mínimo": 1930.0, "Objetivo máximo": 2133.0, "Real": 3674.0, "Puntos posibles": 10},
        {"Concepto": "Cliente Incognito", "Objetivo mínimo": 75.0, "Objetivo máximo": 100.0, "Real": 91.80, "Puntos posibles": 10}
    ]

    df_ypf = pd.DataFrame(datos_ypf_base)
    st.data_editor(df_ypf, use_container_width=True, hide_index=True, key=f"editor_ypf_{mes_seleccionado_ypf}")

    st.markdown("---")
    st.subheader("📊 Resumen de Evaluación")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Puntos Totales Posibles", value="95")
    with col2:
        st.metric(label="Puntos Obtenidos (Estimados)", value="34.74")
    with col3:
        st.metric(label="Estado General", value="En Seguimiento 🟡")
