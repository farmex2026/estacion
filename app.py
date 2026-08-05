import streamlit as st
import pandas as pd
import io
import calendar

# Configuración inicial de la página
st.set_page_config(page_title="Gestión Estación YPF", layout="wide")

# Totales oficiales de venta 2025 por mes (Playa / Combustibles)
TOTALES_2025 = {
    "Enero": 291507.0,
    "Febrero": 315834.0,
    "Marzo": 381244.0,
    "Abril": 395330.0,
    "Mayo": 534107.0,
    "Junio": 505966.0,
    "Julio": 523352.0,
    "Agosto": 524135.0,
    "Septiembre": 499462.0,
    "Octubre": 535096.0,
    "Noviembre": 510923.0,
    "Diciembre": 562513.0
}

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

def dias_en_mes(nombre_mes, anio=2026):
    meses_dict = {
        "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4,
        "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
        "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
    }
    m = meses_dict.get(nombre_mes, 1)
    return calendar.monthrange(anio, m)[1]

# ==========================================
# PRECARGA EXACTA DE DATOS 2026 (Enero a Julio)
# ==========================================

# 1. ENERO 2026
if "Enero" not in st.session_state["combustibles_2026"]:
    datos_enero = [
        ("01-01", 289.0, 559.0, 2314.0, 4078.0), ("02-01", 468.0, 726.0, 3539.0, 8425.0),
        ("03-01", 360.0, 736.0, 3328.0, 6512.0), ("04-01", 126.0, 500.0, 3046.0, 5665.0),
        ("05-01", 1732.0, 1056.0, 4153.0, 8399.0), ("06-01", 734.0, 948.0, 3770.0, 6936.0),
        ("07-01", 1016.0, 841.0, 4089.0, 8932.0), ("08-01", 1235.0, 927.0, 5930.0, 9264.0),
        ("09-01", 1499.0, 1615.0, 4976.0, 8849.0), ("10-01", 1967.0, 600.0, 3011.0, 7060.0),
        ("11-01", 180.0, 601.0, 6071.0, 3176.0), ("12-01", 659.0, 1217.0, 4874.0, 8989.0),
        ("13-01", 404.0, 1200.0, 3996.0, 7951.0), ("14-01", 1753.0, 1569.0, 5476.0, 9277.0),
        ("15-01", 1317.0, 1214.0, 5466.0, 11001.0), ("16-01", 443.0, 1153.0, 5075.0, 9440.0),
        ("17-01", 1611.0, 1385.0, 4219.0, 7934.0), ("18-01", 111.0, 681.0, 3441.0, 6200.0),
        ("19-01", 425.0, 1146.0, 5098.0, 8494.0), ("20-01", 784.0, 745.0, 3968.0, 8182.0),
        ("21-01", 1725.0, 1129.0, 4048.0, 7684.0), ("22-01", 1209.0, 1173.0, 5051.0, 9307.0),
        ("23-01", 1191.0, 1509.0, 4825.0, 9743.0), ("24-01", 707.0, 820.0, 3953.0, 6747.0),
        ("25-01", 142.0, 286.0, 3017.0, 6588.0), ("26-01", 1205.0, 1112.0, 5915.0, 8122.0),
        ("27-01", 564.0, 981.0, 3805.0, 7835.0), ("28-01", 597.0, 1431.0, 4248.0, 8578.0),
        ("29-01", 1978.0, 1330.0, 4516.0, 9218.0), ("30-01", 1166.0, 1898.0, 4992.0, 10749.0),
        ("31-01", 1477.0, 1112.0, 4705.0, 9037.0)
    ]
    st.session_state["combustibles_2026"]["Enero"] = pd.DataFrame(datos_enero, columns=["Fecha", "Diesel", "Infinia Diesel", "Infinia", "Super"])

