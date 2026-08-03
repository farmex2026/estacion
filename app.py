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

# Selector global de año en la barra lateral para comparar 2025 y 2026
st.sidebar.markdown("---")
st.sidebar.header("📅 Selector de Año")
anio_activo = st.sidebar.selectbox("Año", [2026, 2025], index=0)

# ==========================================
# 1. DASHBOARD
# ==========================================
if menu_principal == "📊 DASHBOARD":
    st.title(f"📊 Dashboard General ({anio_activo})")
    st.info(f"Panel de control centralizado de la estación para el periodo {anio_activo} (Sincronizado con la nube).")

# ==========================================
# 2. COMBUSTIBLES
# ==========================================
elif menu_principal == "⛽ COMBUSTIBLES":
    st.sidebar.markdown("---")
    st.sidebar.header(f"📂 Mes Combustibles ({anio_activo})")
    mes_seleccionado_comb = st.sidebar.selectbox(
        "Mes Combustibles", meses_lista, key=f"mes_comb_{anio_activo}"
    )

    sheet_comb = f"combustibles_{mes_seleccionado_comb.lower()}_{anio_activo}"

    # Carga automática desde la nube si no está en memoria
    if (
        mes_seleccionado_comb not in st.session_state[f"combustibles_{anio_activo}"]
        or st.session_state[f"combustibles_{anio_activo}"][mes_seleccionado_comb].empty
    ):
        df_nube_comb = cargar_desde_nube(sheet_comb)
        if not df_nube_comb.empty:
            st.session_state[f"combustibles_{anio_activo}"][mes_seleccionado_comb] = df_nube_comb

    if st.sidebar.button(f"🔄 Actualizar Datos desde la Nube"):
        st.cache_data.clear()
        st.session_state[f"combustibles_{anio_activo}"].pop(mes_seleccionado_comb, None)
        df_nube_comb = cargar_desde_nube(sheet_comb)
        if not df_nube_comb.empty:
            st.session_state[f"combustibles_{anio_activo}"][mes_seleccionado_comb] = df_nube_comb
        st.rerun()

    df_c = st.session_state[f"combustibles_{anio_activo}"].get(mes_seleccionado_comb, pd.DataFrame())

    st.subheader(f"⛽ Gestión y Ventas de COMBUSTIBLES - {mes_seleccionado_comb} ({anio_activo})")

    if not df_c.empty:
        # Subir la primera fila como encabezado si contiene los nombres reales
        if len(df_c) > 0 and any("fecha" in str(v).lower() for v in df_c.iloc[0].values):
            df_c.columns = df_c.iloc[0].astype(str).str.strip()
            df_c = df_c.iloc[1:].reset_index(drop=True)

        # Asegurar limpieza de nombres de columnas
        df_c.columns = [str(c).strip() for c in df_c.columns]
        
        # Mapeo exacto de columnas según tu estructura requerida
        c_fecha = "Fecha y Hora" if "Fecha y Hora" in df_c.columns else df_c.columns[0]
        c_prod = "Producto" if "Producto" in df_c.columns else df_c.columns[2]
        c_vol = "Volumen" if "Volumen" in df_c.columns else df_c.columns[3]
        c_venta = "Venta Total" if "Venta Total" in df_c.columns else df_c.columns[4]
        
        # Convertir a numéricos de forma segura
        df_c[c_venta] = pd.to_numeric(df_c[c_venta], errors='coerce').fillna(0)
        df_c[c_vol] = pd.to_numeric(df_c[c_vol], errors='coerce').fillna(0)
        
        total_ventas = df_c[c_venta].sum()
        total_despachos = len(df_c)

        # Métricas principales arriba
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📦 Cantidad de Despachos", formato_arg(total_despachos))
        with col2:
            st.metric("⛽ Ventas Totales", formato_arg(total_ventas, 2 if total_ventas % 1 != 0 else 0))

        st.markdown("---")

        # Mix de Ventas por Producto (Naftas y Diésel) usando Volumen
        st.markdown("### 📊 Mix de Ventas por Producto")
        if c_prod in df_c.columns:
            df_c['prod_lower'] = df_c[c_prod].astype(str).str.lower()
            
            vol_super = df_c[df_c['prod_lower'].str.contains('super|ns xxi', case=False, na=False)][c_vol].sum()
            vol_infinia_nafta = df_c[df_c['prod_lower'].str.contains('infinia', case=False, na=False) & ~df_c['prod_lower'].str.contains('diesel', case=False, na=False)][c_vol].sum()
            total_naftas = vol_super + vol_infinia_nafta

            vol_d500 = df_c[df_c['prod_lower'].str.contains('500|d500|diesel 500', case=False, na=False)][c_vol].sum()
            vol_infinia_diesel = df_c[df_c['prod_lower'].str.contains('infinia diesel|diesel infinia|go', case=False, na=False)][c_vol].sum()
            total_diesel = vol_d500 + vol_infinia_diesel

            col_mix1, col_mix2 = st.columns(2)
            with col_mix1:
                st.markdown("#### 🟢 Mix Naftas (Super / NS XXI vs Infinia)")
                if total_naftas > 0:
                    pct_super = (vol_super / total_naftas) * 100
                    pct_infinia = (vol_infinia_nafta / total_naftas) * 100
                    df_mix_naftas = pd.DataFrame({
                        "Producto": ["Super / NS XXI", "Infinia"],
                        "Volumen (L)": [formato_arg(vol_super, 2), formato_arg(vol_infinia_nafta, 2)],
                        "Mix (%)": [f"{pct_super:.2f}%", f"{pct_infinia:.2f}%"]
                    })
                    st.dataframe(df_mix_naftas, use_container_width=True, hide_index=True)
                else:
                    st.info("Procesando mix de naftas...")

            with col_mix2:
                st.markdown("#### 🛢️ Mix Diésel (GO - INFINIA DIESEL vs D. DIESEL 500)")
                if total_diesel > 0:
                    pct_d500 = (vol_d500 / total_diesel) * 100
                    pct_inf_diesel = (vol_infinia_diesel / total_diesel) * 100
                    df_mix_diesel = pd.DataFrame({
                        "Producto": ["D. Diesel 500", "GO - Infinia Diesel"],
                        "Volumen (L)": [formato_arg(vol_d500, 2), formato_arg(vol_infinia_diesel, 2)],
                        "Mix (%)": [f"{pct_d500:.2f}%", f"{pct_inf_diesel:.2f}%"]
                    })
                    st.dataframe(df_mix_diesel, use_container_width=True, hide_index=True)
                else:
                    st.info("Procesando mix de diésel...")
        else:
            st.info("Procesando mix de productos...")

        st.markdown("---")
        st.markdown("### 📋 Detalle General de Cargas")
        df_mostrar = df_c.drop(columns=[c for c in df_c.columns if str(c).startswith('_') or c == 'prod_lower'], errors='ignore')
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros de Combustibles en la nube para **{mes_seleccionado_comb} {anio_activo}**.")

