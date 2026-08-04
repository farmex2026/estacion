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
    if f"full_calendar_{anio}" not in st.session_state:
        st.session_state[f"full_calendar_{anio}"] = {}
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

# Función para limpiar y evitar nombres de columnas duplicados
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

# Función para limpiar números y preparar el DataFrame de un turno
def procesar_turno_full(df):
    if df.empty:
        return df
    df = limpiar_columnas(df)
    # Detectar columna de rubro/concepto
    col_rubro = df.columns[0]
    for col in df.columns:
        c_low = str(col).lower()
        if any(k in c_low for k in ['rubro', 'descripcion', 'concepto', 'producto', 'item', 'detalle']):
            col_rubro = col
            break
    
    # Limpiar columnas numéricas
    for col in df.columns:
        if col == col_rubro:
            continue
        serie_str = df[col].astype(str).str.strip()
        temp_col = serie_str.str.replace('$', '', regex=False).str.replace(' ', '', regex=False)
        temp_col = temp_col.apply(lambda x: x.replace('.', '').replace(',', '.') if (',' in x and '.' in x) or (x.count('.') > 1) or (',' in x and x.find(',') > x.find('.')) else x.replace(',', '.'))
        converted = pd.to_numeric(temp_col, errors='coerce')
        if converted.notna().sum() > 0:
            df[col] = converted.fillna(0)
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