# 2. FEBRERO 2026
if "Febrero" not in st.session_state["combustibles_2026"]:
    datos_febrero = [
        ("01-02", 218.0, 837.0, 3916.0, 7458.0), ("02-02", 1218.0, 1035.0, 4856.0, 9821.0),
        ("03-02", 459.0, 1137.0, 4839.0, 8968.0), ("04-02", 1829.0, 1215.0, 4107.0, 8691.0),
        ("05-02", 644.0, 1009.0, 4618.0, 9623.0), ("06-02", 624.0, 1492.0, 4948.0, 9538.0),
        ("07-02", 463.0, 383.0, 2696.0, 4315.0), ("08-02", 188.0, 794.0, 3521.0, 6484.0),
        ("09-02", 915.0, 804.0, 5422.0, 8984.0), ("10-02", 981.0, 1168.0, 4461.0, 9442.0),
        ("11-02", 674.0, 1153.0, 4721.0, 8640.0), ("12-02", 1101.0, 1224.0, 5711.0, 10366.0),
        ("13-02", 448.0, 1848.0, 6713.0, 11718.0), ("14-02", 1873.0, 1031.0, 4417.0, 8755.0),
        ("15-02", 130.0, 522.0, 3596.0, 6137.0), ("16-02", 77.0, 648.0, 3733.0, 6964.0),
        ("17-02", 134.0, 199.0, 3584.0, 5727.0), ("18-02", 485.0, 1033.0, 4895.0, 10577.0),
        ("19-02", 340.0, 1027.0, 4845.0, 9502.0), ("20-02", 1271.0, 1594.0, 5489.0, 10030.0),
        ("21-02", 767.0, 551.0, 4658.0, 9204.0), ("22-02", 279.0, 644.0, 3907.0, 7183.0),
        ("23-02", 1374.0, 1187.0, 4811.0, 9157.0), ("24-02", 1046.0, 1363.0, 4725.0, 9564.0),
        ("25-02", 942.0, 1343.0, 3879.0, 9385.0), ("26-02", 1204.0, 883.0, 5263.0, 10062.0),
        ("27-02", 605.0, 1245.0, 6659.0, 11572.0), ("28-02", 1962.0, 1251.0, 5245.0, 11187.0)
    ]
    st.session_state["combustibles_2026"]["Febrero"] = pd.DataFrame(datos_febrero, columns=["Fecha", "Diesel", "Infinia Diesel", "Infinia", "Super"])

# 3. MARZO 2026
if "Marzo" not in st.session_state["combustibles_2026"]:
    datos_marzo = [
        ("01-03", 81.0, 729.0, 4746.0, 9341.0), ("02-03", 634.0, 1343.0, 6910.0, 10675.0),
        ("03-03", 1009.0, 1584.0, 5699.0, 10824.0), ("04-03", 901.0, 1591.0, 5548.0, 10058.0),
        ("05-03", 1326.0, 1333.0, 5153.0, 11109.0), ("06-03", 1266.0, 1354.0, 6266.0, 10508.0),
        ("07-03", 875.0, 647.0, 4623.0, 8949.0), ("08-03", 319.0, 417.0, 3966.0, 8140.0),
        ("09-03", 1382.0, 1231.0, 7037.0, 11482.0), ("10-03", 1390.0, 1644.0, 5748.0, 10438.0),
        ("11-03", 1927.0, 1135.0, 5737.0, 10586.0), ("12-03", 1561.0, 1568.0, 5945.0, 10827.0),
        ("13-03", 642.0, 1166.0, 5368.0, 10830.0), ("14-03", 1431.0, 1205.0, 5319.0, 9906.0),
        ("15-03", 149.0, 920.0, 3496.0, 7496.0), ("16-03", 1114.0, 1120.0, 6524.0, 10223.0),
        ("17-03", 944.0, 1195.0, 4057.0, 9091.0), ("18-03", 1198.0, 1710.0, 4746.0, 10820.0),
        ("19-03", 595.0, 1172.0, 6260.0, 10722.0), ("20-03", 1929.0, 1428.0, 5843.0, 10997.0),
        ("21-03", 1040.0, 619.0, 5259.0, 9503.0), ("22-03", 143.0, 601.0, 3584.0, 6801.0),
        ("23-03", 464.0, 755.0, 4284.0, 7944.0), ("24-03", 328.0, 646.0, 3785.0, 6603.0),
        ("25-03", 738.0, 1285.0, 5049.0, 8476.0), ("26-03", 838.0, 896.0, 5227.0, 9669.0),
        ("27-03", 1221.0, 1524.0, 5339.0, 11494.0), ("28-03", 456.0, 1094.0, 4565.0, 8344.0),
        ("29-03", 162.0, 971.0, 4400.0, 7474.0), ("30-03", 1214.0, 1183.0, 5730.0, 11081.0),
        ("31-03", 895.0, 1421.0, 5085.0, 9789.0)
    ]
    st.session_state["combustibles_2026"]["Marzo"] = pd.DataFrame(datos_marzo, columns=["Fecha", "Diesel", "Infinia Diesel", "Infinia", "Super"])

