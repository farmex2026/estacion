def procesar_archivos_turnos(archivos):
    lista_dfs = []
    for archivo in archivos:
        try:
            # Intentamos leer el Excel (probando primero con header en la fila 0, por si cambió el formato)
            df = pd.read_excel(archivo)
            df.columns = [str(c).strip() for c in df.columns]
            lista_dfs.append(df)
        except Exception as e:
            try:
                df = pd.read_excel(archivo, header=1)
                df.columns = [str(c).strip() for c in df.columns]
                lista_dfs.append(df)
            except Exception as e2:
                st.warning(f"No se pudo leer el archivo {archivo.name}: {e2}")
    if lista_dfs:
        df_concatenado = pd.concat(lista_dfs, ignore_index=True)
        return df_concatenado.drop_duplicates().reset_index(drop=True)
    return pd.DataFrame()


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

    col_fecha = buscar_columna(["fecha", "apertura", "dia"])
    col_super = buscar_columna(["súper", "super", "nafta super"])
    col_diesel = buscar_columna(["diesel 500", "d500", "diesel 500"])
    col_inf_nafta = buscar_columna(["infinia nafta", "inf. nafta", "infinia"])
    col_inf_diesel = buscar_columna(
        ["infinia diesel", "inf. diesel", "diesel infinia"]
    )

    # Si no encuentra las columnas por nombre, tomamos las primeras por posición como respaldo
    if not col_fecha and len(cols) > 0:
        col_fecha = cols[0]
    if not col_super and len(cols) > 1:
        col_super = cols[1]
    if not col_diesel and len(cols) > 2:
        col_diesel = cols[2]
    if not col_inf_nafta and len(cols) > 3:
        col_inf_nafta = cols[3]
    if not col_inf_diesel and len(cols) > 4:
        col_inf_diesel = cols[4]

    fechas_raw = (
        df[col_fecha]
        if col_fecha and col_fecha in df.columns
        else pd.Series([""] * len(df))
    )
    dias_map = {
        "Mon": "Lun",
        "Tue": "Mar",
        "Wed": "Mié",
        "Thu": "Jue",
        "Fri": "Vie",
        "Sat": "Sáb",
        "Sun": "Dom",
    }

    lista_fechas = []
    lista_turnos = []

    for val in fechas_raw:
        val_str = str(val).strip() if pd.notna(val) else ""
        if val_str.lower() in ["nan", "nat", "none"]:
            val_str = ""
        turno = "DESCONOCIDO"
        if "(1)" in val_str or val_str.endswith(" 1"):
            turno = "TURNO NOCHE"
        elif "(2)" in val_str or val_str.endswith(" 2"):
            turno = "TURNO MAÑANA"
        elif "(3)" in val_str or val_str.endswith(" 3"):
            turno = "TURNO TARDE"
        fecha_limpia = re.sub(r"\s*\([123]\)", "", val_str).strip()
        for eng, esp in dias_map.items():
            fecha_limpia = re.sub(
                r"\b" + eng + r"\b", esp, fecha_limpia, flags=re.IGNORECASE
            )
        lista_fechas.append(fecha_limpia)
        lista_turnos.append(turno)

    res = pd.DataFrame()
    res["Fecha"] = lista_fechas
    res["NAFTA SUPER"] = (
        limpiar_serie_numerica(df[col_super])
        if col_super and col_super in df.columns
        else 0.0
    )
    res["DIESEL 500"] = (
        limpiar_serie_numerica(df[col_diesel])
        if col_diesel and col_diesel in df.columns
        else 0.0
    )
    res["INFINIA NAFTA"] = (
        limpiar_serie_numerica(df[col_inf_nafta])
        if col_inf_nafta and col_inf_nafta in df.columns
        else 0.0
    )
    res["INFINIA DIESEL"] = (
        limpiar_serie_numerica(df[col_inf_diesel])
        if col_inf_diesel and col_inf_diesel in df.columns
        else 0.0
    )
    res["TOTAL"] = (
        res["NAFTA SUPER"]
        + res["DIESEL 500"]
        + res["INFINIA NAFTA"]
        + res["INFINIA DIESEL"]
    )
    res["Turno"] = lista_turnos

    return res
