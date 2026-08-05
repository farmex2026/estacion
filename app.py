import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Control de Combustibles YPF", layout="wide")

st.title("⛽ Control de Combustibles YPF")

# 1. Botón para subir tu archivo Excel con todos los datos
uploaded_file = st.file_uploader(
    "Cargar planilla de combustibles (Excel)", type=["xlsx", "xls"]
)

if uploaded_file is not None:
  # Leer el archivo Excel
  df_raw = pd.read_excel(uploaded_file, skiprows=1)

  # Limpiar y preparar los datos (asumiendo la estructura estándar de las columnas)
  # Buscamos las columnas de fecha, diesel, infinia diesel, infinia y super
  df_tabla = df_raw.iloc[:, :5].copy()
  df_tabla.columns = ["Fecha", "Diesel", "Infinia Diesel", "Infinia", "Super"]

  # Filtrar filas válidas (que tengan fecha y no sean totales)
  df_tabla = df_tabla.dropna(subset=["Fecha"])
  df_tabla = df_tabla[
      ~df_tabla["Fecha"].astype(str).str.contains("TOTALES|super", case=False)
  ]

  # Convertir columnas numéricas
  for col in ["Diesel", "Infinia Diesel", "Infinia", "Super"]:
    df_tabla[col] = pd.to_numeric(df_tabla[col], errors="coerce").fillna(0)

  # Selector de meses (si el archivo tiene múltiples meses o filtrado)
  st.markdown("### 📊 Resumen, Mix y Proyecciones")

  # Cálculos automáticos basados en los datos del archivo
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

  # 2. Métricas Principales (Arriba)
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

  # 3. Tarjetas de Mix: Super vs Infinia & Diesel 500 vs Infinia Diesel
  col1, col2 = st.columns(2)

  with col1:
    st.markdown(
        f"""
        <div style="background-color: #1a1a1a; padding: 18px; border-radius: 8px; border-left: 5px solid #3b82f6; border: 1px solid #333; color: #e0e0e0;">
            <h4 style="margin:0; color: #60a5fa;">Naftas: Super vs Infinia</h4>
            <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                <span>Super: <b>{tot_super:,.1f} L</b> ({mix_super:.1f}%)</span>
                <span>Infinia: <b>{tot_infinia:,.1f} L</b> ({mix_infinia:.1f}%)</span>
            </div>
            <hr style="border-color: #333; margin: 12px 0;">
            <p style="margin:4px 0; font-size: 14px;">Total Naftas: <b>{total_general_nafta:,.1f} L</b></p>
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
                <span>Diesel 500: <b>{tot_diesel:,.1f} L</b> ({mix_diesel_500:.1f}%)</span>
                <span>Inf. Diesel: <b>{tot_inf_diesel:,.1f} L</b> ({mix_inf_diesel:.1f}%)</span>
            </div>
            <hr style="border-color: #333; margin: 12px 0;">
            <p style="margin:4px 0; font-size: 14px;">Total Gasoil: <b>{total_general_gasoil:,.1f} L</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)

  # 4. Detalle de las ventas diarias (Abajo)
  st.markdown("### 📋 Detalle de Registros Diarios (Mes Completo)")
  st.dataframe(df_tabla, use_container_width=True, hide_index=True)

else:
  st.info(
      "👆 Por favor, sube tu archivo Excel de combustibles usando el botón de"
      " arriba para visualizar los datos, mix y proyecciones."
  )