# 4. ABRIL 2026
if "Abril" not in st.session_state["combustibles_2026"]:
    datos_abril = [
        ("01-04", 1629.0, 2448.0, 6568.0, 13754.0), ("02-04", 289.0, 1313.0, 5689.0, 9694.0),
        ("03-04", 389.0, 742.0, 4155.0, 7488.0), ("04-04", 855.0, 501.0, 3924.0, 7271.0),
        ("05-04", 273.0, 462.0, 4107.0, 7172.0), ("06-04", 320.0, 1040.0, 5125.0, 10936.0),
        ("07-04", 1614.0, 1226.0, 4671.0, 10346.0), ("08-04", 675.0, 977.0, 4893.0, 10502.0),
        ("09-04", 724.0, 1281.0, 6328.0, 12000.0), ("10-04", 1497.0, 1431.0, 6391.0, 12460.0),
        ("11-04", 955.0, 1165.0, 3705.0, 9366.0), ("12-04", 377.0, 785.0, 4323.0, 8576.0),
        ("13-04", 840.0, 1182.0, 5348.0, 10559.0), ("14-04", 960.0, 5414.0, 5414.0, 9805.0),
        ("15-04", 922.0, 1184.0, 4977.0, 9161.0), ("16-04", 1767.0, 1103.0, 5163.0, 12050.0),
        ("17-04", 735.0, 1629.0, 5955.0, 11420.0), ("18-04", 1323.0, 856.0, 4612.0, 9666.0),
        ("19-04", 231.0, 420.0, 4004.0, 7478.0), ("20-04", 525.0, 1009.0, 5767.0, 10718.0),
        ("21-04", 862.0, 1491.0, 4614.0, 9125.0), ("22-04", 556.0, 1672.0, 5019.0, 10029.0),
        ("23-04", 2653.0, 672.0, 4870.0, 9571.0), ("24-04", 926.0, 1178.0, 5625.0, 11080.0),
        ("25-04", 406.0, 796.0, 4809.0, 8534.0), ("26-04", 354.0, 3906.0, 3906.0, 6770.0),
        ("27-04", 1478.0, 1627.0, 5272.0, 10728.0), ("28-04", 579.0, 1291.0, 4480.0, 9608.0),
        ("29-04", 773.0, 1084.0, 5572.0, 9579.0), ("30-04", 1933.0, 1934.0, 7783.0, 11802.0)
    ]
    st.session_state["combustibles_2026"]["Abril"] = pd.DataFrame(datos_abril, columns=["Fecha", "Diesel", "Infinia Diesel", "Infinia", "Super"])