# ==========================================
# 3. TIENDA FULL
# ==========================================
elif menu_principal == "🛒 TIENDA FULL":
    st.sidebar.markdown("---")
    st.sidebar.header(f"📂 Mes Full ({anio_activo})")
    mes_seleccionado_full = st.sidebar.selectbox("Mes Full", meses_lista, key=f"mes_full_{anio_activo}")
    
    sheet_full = f"full_{mes_seleccionado_full.lower()}_{anio_activo}"

    if (
        mes_seleccionado_full not in st.session_state[f"full_{anio_activo}"]
        or st.session_state[f"full_{anio_activo}"][mes_seleccionado_full].empty
    ):
        df_nube_full = cargar_desde_nube(sheet_full)
        if not df_nube_full.empty:
            st.session_state[f"full_{anio_activo}"][mes_seleccionado_full] = df_nube_full

    if st.sidebar.button(f"🔄 Actualizar Full desde la Nube"):
        st.cache_data.clear()
        st.session_state[f"full_{anio_activo}"].pop(mes_seleccionado_full, None)
        df_nube_full = cargar_desde_nube(sheet_full)
        if not df_nube_full.empty:
            st.session_state[f"full_{anio_activo}"][mes_seleccionado_full] = df_nube_full
        st.rerun()

    st.title(f"🛒 Tienda Full - {mes_seleccionado_full} ({anio_activo})")
    df_rubros = st.session_state[f"full_{anio_activo}"].get(mes_seleccionado_full, pd.DataFrame())

    if not df_rubros.empty:
        cols_lower = {str(c).lower().strip(): c for c in df_rubros.columns}
        col_codigo = next((cols_lower[c] for c in cols_lower if c in ["codigo", "código", "cod"]), None)
        col_rubro = next((cols_lower[c] for c in cols_lower if c in ["rubro", "descripcion", "descripción", "categoria", "categoría"]), None)
        col_cantidad = next((cols_lower[c] for c in cols_lower if c in ["cantidad", "cant", "unidades", "ventas"]), None)

        if col_codigo and col_rubro and col_cantidad:
            df_temp = df_rubros.rename(columns={col_codigo: "Codigo", col_rubro: "Rubro", col_cantidad: "Cantidad"})
            df_temp["Cantidad"] = pd.to_numeric(df_temp["Cantidad"], errors="coerce").fillna(0)

            df_rubros_sum = (
                df_temp.groupby(["Codigo", "Rubro"])["Cantidad"]
                .sum()
                .reset_index()
            )
            df_rubros_sum = df_rubros_sum.sort_values(
                by="Cantidad", ascending=False
            ).reset_index(drop=True)

            st.dataframe(
                df_rubros_sum.style.format({"Cantidad": lambda x: formato_arg(x, 0)}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.dataframe(df_rubros, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros de Tienda Full en la nube para **{mes_seleccionado_full} {anio_activo}**.")

# ==========================================
# 4. BOXES
# ==========================================
elif menu_principal == "📦 BOXES":
    st.sidebar.markdown("---")
    st.sidebar.header(f"📂 Mes Boxes ({anio_activo})")
    mes_seleccionado_boxes = st.sidebar.selectbox(
        "Mes Boxes", meses_lista, key=f"mes_boxes_{anio_activo}"
    )

    sheet_boxes = f"boxes_{mes_seleccionado_boxes.lower()}_{anio_activo}"

    if (
        mes_seleccionado_boxes not in st.session_state[f"boxes_{anio_activo}"]
        or st.session_state[f"boxes_{anio_activo}"][mes_seleccionado_boxes].empty
    ):
        df_nube_boxes = cargar_desde_nube(sheet_boxes)
        if not df_nube_boxes.empty:
            st.session_state[f"boxes_{anio_activo}"][mes_seleccionado_boxes] = df_nube_boxes

    if st.sidebar.button(f"🔄 Actualizar Boxes desde la Nube"):
        st.cache_data.clear()
        st.session_state[f"boxes_{anio_activo}"].pop(mes_seleccionado_boxes, None)
        df_nube_boxes = cargar_desde_nube(sheet_boxes)
        if not df_nube_boxes.empty:
            st.session_state[f"boxes_{anio_activo}"][mes_seleccionado_boxes] = df_nube_boxes
        st.rerun()

    df_b = st.session_state[f"boxes_{anio_activo}"].get(mes_seleccionado_boxes, pd.DataFrame())

    st.subheader(f"📦 BOXES - {mes_seleccionado_boxes} ({anio_activo})")

    if not df_b.empty:
        st.success(f"✅ Registros cargados: {len(df_b)} filas")
        st.markdown("---")
        st.dataframe(df_b, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros de Boxes en la nube para **{mes_seleccionado_boxes} {anio_activo}**.")

# ==========================================
# 5. TABLERO YPF
# ==========================================
elif menu_principal == "🎯 +YPF":
    st.sidebar.markdown("---")
    st.sidebar.header(f"🎯 Configuración YPF ({anio_activo})")
    mes_seleccionado_ypf = st.sidebar.selectbox(
        "Mes YPF", meses_lista, key=f"mes_ypf_{anio_activo}"
    )

    st.subheader(f"🎯 Tablero de Exigencias YPF - {mes_seleccionado_ypf} ({anio_activo})")

    unidades_comida_real_calculado = 0
    try:
        if f"full_{anio_activo}" in st.session_state and mes_seleccionado_ypf in st.session_state[f"full_{anio_activo}"]:
            df_full_temp = st.session_state[f"full_{anio_activo}"][mes_seleccionado_ypf]
            cols_lower = {str(c).lower().strip(): c for c in df_full_temp.columns}
            col_rubro = next((cols_lower[c] for c in cols_lower if c in ["rubro", "descripcion", "descripción", "categoria", "categoría"]), None)
            col_cantidad = next((cols_lower[c] for c in cols_lower if c in ["cantidad", "cant", "unidades", "ventas"]), None)

            if col_rubro and col_cantidad:
                mask_comida = df_full_temp[col_rubro].astype(str).str.contains("Comida|Cafeteria|Cafetería", case=False, na=False)
                unidades_comida_real_calculado = int(pd.to_numeric(df_full_temp.loc[mask_comida, col_cantidad], errors="coerce").sum())
    except Exception:
        unidades_comida_real_calculado = 0

    if unidades_comida_real_calculado == 0:
        unidades_comida_real_calculado = 3674

    datos_ypf_base = [
        {
            "Concepto": "Volumen Diesel m3 (Infinia Diesel + D500)",
            "Objetivo mínimo": 59700.0,
            "Objetivo máximo": 69700.0,
            "Real": 59394.0,
            "Puntos posibles": 20,
        },
        {
            "Concepto": "Volumen nafta m3 (Infinia + Super)",
            "Objetivo mínimo": 427000.0,
            "Objetivo máximo": 498100.0,
            "Real": 424652.0,
            "Puntos posibles": 25,
        },
        {
            "Concepto": "Mix nafta infinia",
            "Objetivo mínimo": 30.70,
            "Objetivo máximo": 35.80,
            "Real": 35.98,
            "Puntos posibles": 10,
        },
        {
            "Concepto": "Volumen lubricante m3 (trimestral)",
            "Objetivo mínimo": 2610.0,
            "Objetivo máximo": 2900.0,
            "Real": 2052.0,
            "Puntos posibles": 10,
        },
        {
            "Concepto": "Crosselling",
            "Objetivo mínimo": 30.70,
            "Objetivo máximo": 37.60,
            "Real": 31.45,
            "Puntos posibles": 5,
        },
        {
            "Concepto": "Unidades totales (sin tabaco)",
            "Objetivo mínimo": 9264.0,
            "Objetivo máximo": 10808.0,
            "Real": 9582.0,
            "Puntos posibles": 10,
        },
        {
            "Concepto": "Unidades Comida y Cafetería",
            "Objetivo mínimo": 1930.0,
            "Objetivo máximo": 2133.0,
            "Real": float(unidades_comida_real_calculado),
            "Puntos posibles": 10,
        },
        {
            "Concepto": "Cliente Incognito",
            "Objetivo mínimo": 75.0,
            "Objetivo máximo": 100.0,
            "Real": 91.80,
            "Puntos posibles": 10,
        }
    ]

    df_ypf = pd.DataFrame(datos_ypf_base)

    st.markdown(f"### 📋 Planilla de Objetivos e Indicadores ({anio_activo})")
    
    df_ypf_editado = st.data_editor(
        df_ypf,
        use_container_width=True,
        hide_index=True,
        key=f"editor_ypf_{anio_activo}_{mes_seleccionado_ypf}"
    )

    st.markdown("---")
    st.subheader("📊 Resumen de Evaluación")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Puntos Totales Posibles", value="95")
    with col2:
        st.metric(label="Puntos Obtenidos (Estimados)", value="34.74")
    with col3:
        st.metric(label="Estado General", value="En Seguimiento 🟡")
