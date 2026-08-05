import streamlit as st
import pandas as pd
import io

# Configuración inicial de la página
st.set_page_config(page_title="Gestión Estación YPF", layout="wide")

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

# Precarga exacta de Junio 2026 (Total: 496.179 L)
if "Junio" not in st.session_state["combustibles_2026"]:
    datos_junio_2026 = [
        ("01-06", 1617.0, 1157.0, 5418.0, 9583.0),
        ("02-06", 932.0, 1399.0, 4545.0, 7929.0),
        ("03-06", 891.0, 1499.0, 5679.0, 10770.0),
        ("04-06", 1119.0, 1077.0, 5289.0, 10904.0),
        ("05-06", 1472.0, 1256.0, 5271.0, 9514.0),
        ("06-06", 2028.0, 729.0, 4499.0, 8741.0),
        ("07-06", 204.0, 827.0, 3950.0, 7726.0),
        ("08-06", 516.0, 1177.0, 4557.0, 10470.0),
        ("09-06", 1551.0, 1278.0, 5718.0, 9175.0),
        ("10-06", 1034.0, 1188.0, 6571.0, 11773.0),
        ("11-06", 1152.0, 1534.0, 5819.0, 10913.0),
        ("12-06", 2021.0, 1495.0, 5723.0, 10970.0),
        ("13-06", 1038.0, 823.0, 4544.0, 8974.0),
        ("14-06", 393.0, 485.0, 4236.0, 7129.0),
        ("15-06", 300.0, 542.0, 4669.0, 7414.0),
        ("16-06", 1163.0, 1098.0, 5400.0, 8524.0),
        ("17-06", 712.0, 1050.0, 4980.0, 9175.0),
        ("18-06", 1154.0, 1411.0, 4532.0, 10865.0),
        ("19-06", 1400.0, 1420.0, 5602.0, 11701.0),
        ("20-06", 685.0, 794.0, 5305.0, 8565.0),
        ("21-06", 151.0, 429.0, 3999.0, 6716.0),
        ("22-06", 739.0, 927.0, 4545.0, 8669.0),
        ("23-06", 954.0, 1072.0, 4681.0, 9387.0),
        ("24-06", 1973.0, 1241.0, 5039.0, 8849.0),
        ("25-06", 764.0, 1466.0, 6059.0, 11293.0),
        ("26-06", 1899.0, 1449.0, 6085.0, 10768.0),
        ("27-06", 1734.0, 694.0, 4638.0, 9675.0),
        ("28-06", 194.0, 475.0, 3669.0, 7076.0),
        ("29-06", 1707.0, 853.0, 4513.0, 8794.0),
        ("30-06", 627.0, 1334.0, 5096.0, 9203.0)
    ]
    st.session_state["combustibles_2026"]["Junio"] = pd.DataFrame(
        datos_junio_2026, 
        columns=["Fecha", "Diesel", "Infinia Diesel", "Infinia", "Super"]
    )

# Precarga exacta de Julio 2026 (Total: ~480.995 L)
if "Julio" not in st.session_state["combustibles_2026"]:
    datos_julio_2026 = [
        ("01-07", 1760.0, 1208.0, 5884.0, 9886.0),
        ("02-07", 1004.0, 2021.0, 5087.0, 10355.0),
        ("03-07", 964.0, 1465.0, 5647.0, 10817.0),
        ("04-07", 946.0, 1398.0, 4968.0, 10187.0),
        ("05-07", 165.0, 849.0, 4134.0, 6840.0),
        ("06-07", 769.0, 915.0, 4951.0, 9306.0),
        ("07-07", 1859.0, 950.0, 5879.0, 9264.0),
        ("08-07", 953.0, 1083.0, 5636.0, 10848.0),
        ("09-07", 235.0, 1156.0, 4778.0, 9927.0),
        ("10-07", 884.0, 1066.0, 5523.0, 9940.0),
        ("11-07", 1231.0, 643.0, 4229.0, 7804.0),
        ("12-07", 121.0, 625.0, 3496.0, 6253.0),
        ("13-07", 737.0, 1486.0, 4878.0, 9448.0),
        ("14-07", 692.0, 718.0, 5060.0, 8836.0),
        ("15-07", 1342.0, 854.0, 4885.0, 7491.0),
        ("16-07", 548.0, 1524.0, 5049.0, 9267.0),
        ("17-07", 866.0, 1078.0, 6376.0, 10919.0),
        ("18-07", 1304.0, 736.92, 7100.0, 3932.0),
        ("19-07", 0.0, 283.0, 2552.0, 5846.0),
        ("20-07", 166.0, 1135.0, 3106.0, 8297.0),
        ("21-07", 1098.0, 947.0, 4623.0, 9115.0),
        ("22-07", 333.0, 830.0, 4702.0, 8891.0),
        ("23-07", 929.0, 1210.0, 5926.0, 9516.0),
        ("24-07", 787.0, 1376.0, 4984.0, 9747.0),
        ("25-07", 1288.0, 848.8, 4594.0, 8334.0),
        ("26-07", 152.0, 861.19, 3892.0, 6716.0),
        ("27-07", 1248.0, 882.23, 3782.0, 7511.0),
        ("28-07", 622.0, 1113.0, 5123.0, 8511.0),
        ("29-07", 700.0, 1248.0, 4026.0, 8863.0),
        ("30-07", 513.0, 1386.0, 4932.0, 8669.0),
        ("31-07", 1246.0, 1287.0, 5502.0, 9710.0)
    ]
    st.session_state["combustibles_2026"]["Julio"] = pd.DataFrame(
        datos_julio_2026, 
        columns=["Fecha", "Diesel", "Infinia Diesel", "Infinia", "Super"]
    )