# 5. MAYO 2026
if "Mayo" not in st.session_state["combustibles_2026"]:
    datos_mayo = [
        ("01-05", 422.0, 1026.0, 4370.0, 8935.0), ("02-05", 1309.0, 377.0, 4146.0, 7968.0),
        ("03-05", 225.0, 934.0, 3632.0, 8020.0), ("04-05", 938.0, 1331.0, 5263.0, 8832.0),
        ("05-05", 1652.0, 2133.0, 4445.0, 9712.0), ("06-05", 517.0, 1060.0, 4590.0, 10191.0),
        ("07-05", 1434.0, 1120.0, 5201.0, 10012.0), ("08-05", 1990.0, 1231.0, 6730.0, 11266.0),
        ("09-05", 817.0, 614.0, 4191.0, 8538.0), ("10-05", 239.0, 570.0, 4559.0, 8743.0),
        ("11-05", 983.0, 1386.0, 5623.0, 11832.0), ("12-05", 1747.0, 1268.0, 5168.0, 9302.0),
        ("13-05", 2206.0, 1333.0, 5181.0, 9662.0), ("14-05", 562.0, 2110.0, 5930.0, 11100.0),
        ("15-05", 1168.0, 1383.0, 5845.0, 10560.0), ("16-05", 1236.0, 1098.0, 4171.0, 9945.0),
        ("17-05", 305.0, 549.0, 3930.0, 7271.0), ("18-05", 1845.0, 1085.0, 4892.0, 9445.0),
        ("19-05", 977.0, 1356.0, 4431.0, 9577.0), ("20-05", 1607.0, 1119.0, 5235.0, 9208.0),
        ("21-05", 1821.0, 1318.0, 5108.0, 9815.0), ("22-05", 1519.0, 1553.0, 5905.0, 12233.0),
        ("23-05", 852.0, 1094.0, 5363.0, 7905.0), ("24-05", 201.0, 612.0, 3142.0, 6907.0),
        ("25-05", 238.0, 1034.0, 4874.0, 6707.0), ("26-05", 1225.0, 1561.0, 4351.0, 8880.0),
        ("27-05", 1513.0, 1417.0, 4791.0, 9769.0), ("28-05", 1426.0, 1364.0, 5769.0, 10495.0),
        ("29-05", 1535.0, 991.0, 7008.0, 11394.0), ("30-05", 1395.0, 691.0, 4149.0, 9804.0),
        ("31-05", 768.0, 698.0, 4173.0, 7604.0)
    ]
    st.session_state["combustibles_2026"]["Mayo"] = pd.DataFrame(datos_mayo, columns=["Fecha", "Diesel", "Infinia Diesel", "Infinia", "Super"])

# 6. JUNIO 2026
if "Junio" not in st.session_state["combustibles_2026"]:
    datos_junio = [
        ("01-06", 1617.0, 1157.0, 5418.0, 9583.0), ("02-06", 932.0, 1399.0, 4545.0, 7929.0),
        ("03-06", 891.0, 1499.0, 5679.0, 10770.0), ("04-06", 1119.0, 1077.0, 5289.0, 10904.0),
        ("05-06", 1472.0, 1256.0, 5271.0, 9514.0), ("06-06", 2028.0, 729.0, 4499.0, 8741.0),
        ("07-06", 204.0, 827.0, 3950.0, 7726.0), ("08-06", 516.0, 1177.0, 4557.0, 10470.0),
        ("09-06", 1551.0, 1278.0, 5718.0, 9175.0), ("10-06", 1034.0, 1188.0, 6571.0, 11773.0),
        ("11-06", 1152.0, 1534.0, 5819.0, 10913.0), ("12-06", 2021.0, 1495.0, 5723.0, 10970.0),
        ("13-06", 1038.0, 823.0, 4544.0, 8974.0), ("14-06", 393.0, 485.0, 4236.0, 7129.0),
        ("15-06", 300.0, 542.0, 4669.0, 7414.0), ("16-06", 1163.0, 1098.0, 5400.0, 8524.0),
        ("17-06", 712.0, 1050.0, 4980.0, 9175.0), ("18-06", 1154.0, 1411.0, 4532.0, 10865.0),
        ("19-06", 1400.0, 1420.0, 5602.0, 11701.0), ("20-06", 685.0, 794.0, 5305.0, 8565.0),
        ("21-06", 151.0, 429.0, 3999.0, 6716.0), ("22-06", 739.0, 927.0, 4545.0, 8669.0),
        ("23-06", 954.0, 1072.0, 4681.0, 9387.0), ("24-06", 1973.0, 1241.0, 5039.0, 8849.0),
        ("25-06", 764.0, 1466.0, 6059.0, 11293.0), ("26-06", 1899.0, 1449.0, 6085.0, 10768.0),
        ("27-06", 1734.0, 694.0, 4638.0, 9675.0), ("28-06", 194.0, 475.0, 3669.0, 7076.0),
        ("29-06", 1707.0, 853.0, 4513.0, 8794.0), ("30-06", 627.0, 1334.0, 5096.0, 9203.0)
    ]
    st.session_state["combustibles_2026"]["Junio"] = pd.DataFrame(datos_junio, columns=["Fecha", "Diesel", "Infinia Diesel", "Infinia", "Super"])

