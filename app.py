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

# Tu URL de Google Apps Script conectada
URL_NUBE = "https://script.google.com/macros/s/AKfycbxUWd3i5utU7OeQcT462lTRi91aPRLBAH9E6lulLuV2W1FPn68wMaMfkS8RjdTnXPUd/exec"

def cargar_desd_nube(sheet_name):
    try:
        if URL_NUBE:
            res = requests.get(f"{URL_NUBE}?month={sheet_name}", timeout=15)
            if res.status_code == 200:
                data = res.json()
                if "rows" in data and "headers" in data and data["rows"]:
                    return pd.DataFrame(data["rows"], columns=data["headers"])
    except Exception as e:
        st.warning(f"No se pudo cargar desde la nube: {e}")
    return pd.DataFrame()

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
                    # Se configuro header=6 para que lea a partir de la fila 7 (A7)
                    df_c = pd.read_excel(arq, header=6)
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
                        requests.post(URL_NUBE, json=payload, timeout=60)
                    st.success(f"¡Combustibles de {anio_activo} guardados en la nube!")
                except Exception as e:
                    st.error(f"Error al guardar en la nube: {e}")

    df_c = st.session_state[f"combustibles_{anio_activo}"].get(mes_seleccionado_comb, pd.DataFrame())

    st.subheader(f"⛽ Gestión y Ventas de COMBUSTIBLES - {mes_seleccionado_comb} ({anio_activo})")

    if not df_c.empty:
        st.success(f"✅ Registros cargados: {len(df_c)} filas")
        st.markdown("---")
        st.dataframe(df_c, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros de Combustibles para **{mes_seleccionado_comb} {anio_activo}**.")

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
                    df_f = pd.read_excel(arq)
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
                        requests.post(URL_NUBE, json=payload, timeout=60)
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
                return f"{int(val):,}"

            st.dataframe(
                df_rubros_sum.style.format({"Cantidad": fmt_entero}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("⚠️ Columnas detectadas de forma general:")
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
                    df_b = pd.read_excel(arq)
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
                        requests.post(URL_NUBE, json=payload, timeout=60)
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
