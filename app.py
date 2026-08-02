def procesar_df_turnos_2026(df):
    if df.empty:
        return pd.DataFrame()
    
    cols = df.columns
    
    def buscar_columna(nombres_posibles):
        for col in cols:
            c_low = str(col).strip().lower()
            for nombre in nombres_posibles:
                if nombre in c_low:
                    return col
        return None

    # Identificar columnas por texto clave
    col_fecha = buscar_columna(["fecha", "apertura"])
    col_super = buscar_columna(["súper", "super"])
    col_diesel = buscar_columna(["diesel 500", "d500", "diesel 500"])
    col_inf_nafta = buscar_columna(["infinia nafta", "inf. nafta"])
    col_inf_diesel = buscar_columna(["infinia diesel", "inf. diesel"])

    # Si no encuentra por nombre exacto, usa los índices por defecto como respaldo
    if not col_fecha and len(cols) > 0: col_fecha = cols[0]
    if not col_super and len(cols) > 1: col_super = cols[1]
    if not col_diesel and len(cols) > 2: col_diesel = cols[2]
    if not col_inf_nafta and len(cols) > 3: col_inf_nafta = cols[3]
    if not col_inf_diesel and len(cols) > 4: col_inf_diesel = cols[4]

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
    res["NAFTA SUPER"] = limpiar_serie_numerica(df[col_super]) if col_super and col_super in df.columns else 0.0
    res["DIESEL 500"] = limpiar_serie_numerica(df[col_diesel]) if col_diesel and col_diesel in df.columns else 0.0
    res["INFINIA NAFTA"] = limpiar_serie_numerica(df[col_inf_nafta]) if col_inf_nafta and col_inf_nafta in df.columns else 0.0
    res["INFINIA DIESEL"] = limpiar_serie_numerica(df[col_inf_diesel]) if col_inf_diesel and col_inf_diesel in df.columns else 0.0
    
    # Cálculo automático y seguro de la suma total
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