# 7. JULIO 2026
if "Julio" not in st.session_state["combustibles_2026"]:
    datos_julio = [
        ("01-07", 1760.0, 1208.0, 5884.0, 9886.0), ("02-07", 1004.0, 2021.0, 5087.0, 10355.0),
        ("03-07", 964.0, 1465.0, 5647.0, 10817.0), ("04-07", 946.0, 1398.0, 4968.0, 10187.0),
        ("05-07", 165.0, 849.0, 4134.0, 6840.0), ("06-07", 769.0, 915.0, 4951.0, 9306.0),
        ("07-07", 1859.0, 950.0, 5879.0, 9264.0), ("08-07", 953.0, 1083.0, 5636.0, 10848.0),
        ("09-07", 235.0, 1156.0, 4778.0, 9927.0), ("10-07", 884.0, 1066.0, 5523.0, 9940.0),
        ("11-07", 1231.0, 643.0, 4229.0, 7804.0), ("12-07", 121.0, 625.0, 3496.0, 6253.0),
        ("13-07", 737.0, 1486.0, 4878.0, 9448.0), ("14-07", 692.0, 718.0, 5060.0, 8836.0),
        ("15-07", 1342.0, 854.0, 4885.0, 7491.0), ("16-07", 548.0, 1524.0, 5049.0, 9267.0),
        ("17-07", 866.0, 1078.0, 6376.0, 10919.0), ("18-07", 1304.0, 736.92, 7100.0, 3932.0),
        ("19-07", 0.0, 283.0, 2552.0, 5846.0), ("20-07", 166.0, 1135.0, 3106.0, 8297.0),
        ("21-07", 1098.0, 947.0, 4623.0, 9115.0), ("22-07", 333.0, 830.0, 4702.0, 8891.0),
        ("23-07", 929.0, 1210.0, 5926.0, 9516.0), ("24-07", 787.0, 1376.0, 4984.0, 9747.0),
        ("25-07", 1288.0, 848.8, 4594.0, 8334.0), ("26-07", 152.0, 861.19, 3892.0, 6716.0),
        ("27-07", 1248.0, 882.23, 3782.0, 7511.0), ("28-07", 622.0, 1113.0, 5123.0, 8511.0),
        ("29-07", 700.0, 1248.0, 4026.0, 8863.0), ("30-07", 513.0, 1386.0, 4932.0, 8669.0),
        ("31-07", 1246.0, 1287.0, 5502.0, 9710.0)
    ]
    st.session_state["combustibles_2026"]["Julio"] = pd.DataFrame(datos_julio, columns=["Fecha", "Diesel", "Infinia Diesel", "Infinia", "Super"])

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

