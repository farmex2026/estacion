import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Gestión Estación YPF", layout="wide")

# Inicialización de session_state si no existe
if "full_2026" not in st.session_state:
    st.session_state.full_2026 = {}
if "boxes_2026" not in st.session_state:
    st.session_state.boxes_2026 = {}

meses_lista = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

URL_NUBE = ""  # Tu URL de Google Apps Script o API si la usas

def cargar_desd_nube(sheet_name):
    try:
        if URL_NUBE:
            res = requests.get(f"{URL_NUBE}?month={sheet_name}", timeout=10)
            if res.status_code == 200:
                data = res.json()
                if "rows" in data and "headers" in data:
                    return pd.DataFrame(data["rows"], columns=data["headers"])
    except Exception:
        pass
    return pd.DataFrame()

# Menú principal en la barra lateral
menu_principal = st.sidebar.selectbox(
    "Menú Principal", 
    ["📊 DASHBOARD", "⛽ COMBUSTIBLES", "🛒 TIENDA FULL", "📦 BOXES", "🎯 +YPF"]
)

if menu_principal == "📊 DASHBOARD":
    st.title("📊 Dashboard General")
    st.info("Bienvenido al panel de control de la estación.")

elif menu_principal == "⛽ COMBUSTIBLES":
    st.title("⛽ Gestión de Combustibles")
    st.info("Módulo de combustibles activo.")

