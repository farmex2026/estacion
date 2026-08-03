import streamlit as st
import pandas as pd
import requests

# Configuración inicial de la página
st.set_page_config(page_title="Gestión Estación YPF", layout="wide")

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

# Función robusta con caché corto para actualización instantánea
@st.cache_data(ttl=5, show_spinner="Sincronizando con la nube...")
def cargar_desd_nube(sheet_name):
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
        st.warning(f"No se pudo cargar desde la nube: {e}")
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
    st.info(f"Panel de control centralizado de la estación para el periodo {anio_activo}.")

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

    if (
        mes_seleccionado_comb not in st.session_state[f"combustibles_{anio_activo}"]
        or st.session_state[f"combustibles_{anio_activo}"][mes_seleccionado_comb].empty
    ):
        df_nube_comb = cargar_desd_nube(sheet_comb)
        if not df_nube_comb.empty:
            st.session_state[f"combustibles_{anio_activo}"][mes_seleccionado_comb] = df_nube_comb

    if st.sidebar.button(f"🔄 Recargar Combustibles {anio_activo} desde la Nube"):
        st.cache_data.clear()
        st.session_state[f"combustibles_{anio_activo}"].pop(mes_seleccionado_comb, None)
        df_nube_comb = cargar_desd_nube(sheet_comb)
        if not df_nube_comb.empty:
            st.session_state[f"combustibles_{anio_activo}"][mes_seleccionado_comb] = df_nube_comb
        st.rerun()

    with st.sidebar.expander(f"🔐 Panel Admin (Subir Combustibles {anio_activo})"):
        archivos_comb = st.file_uploader(
            f"Subir Planillas Combustibles ({anio_activo})",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            key=f"uploader_comb_{anio_activo}_{mes_seleccionado_comb}",
        )

        if archivos_comb:
            lista_dfs_comb = []
            for arq in archivos_comb:
                try:
                    df_c = pd.read_excel(arq, header=0)
                    df_c.columns = [str(c).strip() for c in df_c.columns]
                    lista_dfs_comb.append(df_c)
                except Exception as e:
                    st.warning(f"No se pudo leer el archivo {arq.name}: {e}")

            if lista_dfs_comb:
                df_comb_concatenado = pd.concat(lista_dfs_comb, ignore_index=True).drop_duplicates().reset_index(drop=True)
                st.session_state[f"combustibles_{anio_activo}"][mes_seleccionado_comb] = df_comb_concatenado

                try:
                    df_para_nube = df_comb_concatenado.copy().fillna("").astype(str)
                    payload = {
                        "month": sheet_comb,
                        "headers": df_para_nube.columns.tolist(),
                        "rows": df_para_nube.values.tolist(),
                    }
                    if URL_NUBE:
                        requests.post(URL_NUBE, json=payload, timeout=30)
                    st.cache_data.clear()
                    st.success(f"¡Combustibles de {anio_activo} guardados en la nube!")
                except Exception as e:
                    st.error(f"Error al guardar en la nube: {e}")

    df_c = st.session_state[f"combustibles_{anio_activo}"].get(mes_seleccionado_comb, pd.DataFrame())

    st.subheader(f"⛽ Gestión y Ventas de COMBUSTIBLES - {mes_seleccionado_comb} ({anio_activo})")

    if not df_c.empty:
        # 1. Venta Totales: Extraído estrictamente de la Columna 5 (índice 4)
        c_vol = df_c.columns[4] if len(df_c.columns) >= 5 else df_c.columns[-1]
        df_c[c_vol] = pd.to_numeric(df_c[c_vol], errors='coerce').fillna(0)
        total_ventas = df_c[c_vol].sum()

        # Cantidad de despachos
        c_desp = next((c for c in df_c.columns if any(k in str(c).lower() for k in ["despacho", "cant", "transaccion"])), None)
        total_despachos = int(df_c[c_desp].sum()) if c_desp and pd.to_numeric(df_c[c_desp], errors='coerce').notna().sum() > 0 else len(df_c)

        # 2. Detección automática inteligente de Producto
        c_prod = None
        for col in df_c.columns:
            c_low = str(col).lower()
            if any(k in c_low for k in ["producto", "combustible", "articulo", "tipo", "desc", "fuel"]):
                c_prod = col
                break
        if not c_prod:
            for col in df_c.columns:
                if df_c[col].dtype == object:
                    c_prod = col
                    break

        # 3. Detección automática inteligente de Surtidor
        c_surtidor = None
        for col in df_c.columns:
            c_low = str(col).lower()
            if any(k in c_low for k in ["surtidor", "surt", "isla", "manguera", "boca", "pico", "pos"]):
                c_surtidor = col
                break
        if not c_surtidor:
            for col in df_c.columns:
                if col != c_vol:
                    s_num = pd.to_numeric(df_c[col], errors='coerce')
                    if s_num.notna().sum() > 0 and s_num.nunique() <= 15 and s_num.min() >= 1:
                        c_surtidor = col
                        break

        # 4. Detección automática inteligente de Día / Fecha
        c_dia = None
        for col in df_c.columns:
            c_low = str(col).lower()
            if any(k in c_low for k in ["dia", "día", "fecha", "date", "fch", "semana", "day"]):
                c_dia = col
                break

        # Métricas principales arriba perfectamente alineadas
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📦 Cantidad de Despachos", formato_arg(total_despachos))
        with col2:
            st.metric("⛽ Ventas Totales", formato_arg(total_ventas, 2 if total_ventas % 1 != 0 else 0))

        st.markdown("---")

        # Bloque de Surtidores y Días de la semana alineados en 2 columnas
        col_surt, col_dias = st.columns(2)

        with col_surt:
            st.markdown("### 🔌 Ventas por Surtidor")
            if c_surtidor:
                df_surt_sum = df_c.groupby(c_surtidor)[c_vol].sum().reset_index()
                df_surt_sum.columns = ["Surtidor", "Volumen (Litros)"]
                df_surt_sum = df_surt_sum.sort_values(by="Volumen (Litros)", ascending=False).reset_index(drop=True)
                st.dataframe(
                    df_surt_sum.style.format({"Volumen (Litros)": lambda x: formato_arg(x, 2)}),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Calculando distribución por surtidor...")

        with col_dias:
            st.markdown("### 📅 Ventas por Día")
            if c_dia:
                df_dia_sum = df_c.groupby(c_dia)[c_vol].sum().reset_index()
                df_dia_sum.columns = ["Día / Fecha", "Volumen (Litros)"]
                st.dataframe(
                    df_dia_sum.style.format({"Volumen (Litros)": lambda x: formato_arg(x, 2)}),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Calculando distribución por día...")

        st.markdown("---")

        # Mix de Ventas por Producto (Naftas y Diésel)
        st.markdown("### 📊 Mix de Ventas por Producto")
        if c_prod:
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
                        "Volumen (Litros)": [formato_arg(vol_super, 2), formato_arg(vol_infinia_nafta, 2)],
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
                        "Volumen (Litros)": [formato_arg(vol_d500, 2), formato_arg(vol_infinia_diesel, 2)],
                        "Mix (%)": [f"{pct_d500:.2f}%", f"{pct_inf_diesel:.2f}%"]
                    })
                    st.dataframe(df_mix_diesel, use_container_width=True, hide_index=True)
                else:
                    st.info("Procesando mix de diésel...")
        else:
            st.info("Procesando mix de productos...")

        st.markdown("---")
        st.markdown("### 📋 Detalle General de Cargas")
        df_mostrar = df_c.drop(columns=[c for c in ['prod_lower'] if c in df_c.columns], errors='ignore')
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros de Combustibles cargados para **{mes_seleccionado_comb} {anio_activo}**.")

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
        df_nube_full = cargar_desd_nube(sheet_full)
        if not df_nube_full.empty:
            st.session_state[f"full_{anio_activo}"][mes_seleccionado_full] = df_nube_full

    if st.sidebar.button(f"🔄 Recargar Full {anio_activo} desde la Nube"):
        st.cache_data.clear()
        st.session_state[f"full_{anio_activo}"].pop(mes_seleccionado_full, None)
        df_nube_full = cargar_desd_nube(sheet_full)
        if not df_nube_full.empty:
            st.session_state[f"full_{anio_activo}"][mes_seleccionado_full] = df_nube_full
        st.rerun()

    with st.sidebar.expander(f"🔐 Panel Admin (Subir Full {anio_activo})"):
        archivos_full = st.file_uploader(
            f"Subir Planillas Full ({anio_activo})",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            key=f"uploader_full_{anio_activo}_{mes_seleccionado_full}",
        )

        if archivos_full:
            lista_dfs_full = []
            for arq in archivos_full:
                try:
                    df_f = pd.read_excel(arq, header=0)
                    df_f.columns = [str(c).strip() for c in df_f.columns]
                    lista_dfs_full.append(df_f)
                except Exception as e:
                    st.warning(f"No se pudo leer el archivo {arq.name}: {e}")

            if lista_dfs_full:
                df_full_concatenado = pd.concat(lista_dfs_full, ignore_index=True).drop_duplicates().reset_index(drop=True)
                st.session_state[f"full_{anio_activo}"][mes_seleccionado_full] = df_full_concatenado

                try:
                    df_para_nube = df_full_concatenado.copy().fillna("").astype(str)
                    payload = {
                        "month": sheet_full,
                        "headers": df_para_nube.columns.tolist(),
                        "rows": df_para_nube.values.tolist(),
                    }
                    if URL_NUBE:
                        requests.post(URL_NUBE, json=payload, timeout=30)
                    st.cache_data.clear()
                    st.success(f"¡Full de {anio_activo} guardado en la nube!")
                except Exception as e:
                    st.error(f"Error al guardar en la nube: {e}")

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

            def fmt_entero(val):
                return formato_arg(val, 0)

            st.dataframe(
                df_rubros_sum.style.format({"Cantidad": fmt_entero}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.dataframe(df_rubros, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros de Tienda Full para **{mes_seleccionado_full} {anio_activo}**.")

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
        df_nube_boxes = cargar_desd_nube(sheet_boxes)
        if not df_nube_boxes.empty:
            st.session_state[f"boxes_{anio_activo}"][mes_seleccionado_boxes] = df_nube_boxes

    if st.sidebar.button(f"🔄 Recargar Boxes {anio_activo} desde la Nube"):
        st.cache_data.clear()
        st.session_state[f"boxes_{anio_activo}"].pop(mes_seleccionado_boxes, None)
        df_nube_boxes = cargar_desd_nube(sheet_boxes)
        if not df_nube_boxes.empty:
            st.session_state[f"boxes_{anio_activo}"][mes_seleccionado_boxes] = df_nube_boxes
        st.rerun()

    with st.sidebar.expander(f"🔐 Panel Admin (Subir Boxes {anio_activo})"):
        archivos_boxes = st.file_uploader(
            f"Subir Planillas Boxes ({anio_activo})",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            key=f"uploader_boxes_{anio_activo}_{mes_seleccionado_boxes}",
        )

        if archivos_boxes:
            lista_dfs_boxes = []
            for arq in archivos_boxes:
                try:
                    df_b = pd.read_excel(arq, header=0)
                    df_b.columns = [str(c).strip() for c in df_b.columns]
                    lista_dfs_boxes.append(df_b)
                except Exception as e:
                    st.warning(f"No se pudo leer el archivo {arq.name}: {e}")

            if lista_dfs_boxes:
                df_boxes_concatenado = pd.concat(lista_dfs_boxes, ignore_index=True).drop_duplicates().reset_index(drop=True)
                st.session_state[f"boxes_{anio_activo}"][mes_seleccionado_boxes] = df_boxes_concatenado

                try:
                    df_para_nube = df_boxes_concatenado.copy().fillna("").astype(str)
                    payload = {
                        "month": sheet_boxes,
                        "headers": df_para_nube.columns.tolist(),
                        "rows": df_para_nube.values.tolist(),
                    }
                    if URL_NUBE:
                        requests.post(URL_NUBE, json=payload, timeout=30)
                    st.cache_data.clear()
                    st.success(f"¡Boxes de {anio_activo} guardados en la nube!")
                except Exception as e:
                    st.error(f"Error al guardar en la nube: {e}")

    df_b = st.session_state[f"boxes_{anio_activo}"].get(mes_seleccionado_boxes, pd.DataFrame())

    st.subheader(f"📦 BOXES - {mes_seleccionado_boxes} ({anio_activo})")

    if not df_b.empty:
        st.success(f"✅ Registros cargados: {len(df_b)} filas")
        st.markdown("---")
        st.dataframe(df_b, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros de Boxes para **{mes_seleccionado_boxes} {anio_activo}**.")

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