# ==========================================
# 3. TIENDA FULL (CALENDARIO POR DÍA Y TURNO)
# ==========================================
elif menu_principal == "🛒 TIENDA FULL":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Configuración de Mes y Año")
    mes_full = st.sidebar.selectbox("Mes Full", meses_lista, key="mes_full_sel")
    anio_full = st.sidebar.selectbox("Año Full", [2026, 2025], index=0, key="anio_full_sel")

    sheet_full_name = f"full_calendar_{mes_full.lower()}_{anio_full}"

    # Cargar datos iniciales desde nube si el session_state está vacío
    if mes_full not in st.session_state[f"full_calendar_{anio_full}"]:
        df_nube = cargar_desde_nube(sheet_full_name)
        if not df_nube.empty:
            st.session_state[f"full_calendar_{anio_full}"][mes_full] = df_nube
        else:
            st.session_state[f"full_calendar_{anio_full}"][mes_full] = pd.DataFrame(columns=["Dia", "Turno", "ID_Planilla", "Rubro", "Valor"])

    st.sidebar.markdown("---")
    st.sidebar.header("📋 Carga Rápida por Día / Turno")
    
    dia_sel = st.sidebar.selectbox("Día del mes", list(range(1, 32)), key=f"dia_sel_{anio_full}_{mes_full}")
    turno_sel = st.sidebar.selectbox("Turno", ["Mañana", "Tarde"], key=f"turno_sel_{anio_full}_{mes_full}")
    id_planilla_default = f"{str(dia_sel).zfill(2)}-{mes_full.lower()}-15641"
    id_planilla_ingresado = st.sidebar.text_input("ID / Nombre Planilla", value=id_planilla_default, key=f"id_planilla_{anio_full}_{mes_full}")
    
    st.sidebar.info("Copiá la tabla de tu archivo `.htm` y pegala acá abajo:")
    texto_turno = st.sidebar.text_area("Pegar datos del turno (Ctrl + V)", height=120, key=f"txt_turno_{anio_full}_{mes_full}")

    if st.sidebar.button("💾 Guardar / Actualizar este Turno", key=f"btn_guardar_turno_{anio_full}_{mes_full}"):
        if texto_turno.strip():
            try:
                df_nuevo = pd.read_csv(io.StringIO(texto_turno), sep=None, engine='python')
                df_nuevo = procesar_turno_full(df_nuevo)
                
                # Transformar a formato plano (melt o filas por rubro)
                col_rubro = df_nuevo.columns[0]
                cols_vals = [c for c in df_nuevo.columns if c != col_rubro]
                
                # Armar registros limpios
                df_melted = pd.melt(df_nuevo, id_vars=[col_rubro], value_vars=cols_vals, var_name="Metrica", value_name="Valor")
                df_melted.rename(columns={col_rubro: "Rubro"}, inplace=True)
                df_melted["Dia"] = dia_sel
                df_melted["Turno"] = turno_sel
                df_melted["ID_Planilla"] = id_planilla_ingresado
                
                # Asegurar valores numéricos
                df_melted["Valor"] = pd.to_numeric(df_melted["Valor"], errors='coerce').fillna(0)

                # Actualizar session_state (remover datos previos de ese mismo día y turno si existían y agregar los nuevos)
                df_actual = st.session_state[f"full_calendar_{anio_full}"][mes_full]
                if not df_actual.empty:
                    # Filtrar fuera el día y turno anterior para reemplazarlo
                    df_actual = df_actual[~((df_actual["Dia"] == dia_sel) & (df_actual["Turno"] == turno_sel))]
                    df_combinado = pd.concat([df_actual, df_melted], ignore_index=True)
                else:
                    df_combinado = df_melted

                st.session_state[f"full_calendar_{anio_full}"][mes_full] = df_combinado
                
                # Guardar automáticamente en la nube
                guardar_en_nube(sheet_full_name, df_combinado)
                st.sidebar.success(f"¡Turno {turno_sel} del Día {dia_sel} guardado con éxito!")
            except Exception as e:
                st.sidebar.error(f"Error al procesar el turno: {e}")
        else:
            st.sidebar.warning("El cuadro de texto está vacío.")

    if st.sidebar.button("🔄 Recargar desde la Nube", key=f"btn_recargar_full_{anio_full}_{mes_full}"):
        st.cache_data.clear()
        df_nube = cargar_desde_nube(sheet_full_name)
        if not df_nube.empty:
            st.session_state[f"full_calendar_{anio_full}"][mes_full] = df_nube
            st.sidebar.success("Datos actualizados desde la nube.")
            st.rerun()

    # Vista Principal de Tienda Full
    st.title(f"🛒 Tienda Full - Calendario de Ventas ({mes_full} {anio_full})")

    df_mes = st.session_state[f"full_calendar_{anio_full}"].get(mes_full, pd.DataFrame())

    if not df_mes.empty:
        st.markdown("### 📅 Resumen por Día y Turno")
        # Crear una tabla pivote para mostrar el calendario de ventas de forma clara
        try:
            # Agrupar por Día y Turno sumando la métrica principal o total
            df_resumen = df_mes.groupby(["Dia", "Turno", "ID_Planilla"], as_index=False)["Valor"].sum()
            st.dataframe(df_resumen, use_container_width=True, hide_index=True)
        except Exception as e:
            st.dataframe(df_mes, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay turnos cargados para {mes_full} {anio_full}. Utilizá la barra lateral para cargar los turnos Día por Día.")

    # Comparativa rápida 2026 vs 2025 en la misma vista de Full
    st.markdown("---")
    st.subheader(f"📊 Comparativa Mensual Full: 2026 vs 2025 ({mes_full})")
    
    df_26 = st.session_state["full_calendar_2026"].get(mes_full, pd.DataFrame())
    df_25 = st.session_state["full_calendar_2025"].get(mes_full, pd.DataFrame())
    
    tot_26 = df_26["Valor"].sum() if not df_26.empty and "Valor" in df_26.columns else 0
    tot_25 = df_25["Valor"].sum() if not df_25.empty and "Valor" in df_25.columns else 0
    
    diff_full = ((tot_26 - tot_25) / tot_25 * 100) if tot_25 > 0 else 0
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.metric(f"🛒 Total Full 2026 ({mes_full})", f"$ {formato_arg(tot_26, 2)}")
    with col_f2:
        st.metric(f"🛒 Total Full 2025 ({mes_full})", f"$ {formato_arg(tot_25, 2)}", delta=f"{diff_full:+.2f}% vs 2025")

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
