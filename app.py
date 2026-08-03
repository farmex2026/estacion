import streamlit as st
import pandas as pd
import requests

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

# URL de Google Apps Script conectada
URL_NUBE = "https://script.google.com/macros/s/AKfycbxUWd3i5utU7OeQcT462lTRi91aPRLBAH9E6lulLuV2W1FPn68wMaMfkS8RjdTnXPUd/exec"

# Función robusta con caché corto para actualización instantánea desde la nube
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
                        return pd.DataFrame(rows, columns=headers)
                    elif rows and not headers:
                        return pd.DataFrame(rows)
                elif isinstance(data, list) and len(data) > 0:
                    return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"No se pudo conectar con la nube: {e}")
    return pd.DataFrame()

# Formateador de números estilo argentino (ej: 2.154 o 1.254.300)
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
# 2. COMBUSTIBLES
# ==========================================
elif menu_principal == "⛽ COMBUSTIBLES":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Seleccionar Mes")
    mes_seleccionado_comb = st.sidebar.selectbox("Mes Combustibles", meses_lista)

    # Opción de carga manual de archivo para 2026
    st.sidebar.markdown("---")
    st.sidebar.header("📥 Carga Manual de Archivo (2026)")
    archivo_subido = st.sidebar.file_uploader(f"Subir Excel/CSV 2026 - {mes_seleccionado_comb}", type=["csv", "xlsx", "xls"], key=f"uploader_comb_2026_{mes_seleccionado_comb}")
    if archivo_subido is not None:
        try:
            if archivo_subido.name.endswith('.csv'):
                df_subido = pd.read_csv(archivo_subido)
            else:
                df_subido = pd.read_excel(archivo_subido)
            if not df_subido.empty:
                st.session_state["combustibles_2026"][mes_seleccionado_comb] = df_subido
                st.sidebar.success("¡Archivo 2026 cargado con éxito!")
        except Exception as e:
            st.sidebar.error(f"Error al leer el archivo: {e}")

    sheet_comb_2026 = f"combustibles_{mes_seleccionado_comb.lower()}_2026"
    sheet_comb_2025 = f"combustibles_{mes_seleccionado_comb.lower()}_2025"

    # Carga automática desde la nube si no está en memoria
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

    st.subheader(f"⛽ COMBUSTIBLES - {mes_seleccionado_comb} (VS 2026 vs 2025)")

    # Procesar datos 2026
    vol_2026, desp_2026 = 0, 0
    if not df_2026.empty:
        if len(df_2026) > 0 and any("fecha" in str(v).lower() for v in df_2026.iloc[0].values):
            df_2026.columns = df_2026.iloc[0].astype(str).str.strip()
            df_2026 = df_2026.iloc[1:].reset_index(drop=True)
        df_2026.columns = [str(c).strip() for c in df_2026.columns]
        c_vol_26 = "Volumen" if "Volumen" in df_2026.columns else df_2026.columns[3]
        df_2026[c_vol_26] = pd.to_numeric(df_2026[c_vol_26], errors='coerce').fillna(0)
        vol_2026 = df_2026[c_vol_26].sum()
        desp_2026 = len(df_2026)

    # Procesar datos 2025
    vol_2025, desp_2025 = 0, 0
    if not df_2025.empty:
        if len(df_2025) > 0 and any("fecha" in str(v).lower() for v in df_2025.iloc[0].values):
            df_2025.columns = df_2025.iloc[0].astype(str).str.strip()
            df_2025 = df_2025.iloc[1:].reset_index(drop=True)
        df_2025.columns = [str(c).strip() for c in df_2025.columns]
        c_vol_25 = "Volumen" if "Volumen" in df_2025.columns else df_2025.columns[3]
        df_2025[c_vol_25] = pd.to_numeric(df_2025[c_vol_25], errors='coerce').fillna(0)
        vol_2025 = df_2025[c_vol_25].sum()
        desp_2025 = len(df_2025)

    # Métricas comparativas lado a lado (sin ventas totales en pesos)
    col1, col2 = st.columns(2)
    with col1:
        diff_vol = ((vol_2026 - vol_2025) / vol_2025 * 100) if vol_2025 > 0 else 0
        st.metric("📦 Volumen Total (L) 2026", f"{formato_arg(vol_2026, 2)} L", delta=f"{diff_vol:+.2f}% vs 2025 ({formato_arg(vol_2025, 2)} L)")
    with col2:
        diff_desp = ((desp_2026 - desp_2025) / desp_2025 * 100) if desp_2025 > 0 else 0
        st.metric("🔢 Despachos 2026", formato_arg(desp_2026), delta=f"{diff_desp:+.2f}% vs 2025 ({formato_arg(desp_2025)})")

    st.markdown("---")

    # Tabla 2026 plegable y sin columna de Venta Total
    with st.expander(f"📂 Ver Detalle de Cargas del año 2026 ({mes_seleccionado_comb})", expanded=True):
        if not df_2026.empty:
            cols_a_excluir_26 = [c for c in df_2026.columns if str(c).startswith('_') or c == 'prod_lower' or 'venta' in str(c).lower()]
            df_mostrar_26 = df_2026.drop(columns=cols_a_excluir_26, errors='ignore')
            st.dataframe(df_mostrar_26, use_container_width=True, hide_index=True)
        else:
            st.info(f"No hay registros en la nube para Combustibles 2026 - {mes_seleccionado_comb}.")

    # Tabla 2025 plegable y sin columna de Venta Total
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
    st.sidebar.header("📂 Seleccionar Mes")
    mes_seleccionado_full = st.sidebar.selectbox("Mes Full", meses_lista)
    
    sheet_full_2026 = f"full_{mes_seleccionado_full.lower()}_2026"
    sheet_full_2025 = f"full_{mes_seleccionado_full.lower()}_2025"

    if mes_seleccionado_full not in st.session_state["full_2026"] or st.session_state["full_2026"][mes_seleccionado_full].empty:
        df_nube_full_26 = cargar_desde_nube(sheet_full_2026)
        if not df_nube_full_26.empty:
            st.session_state["full_2026"][mes_seleccionado_full] = df_nube_full_26

    if mes_seleccionado_full not in st.session_state["full_2025"] or st.session_state["full_2025"][mes_seleccionado_full].empty:
        df_nube_full_25 = cargar_desde_nube(sheet_full_2025)
        if not df_nube_full_25.empty:
            st.session_state["full_2025"][mes_seleccionado_full] = df_nube_full_25

    if st.sidebar.button("🔄 Actualizar Full desde la Nube"):
        st.cache_data.clear()
        st.session_state["full_2026"].pop(mes_seleccionado_full, None)
        st.session_state["full_2025"].pop(mes_seleccionado_full, None)
        st.rerun()

    st.title(f"🛒 Tienda Full - {mes_seleccionado_full} (VS 2026 vs 2025)")
    df_rubros_26 = st.session_state["full_2026"].get(mes_seleccionado_full, pd.DataFrame())
    df_rubros_25 = st.session_state["full_2025"].get(mes_seleccionado_full, pd.DataFrame())

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

    df_b_26 = st.session_state["boxes_2026"].get(mes_seleccionado_boxes, pd.DataFrame())
    df_b_25 = st.session_state["boxes_2025"].get(mes_seleccionado_boxes, pd.DataFrame())

    st.subheader(f"📦 BOXES - {mes_seleccionado_boxes} (VS 2026 vs 2025)")

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
