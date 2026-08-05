import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Control de Combustibles YPF - Julio 2026", layout="wide"
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #121212;
        color: #e0e0e0;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("⛽ Detalle de Registros - Julio 2026")

# Datos de la tabla (Julio 2026)
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

# 1. Tabla con diseño oscuro y scroll
st.markdown("### 📋 Registros Diario")
html_tabla = f"""
<div style="max-height: 250px; overflow-y: auto; background-color: #121212; color: #e0e0e0; font-family: sans-serif; border: 1px solid #333; border-radius: 4px; margin-bottom: 25px;">
  <table style="width: 100%; border-collapse: collapse; font-size: 13px; text-align: left;">
    <thead>
      <tr style="background-color: #1f1f1f; position: sticky; top: 0; border-bottom: 1px solid #333;">
        <th style="padding: 8px;">Fecha</th>
        <th style="padding: 8px;">Diesel</th>
        <th style="padding: 8px;">Infinia Diesel</th>
        <th style="padding: 8px;">Infinia</th>
        <th style="padding: 8px;">Super</th>
      </tr>
    </thead>
    <tbody>
"""

for idx, row in df_tabla.iterrows():
  border = (
      "border-bottom: 1px solid #222;"
      if idx < len(df_tabla) - 1
      else ""
  )
  html_tabla += f"""
      <tr style="{border}">
        <td style="padding: 6px;">{row["Fecha"]}</td>
        <td>{row["Diesel"]}</td>
        <td>{row["Infinia Diesel"]}</td>
        <td>{row["Infinia"]}</td>
        <td>{row["Super"]}</td>
      </tr>
"""

html_tabla += """
    </tbody>
  </table>
</div>
"""
st.markdown(html_tabla, unsafe_allow_html=True)

# 2. Resumen, Mix y Proyecciones con diseño moderno en tarjetas
st.markdown(
    """
<div style="background-color: #121212; color: #e0e0e0; font-family: sans-serif; padding: 20px; border-radius: 8px; border: 1px solid #333;">
  
  <h3 style="margin-top: 0; color: #fff; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; font-size: 18px;">Resumen y Proyecciones - Combustibles</h3>

  <!-- Bloque 1: Totales y Mix -->
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
    
    <!-- Super + Infinia -->
    <div style="background-color: #1a1a1a; padding: 12px; border-radius: 6px; border-left: 4px solid #3b82f6;">
      <div style="font-size: 12px; color: #9ca3af; text-transform: uppercase; font-weight: bold;">Super + Infinia (Naftas)</div>
      <div style="font-size: 20px; font-weight: bold; color: #fff; margin: 5px 0;">422.349 L</div>
      <div style="font-size: 13px; color: #60a5fa;">Mix: <strong>64%</strong></div>
    </div>

    <!-- D.500 + Inf Diesel -->
    <div style="background-color: #1a1a1a; padding: 12px; border-radius: 6px; border-left: 4px solid #eab308;">
      <div style="font-size: 12px; color: #9ca3af; text-transform: uppercase; font-weight: bold;">Diesel + Inf. Diesel</div>
      <div style="font-size: 20px; font-weight: bold; color: #fff; margin: 5px 0;">58.648 L</div>
      <div style="font-size: 13px; color: #facc15;">Mix: <strong>36%</strong></div>
    </div>

  </div>

  <!-- Bloque 2: Promedios diarios y Proyecciones por categoría -->
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
    
    <!-- Naftas Detalle -->
    <div style="background-color: #1a1a1a; padding: 12px; border-radius: 6px;">
      <div style="font-size: 13px; font-weight: bold; color: #60a5fa; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px;">Naftas (General)</div>
      <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
        <span style="color: #9ca3af;">Promedio / Día:</span>
        <span style="font-weight: bold;">13.624 L</span>
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 13px;">
        <span style="color: #9ca3af;">Proyección Mes:</span>
        <span style="font-weight: bold;">422.349,46 L</span>
      </div>
    </div>

    <!-- Diesel Detalle -->
    <div style="background-color: #1a1a1a; padding: 12px; border-radius: 6px;">
      <div style="font-size: 13px; font-weight: bold; color: #facc15; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px;">Diesel (General)</div>
      <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
        <span style="color: #9ca3af;">Promedio / Día:</span>
        <span style="font-weight: bold;">1.892 L</span>
      </div>
      <div style="display: flex; justify-content: space-between; font-size: 13px;">
        <span style="color: #9ca3af;">Proyección Mes:</span>
        <span style="font-weight: bold;">58.648,28 L</span>
      </div>
    </div>

  </div>

  <!-- Bloque 3: Totales Generales y Comparativa 2025 vs 2026 -->
  <div style="background-color: #1f2937; padding: 15px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
    <div>
      <div style="font-size: 11px; color: #9ca3af; text-transform: uppercase;">Promedio Diario Total</div>
      <div style="font-size: 16px; font-weight: bold; color: #fff;">15.516 L/día</div>
    </div>
    <div>
      <div style="font-size: 11px; color: #9ca3af; text-transform: uppercase;">Proyección Total Mes</div>
      <div style="font-size: 16px; font-weight: bold; color: #10b981;">480.998 L</div>
    </div>
    <div>
      <div style="font-size: 11px; color: #9ca3af; text-transform: uppercase;">Año 2025</div>
      <div style="font-size: 16px; font-weight: bold; color: #9ca3af;">523.352 L</div>
    </div>
  </div>

</div>
""",
    unsafe_allow_html=True,
)