def leer_archivo_universal(uploaded_file):
    if uploaded_file is None:
        return pd.DataFrame()
    nombre = uploaded_file.name.lower()
    contenido_bytes = uploaded_file.read()
    if nombre.endswith(('.htm', '.html')):
        for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']:
            try:
                html_str = contenido_bytes.decode(encoding, errors='ignore')
                dfs = pd.read_html(io.StringIO(html_str))
                if dfs:
                    df_mas_grande = max(dfs, key=lambda d: d.shape[0] * d.shape[1])
                    if not df_mas_grande.empty:
                        return df_mas_grande
            except Exception:
                continue
    try:
        if nombre.endswith('.csv'):
            return pd.read_csv(io.BytesIO(contenido_bytes))
        elif nombre.endswith(('.xls', '.xlsx')):
            return pd.read_excel(io.BytesIO(contenido_bytes))
    except:
        pass
    for func in [pd.read_excel, pd.read_csv]:
        try:
            uploaded_file.seek(0)
            return func(uploaded_file)
        except:
            pass
    return pd.DataFrame()

def procesar_combustibles_df(df):
    if df.empty:
        return 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, df
    
    df.columns = [str(c).strip() for c in df.columns]
    cols_map = {c.lower(): c for c in df.columns}
    
    vol_super = 0.0
    vol_infinia_nafta = 0.0
    vol_diesel_500 = 0.0
    vol_infinia_diesel = 0.0
    despachos = len(df)
    
    col_super = None
    col_inf_nafta = None
    col_inf_diesel = None
    col_diesel = None
    
    # Búsqueda rigurosa de columnas
    for c_low, c_orig in cols_map.items():
        if c_low in ['super', 's xxi (super)', 's xxi']:
            col_super = c_orig
        elif c_low in ['infinia diesel', 'inf diesel', 'infinia d']:
            col_inf_diesel = c_orig
        elif c_low in ['infinia', 'infinia nafta']:
            col_inf_nafta = c_orig
        elif c_low in ['diesel', 'diesel 500', 'd500']:
            col_diesel = c_orig

    if not col_super:
        for c_low, c_orig in cols_map.items():
            if 'super' in c_low or 's xxi' in c_low:
                col_super = c_orig
                break
    if not col_inf_diesel:
        for c_low, c_orig in cols_map.items():
            if 'infinia' in c_low and 'diesel' in c_low:
                col_inf_diesel = c_orig
                break
    if not col_inf_nafta:
        for c_low, c_orig in cols_map.items():
            if 'infinia' in c_low and c_orig != col_inf_diesel:
                col_inf_nafta = c_orig
                break
    if not col_diesel:
        for c_low, c_orig in cols_map.items():
            if 'diesel' in c_low and c_orig != col_inf_diesel:
                col_diesel = c_orig
                break

    if col_super:
        vol_super = pd.to_numeric(df[col_super], errors='coerce').fillna(0).sum()
    if col_inf_nafta:
        vol_infinia_nafta = pd.to_numeric(df[col_inf_nafta], errors='coerce').fillna(0).sum()
    if col_inf_diesel:
        vol_infinia_diesel = pd.to_numeric(df[col_inf_diesel], errors='coerce').fillna(0).sum()
    if col_diesel:
        vol_diesel_500 = pd.to_numeric(df[col_diesel], errors='coerce').fillna(0).sum()

    vol_total = vol_super + vol_infinia_nafta + vol_diesel_500 + vol_infinia_diesel
    total_naftas = vol_super + vol_infinia_nafta
    mix_super = (vol_super / total_naftas * 100) if total_naftas > 0 else 0.0
    mix_infinia_nafta = (vol_infinia_nafta / total_naftas * 100) if total_naftas > 0 else 0.0
    
    total_diesel = vol_diesel_500 + vol_infinia_diesel
    mix_diesel_500 = (vol_diesel_500 / total_diesel * 100) if total_diesel > 0 else 0.0
    mix_infinia_diesel = (vol_infinia_diesel / total_diesel * 100) if total_diesel > 0 else 0.0
    
    return vol_total, despachos, vol_super, mix_super, vol_infinia_nafta, mix_infinia_nafta, vol_diesel_500, mix_diesel_500, vol_infinia_diesel, mix_infinia_diesel, df

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
    st.title("📊 Dashboard General (2026 vs 2025)")
    st.info("Vista general del rendimiento de la estación.")