elif menu_principal == "🛒 TIENDA FULL":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Seleccionar Mes (Full)")
    mes_seleccionado_full = st.sidebar.selectbox("Mes Full", meses_lista, key="mes_full_menu")
    
    sheet_full_26 = f"full_{mes_seleccionado_full.lower()}_2026"

    # Cargar desde la nube si está vacío
    if (
        mes_seleccionado_full not in st.session_state.full_2026
        or st.session_state.full_2026[mes_seleccionado_full].empty
    ):
        df_nube_full = cargar_desd_nube(sheet_full_26)
        if not df_nube_full.empty:
            st.session_state.full_2026[mes_seleccionado_full] = df_nube_full

    if st.sidebar.button("🔄 Recargar Full desde la Nube"):
        st.session_state.full_2026.pop(mes_seleccionado_full, None)
        df_nube_full = cargar_desd_nube(sheet_full_26)
        if not df_nube_full.empty:
            st.session_state.full_2026[mes_seleccionado_full] = df_nube_full
        st.rerun()

    # PANEL ADMIN (Subir Excel Tienda Full)
    with st.sidebar.expander("🔐 Panel Admin (Subir Excel Full)"):
        archivos_full = st.file_uploader(
            f"Subir Planillas Full (2026)",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            key=f"uploader_full_2026_{mes_seleccionado_full}",
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
                st.session_state.full_2026[mes_seleccionado_full] = df_full_concatenado

                try:
                    df_para_nube = df_full_concatenado.copy().fillna("").astype(str)
                    payload = {
                        "month": sheet_full_26,
                        "headers": df_para_nube.columns.tolist(),
                        "rows": df_para_nube.values.tolist(),
                    }
                    if URL_NUBE:
                        requests.post(URL_NUBE, json=payload, timeout=60)
                    st.success(f"¡Archivos de Full procesados correctamente!")
                except Exception as e:
                    st.error(f"Error al guardar Full en la nube: {e}")

    st.title(f"🛒 Gestión de Tienda Full - {mes_seleccionado_full} (2026)")
    df_rubros_26 = st.session_state.full_2026.get(mes_seleccionado_full, pd.DataFrame())

    if not df_rubros_26.empty:
        if "Codigo" in df_rubros_26.columns and "Rubro" in df_rubros_26.columns and "Cantidad" in df_rubros_26.columns:
            df_rubros_sum = (
                df_rubros_26.groupby(["Codigo", "Rubro"])["Cantidad"]
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
            st.warning("El archivo no tiene las columnas exactas 'Codigo', 'Rubro' y 'Cantidad'. Mostrando datos generales:")
            st.dataframe(df_rubros_26, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay cierres de Tienda Full cargados para el mes de **{mes_seleccionado_full}**. Subí tus planillas desde el panel lateral izquierdo.")

elif menu_principal == "📦 BOXES":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Seleccionar Mes (Boxes)")
    mes_seleccionado_boxes = st.sidebar.selectbox(
        "Mes Boxes", meses_lista, key="mes_boxes_trabajo"
    )

    sheet_boxes_26 = f"boxes_{mes_seleccionado_boxes.lower()}_2026"

    if (
        mes_seleccionado_boxes not in st.session_state.boxes_2026
        or st.session_state.boxes_2026[mes_seleccionado_boxes].empty
    ):
        df_nube_boxes = cargar_desd_nube(sheet_boxes_26)
        if not df_nube_boxes.empty:
            st.session_state.boxes_2026[mes_seleccionado_boxes] = df_nube_boxes

    if st.sidebar.button("🔄 Recargar Boxes desde la Nube"):
        st.session_state.boxes_2026.pop(mes_seleccionado_boxes, None)
        df_nube_boxes = cargar_desd_nube(sheet_boxes_26)
        if not df_nube_boxes.empty:
            st.session_state.boxes_2026[mes_seleccionado_boxes] = df_nube_boxes
        st.rerun()

    # PANEL ADMIN (Subir Excel Boxes)
    with st.sidebar.expander("🔐 Panel Admin (Subir Excel Boxes)"):
        archivos_boxes = st.file_uploader(
            f"Subir Planillas Boxes (2026)",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            key=f"uploader_boxes_2026_{mes_seleccionado_boxes}",
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
                st.session_state.boxes_2026[mes_seleccionado_boxes] = df_boxes_concatenado

                try:
                    df_para_nube = df_boxes_concatenado.copy().fillna("").astype(str)
                    payload = {
                        "month": sheet_boxes_26,
                        "headers": df_para_nube.columns.tolist(),
                        "rows": df_para_nube.values.tolist(),
                    }
                    if URL_NUBE:
                        requests.post(URL_NUBE, json=payload, timeout=60)
                    st.success(f"¡Archivos de Boxes procesados correctamente!")
                except Exception as e:
                    st.error(f"Error al guardar Boxes en la nube: {e}")

    df_b26 = st.session_state.boxes_2026.get(mes_seleccionado_boxes, pd.DataFrame())

    st.subheader(f"📦 Gestión y Ventas de BOXES - {mes_seleccionado_boxes} (2026)")

    if not df_b26.empty:
        st.success(f"✅ Registros de Boxes cargados: {len(df_b26)} filas")
        st.markdown("---")
        st.dataframe(df_b26, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros de Boxes cargados para el mes de **{mes_seleccionado_boxes}**. Subí tus planillas desde el panel lateral izquierdo.")

elif menu_principal == "🎯 +YPF":
    st.sidebar.markdown("---")
    st.sidebar.header("🎯 Configuración YPF")
    mes_seleccionado_ypf = st.sidebar.selectbox(
        "Mes YPF", meses_lista, key="mes_ypf_trabajo"
    )

    st.subheader(f"🎯 Tablero de Exigencias YPF - {mes_seleccionado_ypf} (2026)")
    st.markdown("Control centralizado de objetivos, cumplimiento y puntajes de la estación.")

    # Extracción automática de Comida y Cafetería desde Tienda Full si existe
    unidades_comida_real_calculado = 0
    try:
        if "full_2026" in st.session_state and mes_seleccionado_ypf in st.session_state.full_2026:
            df_full_temp = st.session_state.full_2026[mes_seleccionado_ypf]
            if "Rubro" in df_full_temp.columns and "Cantidad" in df_full_temp.columns:
                mask_comida = df_full_temp["Rubro"].str.contains("Comida|Cafeteria|Cafetería", case=False, na=False)
                unidades_comida_real_calculado = int(df_full_temp.loc[mask_comida, "Cantidad"].sum())
    except Exception:
        unidades_comida_real_calculado = 0

    if unidades_comida_real_calculado == 0:
        unidades_comida_real_calculado = 3674  # Valor de referencia por defecto si no hay datos cargados

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

    st.markdown("### 📋 Planilla de Objetivos e Indicadores")
    st.info("💡 El valor **Real** de *Unidades Comida y Cafetería* se actualiza automáticamente según lo que cargues en la sección de **Tienda Full**.")

    df_ypf_editado = st.data_editor(
        df_ypf,
        use_container_width=True,
        hide_index=True,
        key=f"editor_ypf_{mes_seleccionado_ypf}"
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
