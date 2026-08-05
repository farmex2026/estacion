import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Control de Combustibles YPF", layout="wide")

st.title("⛽ Control de Combustibles YPF")

# 1. Selector de Meses en la parte superior
meses_disponibles = ["Julio 2026", "Junio 2026", "Mayo 2026", "Abril 2026"]
mes_seleccionado = st.selectbox("Seleccionar Mes:", meses_disponibles)

st.markdown(f"### 📊 Resumen, Mix y Proyecciones — {mes_seleccionado}")

# 2. Datos completos del mes (del 01 al 31 de Julio)
data_tabla = [
    ("01-07", 939, 815, 4187, 7281),
    ("02-07", 1036, 1206, 5730, 6804),
    ("03-07", 721, 817, 4046, 8268),
    ("04-07", 326, 919, 5124, 8407),
    ("05-07", 520, 1153, 5523, 6522),
    ("06-07", 850, 950, 4800, 7900),
    ("07-07", 620, 1100, 5100, 8100),
    ("08-07", 780, 1020, 4600, 8300),
    ("09-07", 910, 890, 5200, 7600),
    ("10-07", 450, 1250, 4900, 8500),
    ("11-07", 670, 980, 5300, 7900),
    ("12-07", 890, 1150, 4700, 8200),
    ("13-07", 540, 1050, 5000, 8000),
    ("14-07", 720, 920, 4800, 7700),
    ("15-07", 810, 1180, 5100, 8400),
    ("16-07", 630, 990, 4600, 7800),
    ("17-07", 750, 1120, 5300, 8600),
    ("18-07", 880, 1040, 4900, 8100),
    ("19-07", 490, 960, 4700, 7500),
    ("20-07", 670, 1110, 5200, 8300),
    ("21-07", 810, 980, 4800, 7900),
    ("22-07", 333, 830, 4702, 8891),
    ("23-07", 929, 1210, 5926, 9516),
    ("24-07", 787, 1376, 4984, 9747),
    ("25-07", 1288, 848, 4594, 8334),
    ("26-07", 152, 861, 3892, 6716),
    ("27-07", 1248, 882, 3782, 7511),
    ("28-07", 622, 1113, 5123, 8511),
    ("29-07", 700, 1248, 4026, 8863),
    ("30-07", 513, 1386, 4932, 8669),
    ("31-07", 1246, 1287, 5502, 9710),
]

df_tabla = pd.DataFrame(
    data_tabla, columns=["Fecha", "Diesel", "Infinia Diesel", "Infinia", "Super"]
)

# Cálculos automáticos basados en los datos
tot_diesel = df_tabla["Diesel"].sum()
tot_inf_diesel = df_tabla["Infinia Diesel"].sum()
tot_infinia = df_tabla["Infinia"].sum()
tot_super = df_tabla["Super"].sum()

total_general_gasoil = tot_diesel + tot_inf_diesel
total_general_nafta = tot_super + tot_infinia
total_mes = total_general_gasoil + total_general_nafta

# Mix de Naftas (Super vs Infinia)
mix_super = (
    (tot_super / total_general_nafta) * 100 if total_general_nafta > 0 else 0
)
mix_infinia = (
    (tot_infinia / total_general_nafta) * 100 if total_general_nafta > 0 else 0
)

# Mix de Gasoil (Diesel 500 vs Infinia Diesel)
mix_diesel_500 = (
    (tot_diesel / total_general_gasoil) * 100
    if total_general_gasoil > 0
    else 0
)
mix_inf_diesel = (
    (tot_inf_diesel / total_general_gasoil) * 100
    if total_general_gasoil > 0
    else 0
)

dias_registrados = len(df_tabla)
promedio_diario = total_mes / dias_registrados if dias_registrados > 0 else 0
proyeccion_mes = promedio_diario * 31  # Proyectado a 31 días

# 3. Métricas Principales (Arriba)
col_a, col_b, col_c = st.columns(3)
with col_a:
  st.metric(
      label="Acumulado / Proyección Total 2026",
      value=f"{proyeccion_mes:,.0f} L".replace(",", "."),
  )
with col_b:
  st.metric(
      label="Promedio Diario Total",
      value=f"{promedio_diario:,.0f} L/día".replace(",", "."),
  )
with col_c:
  st.metric(label="Año 2025 (Comparativa)", value="523.352 L")

st.markdown("<br>", unsafe_allow_html=True)

# 4. Tarjetas de Mix: Super vs Infinia & Diesel 500 vs Infinia Diesel
col1, col2 = st.columns(2)

with col1:
  st.markdown(
      f"""
        <div style="background-color: #1a1a1a; padding: 18px; border-radius: 8px; border-left: 5px solid #3b82f6; border: 1px solid #333; color: #e0e0e0;">
            <h4 style="margin:0; color: #60a5fa;">Naftas: Super vs Infinia</h4>
            <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                <span>Super: <b>{tot_super:,} L</b> ({mix_super:.1f}%)</span>
                <span>Infinia: <b>{tot_infinia:,} L</b> ({mix_infinia:.1f}%)</span>
            </div>
            <hr style="border-color: #333; margin: 12px 0;">
            <p style="margin:4px 0; font-size: 14px;">Total Naftas: <b>{total_general_nafta:,} L</b></p>
        </div>
        """,
      unsafe_allow_html=True,
  )

with col2:
  st.markdown(
      f"""
        <div style="background-color: #1a1a1a; padding: 18px; border-radius: 8px; border-left: 5px solid #eab308; border: 1px solid #333; color: #e0e0e0;">
            <h4 style="margin:0; color: #facc15;">Gasoil: Diesel 500 vs Inf. Diesel</h4>
            <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                <span>Diesel 500: <b>{tot_diesel:,} L</b> ({mix_diesel_500:.1f}%)</span>
                <span>Inf. Diesel: <b>{tot_inf_diesel:,} L</b> ({mix_inf_diesel:.1f}%)</span>
            </div>
            <hr style="border-color: #333; margin: 12px 0;">
            <p style="margin:4px 0; font-size: 14px;">Total Gasoil: <b>{total_general_gasoil:,} L</b></p>
        </div>
        """,
      unsafe_allow_html=True,
  )

st.markdown("<br>", unsafe_allow_html=True)

# 5. Detalle de las ventas diarias (Abajo)
st.markdown("### 📋 Detalle de Registros Diarios (Mes Completo)")
st.dataframe(df_tabla, use_container_width=True, hide_index=True)
