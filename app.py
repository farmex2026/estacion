import streamlit as st
import pandas as pd
import requests
import json
import re
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

# Lector universal ultra robusto para HTM/HTML de YPF
def leer_archivo_universal(uploaded_file):
    if uploaded_file is None:
        return pd.DataFrame()
    
    nombre = uploaded_file.name.lower()
    contenido_bytes = uploaded_file.read()
    
    # 1. Si es HTML/HTM, intentamos parsearlo con BeautifulSoup y pandas
    if nombre.endswith(('.htm', '.html')):
        for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']:
            try:
                html_str = contenido_bytes.decode(encoding, errors='ignore')
                # Intentar leer tablas con pandas
                dfs = pd.read_html(io.StringIO(html_str))
                if dfs:
                    # Buscamos la tabla que tenga más filas o columnas (la que contiene los datos del turno)
                    df_mas_grande = max(dfs, key=lambda d: d.shape[0] * d.shape[1])
                    if not df_mas_grande.empty:
                        return df_mas_grande
            except Exception:
                continue
                
        # Si falló pd.read_html, intentamos extraer manualmente filas <tr> y celdas <td> con BeautifulSoup
        try:
            soup = BeautifulSoup(contenido_bytes, 'html.parser')
            filas_datos = []
            for tr in soup.find_all('tr'):
                cols = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cols:
                    filas_datos.append(cols)
            if filas_datos:
                max_len = max(len(f) for f in filas_datos)
                # Normalizar filas al mismo ancho
                filas_norm = [f + [''] * (max_len - len(f)) for f in filas_datos]
                return pd.DataFrame(filas_norm)
        except Exception:
            pass

    # 2. Si es Excel o CSV
    try:
        if nombre.endswith('.csv'):
            return pd.read_csv(io.BytesIO(contenido_bytes))
        elif nombre.endswith(('.xls', '.xlsx')):
            return pd.read_excel(io.BytesIO(contenido_bytes))
    except:
        pass
    
    # Intentos genéricos por si el formato difiere
    for func in [pd.read_excel, pd.read_csv]:
        try:
            uploaded_file.seek(0)
            return func(uploaded_file)
        except:
            pass

    return pd.DataFrame()

def procesar_turno_full(df):
    if df.empty:
        return {
            "Bebidas_Calientes": 0.0,
            "Comida_Elaborada_y_Envasada": 0.0,
            "Cigarrillos": 0.0
        }, "DataFrame vacío"
    
    df = limpiar_columnas(df)
    
    val_bebidas = 0.0
    val_comida = 0.0
    val_cigarros = 0.0
    
    encontrados = []
    
    for idx, row in df.iterrows():
        texto_fila = " ".join([str(val) for val in row.values]).lower()
        
        es_bebida = bool(re.search(r'02-232|bebidas?\s*caliente', texto_fila))
        es_comida = bool(re.search(r'02-241|02-198|comida\s*elaborad|comidas?\s*envasad', texto_fila))
        es_cigarro = bool(re.search(r'02-238|cigarrillo', texto_fila))
        
        if not (es_bebida or es_comida or es_cigarro):
            continue
            
        cantidad_encontrada = 0.0
        for col in df.columns:
            val_str = str(row[col]).strip()
            val_limpio = val_str.replace('$', '').replace(' ', '')
            if ',' in val_limpio and '.' in val_limpio:
                val_limpio = val_limpio.replace('.', '').replace(',', '.')
            elif ',' in val_limpio:
                val_limpio = val_limpio.replace(',', '.')
            
            try:
                num = float(val_limpio)
                if 0 <= num < 10000:
                    cantidad_encontrada = num
                    break 
            except:
                continue
                
        if es_bebida:
            val_bebidas += cantidad_encontrada
            encontrados.append(f"Bebidas Calientes: {cantidad_encontrada} (Fila: {texto_fila[:50]})")
        elif es_comida:
            val_comida += cantidad_encontrada
            encontrados.append(f"Comida: {cantidad_encontrada} (Fila: {texto_fila[:50]})")
        elif es_cigarro:
            val_cigarros += cantidad_encontrada
            encontrados.append(f"Cigarrillos: {cantidad_encontrada} (Fila: {texto_fila[:50]})")
            
    detalle_log = " | ".join(encontrados) if encontrados else "No se detectaron los códigos buscados en el archivo."
    return {
        "Bebidas_Calientes": val_bebidas,
        "Comida_Elaborada_y_Envasada": val_comida,
        "Cigarrillos": val_cigarros
    }, detalle_log

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