def procesar_combustibles_df(df, nombre_mes="Enero", anio=2026):
    if df.empty:
        return 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, df, 0.0
    
    df.columns = [str(c).strip() for c in df.columns]
    cols_map = {c.lower(): c for c in df.columns}
    
    vol_super = 0.0
    vol_infinia_nafta = 0.0
    vol_diesel_500 = 0.0
    vol_infinia_diesel = 0.0
    despachos = len(df)
    
    col_super, col_inf_nafta, col_inf_diesel, col_diesel = None, None, None, None
    
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
    
    # Cálculo de Proyección Mensual
    dias_totales = dias_en_mes(nombre_mes, anio)
    promedio_diario = (vol_total / despachos) if despachos > 0 else 0.0
    vol_proyectado = promedio_diario * dias_totales
    
    return vol_total, despachos, vol_super, mix_super, vol_infinia_nafta, mix_infinia_nafta, vol_diesel_500, mix_diesel_500, vol_infinia_diesel, mix_infinia_diesel, df, vol_proyectado

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
    st.title("📊 Dashboard General (2026 vs 2025) y Proyecciones")
    st.markdown("Resumen consolidado y proyecciones mensuales estimadas para todos los meses de 2026.")
    
    # Tabla resumen anual con proyecciones para todos los meses
    data_resumen = []
    tot_vol_2026_acum = 0.0
    tot_vol_2025_acum = 0.0
    
    for m in meses_lista:
        df_m = st.session_state["combustibles_2026"].get(m, pd.DataFrame())
        vol_real_m = 0.0
        proj_m = 0.0
        if not df_m.empty:
            res_m = procesar_combustibles_df(df_m, nombre_mes=m, anio=2026)
            vol_real_m = res_m[0]
            proj_m = res_m[11]
            tot_vol_2026_acum += vol_real_m
        
        vol_25_m = TOTALES_2025.get(m, 0.0)
        tot_vol_2025_acum += vol_25_m
        
        # Si no hay datos detallados para el mes pero hay un estimado o proyección basada en 2025 o promedio
        if proj_m == 0.0:
            proj_m = vol_25_m * 1.05 # Estimación conservadora si no hay datos cargados aún
            
        data_resumen.append({
            "Mes": m,
            "Volumen Real 2026 (L)": vol_real_m,
            "Proyección Mensual 2026 (L)": proj_m,
            "Volumen 2025 (Oficial) (L)": vol_25_m
        })
        
    df_resumen_anual = pd.DataFrame(data_resumen)
    
    st.markdown("### 📈 Tabla Resumen y Proyección por Mes (2026)")
    # Mostrar con formato legible
    st.dataframe(df_resumen_anual.style.format({
        "Volumen Real 2026 (L)": "{:,.0f}",
        "Proyección Mensual 2026 (L)": "{:,.0f}",
        "Volumen 2025 (Oficial) (L)": "{:,.0f}"
    }), use_container_width=True, hide_index=True)

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
    vol_25_oficial = TOTALES_2025.get(mes_comb, 0.0)

    res_26 = procesar_combustibles_df(df_comb_26, nombre_mes=mes_comb, anio=2026)
    vol_26, desp_26, sup_26, mix_sup_26, inf_n_26, mix_inf_n_26, d500_26, mix_d500_26, inf_d_26, mix_inf_d_26, df_proc_26, proj_26 = res_26

    if not df_comb_25.empty:
        res_25 = procesar_combustibles_df(df_comb_25, nombre_mes=mes_comb, anio=2025)
        vol_25 = res_25[0]
        desp_25 = res_25[1]
    else:
        vol_25 = vol_25_oficial
        desp_25 = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        diff_vol = ((vol_26 - vol_25) / vol_25 * 100) if vol_25 > 0 else 0
        st.metric("📦 Volumen Acumulado (L)", f"{formato_arg(vol_26, 0)} L", delta=f"{diff_vol:+.2f}% vs 2025 ({formato_arg(vol_25, 0)} L)")
    with col2:
        st.metric(f"🔮 Proyección Total Mes ({mes_comb})", f"{formato_arg(proj_26, 0)} L", delta=f"Días del mes: {dias_en_mes(mes_comb, anio_comb)}")
    with col3:
        diff_desp = ((desp_26 - desp_25) / desp_25 * 100) if desp_25 > 0 else 0
        st.metric("🔢 Registros / Despachos", formato_arg(desp_26), delta=f"{diff_desp:+.2f}% vs 2025" if desp_25 > 0 else "vs 2025 (Oficial)")

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
    st.markdown(f"### 📋 Detalle de Registros - {mes_comb} {anio_comb}")
    df_activo_proc = df_proc_26 if anio_comb == 2026 else df_comb_25
    if not df_activo_proc.empty:
        st.dataframe(df_activo_proc, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros detallados cargados para {mes_comb} {anio_comb} (Se está utilizando el total mensual oficial de 2025: {formato_arg(vol_25_oficial, 0)} L).")

elif menu_principal == "🛒 TIENDA FULL":
    st.title("🛒 Tienda Full")
    st.info("Módulo de gestión y turnos de Tienda Full.")

elif menu_principal == "📦 BOXES":
    st.title("📦 BOXES")
    st.info("Módulo de Boxes e inventario.")

elif menu_principal == "🎯 +YPF":
    st.title("🎯 Tablero de Exigencias YPF")
    st.info("Módulo de cumplimiento y objetivos.")
