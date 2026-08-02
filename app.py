def procesar_df_turnos_2026(df):
    if df.empty:
        return pd.DataFrame()
    
    cols = df.columns
    
    def get_col(idx, possible_names):
        if idx < len(cols):
            return cols[idx]
        for name in possible_names:
            matches = [c for c in cols if name.lower() in str(c).lower()]
            if matches:
                return matches[0]
        return cols[idx] if idx < len(cols) else None

    col_fecha = get_col(0, ["fecha", "apertura"])
    col_super = get_col(1, ["nafta super", "super"])
    col_diesel = get_col(2, ["diesel 500", "d500", "diesel"])
    col_inf_nafta = get_col(3, ["infinia nafta"])
    col_inf_diesel = get_col(4, ["infinia diesel"])

    fechas_raw = df[col_fecha].astype(str) if col_fecha in df.columns else pd.Series([""] * len(df))
    
    lista_fechas = []
    lista_turnos = []
    
    for val in fechas_raw:
        val_str = val.strip()
        turno = "DESCONOCIDO"
        if "(1)" in val_str or val_str.endswith(" 1") or val_str.endswith("(1)"):
            turno = "TURNO NOCHE"
        elif "(2)" in val_str or val_str.endswith(" 2") or val_str.endswith("(2)"):
            turno = "TURNO MAÑANA"
        elif "(3)" in val_str or val_str.endswith(" 3") or val_str.endswith("(3)"):
            turno = "TURNO TARDE"
            
        fecha_limpia = re.sub(r'\s*\([123]\)', '', val_str).strip()
        lista_fechas.append(fecha_limpia)
        lista_turnos.append(turno)

    res = pd.DataFrame()
    res["Fecha"] = lista_fechas
    res["NAFTA SUPER"] = limpiar_serie_numerica(df[col_super]) if col_super in df.columns else 0.0
    res["DIESEL 500"] = limpiar_serie_numerica(df[col_diesel]) if col_diesel in df.columns else 0.0
    res["INFINIA NAFTA"] = limpiar_serie_numerica(df[col_inf_nafta]) if col_inf_nafta in df.columns else 0.0
    res["INFINIA DIESEL"] = limpiar_serie_numerica(df[col_inf_diesel]) if col_inf_diesel in df.columns else 0.0
    
    # Forzar el cálculo automático sumando todos los productos
    res["TOTAL"] = (
        res["NAFTA SUPER"] 
        + res["DIESEL 500"] 
        + res["INFINIA NAFTA"] 
        + res["INFINIA DIESEL"]
    )

    res["Turno"] = lista_turnos

    if not res.empty:
        mask_basura = res["Fecha"].astype(str).str.strip().str.lower().isin(["fecha apertura", "fecha", "apertura", "nan", ""])
        res = res[~mask_basura].reset_index(drop=True)

    return res