def formato_arg(val, decimales=0):
    try:
        if decimales > 0:
            s = f"{val:,.{decimales}f}"
        else:
            s = f"{val:,.0f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(val)

menu_principal = st.sidebar.selectbox(
    "Menú Principal", 
    ["📊 DASHBOARD", "⛽ COMBUSTIBLES", "🛒 TIENDA FULL", "📦 BOXES", "🎯 +YPF"]
)

if menu_principal == "📊 DASHBOARD":
    st.title("📊 Dashboard General")

elif menu_principal == "⛽ COMBUSTIBLES":
    st.title("⛽ COMBUSTIBLES")

elif menu_principal == "🛒 TIENDA FULL":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Configuración de Mes y Año")
    mes_full = st.sidebar.selectbox("Mes Full", meses_lista, key="mes_full_sel")
    anio_full = st.sidebar.selectbox("Año Full", [2026, 2025], index=0, key="anio_full_sel")

    sheet_full_name = f"full_calendar_{mes_full.lower()}_{anio_full}"

    if mes_full not in st.session_state[f"full_calendar_{anio_full}"]:
        df_nube = cargar_desde_nube(sheet_full_name)
        if not df_nube.empty:
            st.session_state[f"full_calendar_{anio_full}"][mes_full] = df_nube
        else:
            st.session_state[f"full_calendar_{anio_full}"][mes_full] = pd.DataFrame(columns=["Dia", "Turno", "ID_Planilla", "Bebidas_Calientes", "Comida_Elaborada_y_Envasada", "Cigarrillos"])

    st.sidebar.markdown("---")
    st.sidebar.header("📥 Subir Archivo de Turno (Full)")
    
    dia_sel = st.sidebar.selectbox("Día del mes", list(range(1, 32)), key=f"dia_sel_{anio_full}_{mes_full}")
    turno_sel = st.sidebar.selectbox("Turno", ["Mañana", "Tarde"], key=f"turno_sel_{anio_full}_{mes_full}")
    id_planilla_default = f"{str(dia_sel).zfill(2)}-{mes_full.lower()}-15641"
    id_planilla_ingresado = st.sidebar.text_input("Nº Planilla", value=id_planilla_default, key=f"id_planilla_{anio_full}_{mes_full}")
    
    archivo_turno = st.sidebar.file_uploader(
        f"Subir reporte del turno (.htm, Excel, CSV)", 
        type=["csv", "xlsx", "xls", "htm", "html"], 
        key=f"uploader_full_archivo_{anio_full}_{mes_full}"
    )

    if st.sidebar.button("💾 Procesar y Guardar este Turno", key=f"btn_guardar_turno_{anio_full}_{mes_full}"):
        if archivo_turno is not None:
            try:
                df_nuevo = leer_archivo_universal(archivo_turno)
                
                # Depuración visual para ver qué leyó el archivo
                if not df_nuevo.empty:
                    st.success(f"Archivo leído con éxito. Dimensiones de la tabla: {df_nuevo.shape[0]} filas x {df_nuevo.shape[1]} columnas.")
                else:
                    st.error("El archivo se leyó pero devolvió una tabla vacía.")
                
                resultado_turno, log_depuracion = procesar_turno_full(df_nuevo)
                st.info(f"🔍 **Log de lectura:** {log_depuracion}")
                
                nueva_fila = {
                    "Dia": dia_sel,
                    "Turno": turno_sel,
                    "ID_Planilla": id_planilla_ingresado,
                    "Bebidas_Calientes": resultado_turno["Bebidas_Calientes"],
                    "Comida_Elaborada_y_Envasada": resultado_turno["Comida_Elaborada_y_Envasada"],
                    "Cigarrillos": resultado_turno["Cigarrillos"]
                }
                
                df_actual = st.session_state[f"full_calendar_{anio_full}"][mes_full]
                if not df_actual.empty:
                    df_actual = df_actual[~((df_actual["Dia"] == dia_sel) & (df_actual["Turno"] == turno_sel))]
                    df_combinado = pd.concat([df_actual, pd.DataFrame([nueva_fila])], ignore_index=True)
                else:
                    df_combinado = pd.DataFrame([nueva_fila])
                
                df_combinado = df_combinado.sort_values(by=["Dia", "Turno"]).reset_index(drop=True)

                st.session_state[f"full_calendar_{anio_full}"][mes_full] = df_combinado
                guardar_en_nube(sheet_full_name, df_combinado)
                st.sidebar.success(f"¡Turno Día {dia_sel} ({turno_sel}) guardado correctamente!")
            except Exception as e:
                st.sidebar.error(f"Error crítico al procesar: {e}")
        else:
            st.sidebar.warning("Por favor, subí un archivo antes de guardar.")

    if st.sidebar.button("🔄 Recargar desde la Nube", key=f"btn_recargar_full_{anio_full}_{mes_full}"):
        st.cache_data.clear()
        df_nube = cargar_desde_nube(sheet_full_name)
        if not df_nube.empty:
            st.session_state[f"full_calendar_{anio_full}"][mes_full] = df_nube
            st.sidebar.success("Datos actualizados desde la nube.")
            st.rerun()

    st.title(f"🛒 Tienda Full - Calendario de Ventas ({mes_full} {anio_full})")

    df_mes = st.session_state[f"full_calendar_{anio_full}"].get(mes_full, pd.DataFrame())

    if not df_mes.empty:
        st.markdown(f"### 📅 Detalle Diario por Turno - {anio_full}")
        df_mostrar = df_mes.rename(columns={
            "Dia": "Día",
            "ID_Planilla": "Nº Planilla",
            "Bebidas_Calientes": "Bebidas Calientes (Unid.)",
            "Comida_Elaborada_y_Envasada": "Comida Elaborada y Envasada (Unid.)",
            "Cigarrillos": "Cigarrillos (Unid.)"
        })
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay turnos cargados para {mes_full} {anio_full}. Subí un archivo desde la barra lateral.")

    st.markdown("---")
    st.subheader(f"📊 Comparativa Mensual Full (Cantidades): 2026 vs 2025 ({mes_full})")
    
    df_26 = st.session_state["full_calendar_2026"].get(mes_full, pd.DataFrame())
    df_25 = st.session_state["full_calendar_2025"].get(mes_full, pd.DataFrame())
    
    beb_26 = df_26["Bebidas_Calientes"].sum() if not df_26.empty and "Bebidas_Calientes" in df_26.columns else 0
    beb_25 = df_25["Bebidas_Calientes"].sum() if not df_25.empty and "Bebidas_Calientes" in df_25.columns else 0
    diff_beb = ((beb_26 - beb_25) / beb_25 * 100) if beb_25 > 0 else 0

    comida_26 = df_26["Comida_Elaborada_y_Envasada"].sum() if not df_26.empty and "Comida_Elaborada_y_Envasada" in df_26.columns else 0
    comida_25 = df_25["Comida_Elaborada_y_Envasada"].sum() if not df_25.empty and "Comida_Elaborada_y_Envasada" in df_25.columns else 0
    diff_comida = ((comida_26 - comida_25) / comida_25 * 100) if comida_25 > 0 else 0

    cigar_26 = df_26["Cigarrillos"].sum() if not df_26.empty and "Cigarrillos" in df_26.columns else 0
    cigar_25 = df_25["Cigarrillos"].sum() if not df_25.empty and "Cigarrillos" in df_25.columns else 0
    diff_cigar = ((cigar_26 - cigar_25) / cigar_25 * 100) if cigar_25 > 0 else 0

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.metric(f"☕ Bebidas Calientes", f"{formato_arg(beb_26, 2)} unid.", delta=f"{diff_beb:+.2f}% vs 2025 ({formato_arg(beb_25, 2)})")
    with col_f2:
        st.metric(f"🍔 Comida Elaborada/Envasada", f"{formato_arg(comida_26, 2)} unid.", delta=f"{diff_comida:+.2f}% vs 2025 ({formato_arg(comida_25, 2)})")
    with col_f3:
        st.metric(f"🚬 Cigarrillos", f"{formato_arg(cigar_26, 2)} unid.", delta=f"{diff_cigar:+.2f}% vs 2025 ({formato_arg(cigar_25, 2)})")

elif menu_principal == "📦 BOXES":
    st.title("📦 BOXES")

elif menu_principal == "🎯 +YPF":
    st.title("🎯 +YPF")
