import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Control de Combustibles YPF", layout="wide"
)

st.title("⛽ Control de Combustibles YPF")

# 1. Selector de Meses en la parte superior
meses_disponibles = ["Julio 2026", "Junio 2026", "Mayo 2026", "Abril 2026"]
mes_seleccionado = st.selectbox("Seleccionar Mes:", meses_disponibles)

st.markdown(f"### 📊 Resumen, Mix y Proyecciones — {mes_seleccionado}")

# 2. Métricas Principales (Arriba)
col_a, col_b, col_c = st.columns(3)
with col_a:
  st.metric(label="Acumulado / Total 2026 (Mes actual)", value="480.998 L")
with col_b:
  st.metric(label="Promedio Diario Total", value="15.516 L/día")
with col_c:
  st.metric(label="Año 2025 (Comparativa)", value="523.352 L")

st.markdown("<br>", unsafe_allow_html=True)

# 3. Tarjetas de Nafta y Diesel organizadas en columnas
col1, col2 = st.columns(2)

with col1:
  st.markdown(
      """
        <div style="background-color: #1a1a1a; padding: 18px; border-radius: 8px; border-left: 5px solid #3b82f6; border: 1px solid #333; color: #e0e0e0;">
            <h4 style="margin:0; color: #60a5fa;">Super + Infinia (Naftas)</h4>
            <p style="font-size: 26px; font-weight: bold; margin: 10px 0 5px 0; color: #fff;">422.349 L</p>
            <p style="margin:0; color: #9ca3af;">Mix: <b>64%</b></p>
            <hr style="border-color: #333; margin: 12px 0;">
            <p style="margin:4px 0; font-size: 14px;">Promedio / Día: <b>13.624 L</b></p>
            <p style="margin:4px 0; font-size: 14px;">Proyección Mes: <b>422.349,46 L</b></p>
        </div>
        """,
      unsafe_allow_html=True,
  )

with col2:
  st.markdown(
      """
        <div style="background-color: #1a1a1a; padding: 18px; border-radius: 8px; border-left: 5px solid #eab308; border: 1px solid #333; color: #e0e0e0;">
            <h4 style="margin:0; color: #facc15;">Diesel + Inf. Diesel</h4>
            <p style="font-size: 26px; font-weight: bold; margin: 10px 0 5px 0; color: #fff;">58.648 L</p>
            <p style="margin:0; color: #9ca3af;">Mix: <b>36%</b></p>
            <hr style="border-color: #333; margin: 12px 0;">
            <p style="margin:4px 0; font-size: 14px;">Promedio / Día: <b>1.892 L</b></p>
            <p style="margin:4px 0; font-size: 14px;">Proyección Mes: <b>58.648,28 L</b></p>
        </div>
        """,
      unsafe_allow_html=True,
  )

st.markdown("<br>", unsafe_allow_html=True)

# 4. Datos de las ventas diarias (Abajo)
data_tabla = [
    ("22-07", 333, 830, 4702, 8891),
    ("23-07", 929, 1210, 5926, 9516),
    ("24-07", 787, 1376, 4984, 9747),
    ("25-07", 1288, 848.8, 4594, 8334),
    ("26-07", 152, 861.19, 3892, 6716),
    ("27-07", 1248, 882.23, 3782, 7511),
    ("28-07", 622, 1113, 5123, 8511),
    ("29-07", 700, 1248, 4026, 8863),
    ("30-07", 513, 1386, 4932, 8669),
    ("31-07", 1246, 1287, 5502, 9710),
]

df_tabla = pd.DataFrame(
    data_tabla, columns=["Fecha", "Diesel", "Infinia Diesel", "Infinia", "Super"]
)

st.markdown("### 📋 Detalle de Registros Diarios")
st.dataframe(df_tabla, use_container_width=True, hide_index=True)