elif menu_principal == "⛽ COMBUSTIBLES":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Configuración Combustibles")
    mes_comb = st.sidebar.selectbox("Mes Combustibles", meses_lista, index=5, key="mes_comb_sel") # Junio por defecto
    anio_comb = st.sidebar.selectbox("Año Destino", [2026, 2025], index=0, key="anio_comb_sel")

    st.sidebar.markdown("---")
    st.sidebar.header("📥 Subir Reporte Combustibles")
    archivo_comb = st.sidebar.file_uploader(f"Subir Excel/CSV Combustibles ({anio_comb})", type=["csv", "xlsx", "xls", "htm", "html"], key=f"uploader_comb_{anio_comb}_{mes_comb}")

    if st.sidebar.button("💾 Procesar y Guardar Combustibles", key=f"btn_guardar_comb_{anio_comb}_{mes_comb}"):
        if archivo_comb is not None:
            try:
                df_leido = leer_archivo_universal(archivo_comb)
                if not df_leido.empty:
                    st.session_state[f"combustibles_{anio_comb}"][mes_comb] = df_leido
                    st.sidebar.success("¡Combustibles procesados y guardados con éxito!")
                else:
                    st.sidebar.error("El archivo está vacío o no se pudo leer.")
            except Exception as e:
                st.sidebar.error(f"Error al procesar: {e}")
        else:
            st.sidebar.warning("Subí un archivo primero.")

    st.title(f"⛽ Combustibles - {mes_comb} ({anio_comb})")

    df_comb_26 = st.session_state["combustibles_2026"].get(mes_comb, pd.DataFrame())
    df_comb_25 = st.session_state["combustibles_2025"].get(mes_comb, pd.DataFrame())

    res_26 = procesar_combustibles_df(df_comb_26)
    vol_26, desp_26, sup_26, mix_sup_26, inf_n_26, mix_inf_n_26, d500_26, mix_d500_26, inf_d_26, mix_inf_d_26, df_proc_26 = res_26

    res_25 = procesar_combustibles_df(df_comb_25)
    vol_25, desp_25, sup_25, mix_sup_25, inf_n_25, mix_inf_n_25, d500_25, mix_d500_25, inf_d_25, mix_inf_d_25, df_proc_25 = res_25

    col1, col2 = st.columns(2)
    with col1:
        diff_vol = ((vol_26 - vol_25) / vol_25 * 100) if vol_25 > 0 else 0
        st.metric("📦 Volumen Total (L)", f"{formato_arg(vol_26, 0)} L", delta=f"{diff_vol:+.2f}% vs 2025 ({formato_arg(vol_25, 0)} L)")
    with col2:
        diff_desp = ((desp_26 - desp_25) / desp_25 * 100) if desp_25 > 0 else 0
        st.metric("🔢 Registros / Despachos", formato_arg(desp_26), delta=f"{diff_desp:+.2f}% vs 2025 ({formato_arg(desp_25)})")

    st.markdown("---")
    st.markdown("**🚗 Naftas**")
    cn1, cn2 = st.columns(2)
    with cn1:
        st.metric("🟢 S XXI (Super)", f"{formato_arg(sup_26, 0)} L", delta=f"Mix: {formato_arg(mix_sup_26, 2)}%")
    with cn2:
        st.metric("🟣 Infinia Nafta", f"{formato_arg(inf_n_26, 0)} L", delta=f"Mix: {formato_arg(mix_inf_n_26, 2)}%")

    st.markdown("---")
    st.markdown("**🚚 Diesels**")
    cd1, cd2 = st.columns(2)
    with cd1:
        st.metric("🟡 Diesel 500", f"{formato_arg(d500_26, 0)} L", delta=f"Mix: {formato_arg(mix_d500_26, 2)}%")
    with cd2:
        st.metric("🔵 Infinia Diesel", f"{formato_arg(inf_d_26, 0)} L", delta=f"Mix: {formato_arg(mix_inf_d_26, 2)}%")

    st.markdown("---")
    st.markdown(f"### 📋 Detalle de Registros - {anio_comb}")
    df_activo_proc = df_proc_26 if anio_comb == 2026 else df_proc_25
    if not df_activo_proc.empty:
        st.dataframe(df_activo_proc, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros de combustibles cargados para {mes_comb} {anio_comb}.")

elif menu_principal == "🛒 TIENDA FULL":
    st.title("🛒 Tienda Full")
    st.info("Módulo de gestión y turnos de Tienda Full.")

elif menu_principal == "📦 BOXES":
    st.title("📦 BOXES")
    st.info("Módulo de Boxes e inventario.")

elif menu_principal == "🎯 +YPF":
    st.title("🎯 Tablero de Exigencias YPF")
    st.info("Módulo de cumplimiento y objetivos.")
