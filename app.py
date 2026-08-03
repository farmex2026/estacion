# ==========================================
# MENÚ 3: TIENDA FULL (Con persistencia en la Nube)
# ==========================================
elif menu_principal == "🛒 Tienda Full":
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Seleccionar Mes (Tienda Full)")
    mes_seleccionado_full = st.sidebar.selectbox(
        "Mes Tienda Full", meses_lista, key="mes_full_trabajo"
    )

    sheet_full_26 = f"full_{mes_seleccionado_full.lower()}_2026"

    if (
        mes_seleccionado_full not in st.session_state.full_2026
        or st.session_state.full_2026[mes_seleccionado_full].empty
    ):
        df_nube_full = cargar_desd_nube(sheet_full_26)
        if not df_nube_full.empty:
            if "rubros" in df_nube_full.columns:
                df_nube_full["rubros"] = df_nube_full["rubros"].apply(
                    lambda x: json.loads(x)
                    if isinstance(x, str) and x.startswith("[")
                    else []
                )
            st.session_state.full_2026[mes_seleccionado_full] = df_nube_full

    if st.sidebar.button("🔄 Recargar Tienda Full desde la Nube"):
        st.session_state.full_2026.pop(mes_seleccionado_full, None)
        df_nube_full = cargar_desd_nube(sheet_full_26)
        if not df_nube_full.empty:
            if "rubros" in df_nube_full.columns:
                df_nube_full["rubros"] = df_nube_full["rubros"].apply(
                    lambda x: json.loads(x)
                    if isinstance(x, str) and x.startswith("[")
                    else []
                )
            st.session_state.full_2026[mes_seleccionado_full] = df_nube_full
        st.rerun()

    with st.sidebar.expander("🔐 Panel Admin (Subir Cierres Full)"):
        archivos_full = st.file_uploader(
            f"Subir Planillas Full (2026)",
            type=["htm", "html"],
            accept_multiple_files=True,
            key=f"uploader_full_2026_{mes_seleccionado_full}",
        )

        if archivos_full:
            nuevos_registros = []
            for arq in archivos_full:
                if arq.name.endswith((".htm", ".html")):
                    res_html = procesar_archivo_full_html(arq)
                    if res_html:
                        nuevos_registros.append(res_html)

            if nuevos_registros:
                df_actual = st.session_state.full_2026.get(
                    mes_seleccionado_full, pd.DataFrame()
                )
                df_nuevos = pd.DataFrame(nuevos_registros)
                df_concatenado = (
                    pd.concat([df_actual, df_nuevos], ignore_index=True)
                    .drop_duplicates(subset=["archivo"])
                    .reset_index(drop=True)
                )
                st.session_state.full_2026[mes_seleccionado_full] = (
                    df_concatenado
                )

                try:
                    df_para_nube = df_concatenado.copy()
                    if "rubros" in df_para_nube.columns:
                        df_para_nube["rubros"] = df_para_nube["rubros"].apply(
                            lambda x: json.dumps(x)
                        )
                    df_para_nube = df_para_nube.fillna("").astype(str)
                    payload = {
                        "month": sheet_full_26,
                        "headers": df_para_nube.columns.tolist(),
                        "rows": df_para_nube.values.tolist(),
                    }
                    requests.post(URL_NUBE, json=payload, timeout=60)
                    st.success(
                        f"¡{len(nuevos_registros)} archivos de Tienda Full"
                        " procesados y guardados en la nube!"
                    )
                except Exception as e:
                    st.error(f"Error al guardar en la nube: {e}")

    df_f26 = st.session_state.full_2026.get(
        mes_seleccionado_full, pd.DataFrame()
    )

    st.subheader(
        f"🛒 Cantidades Vendidas Tienda Full - {mes_seleccionado_full} (2026)"
    )

    if not df_f26.empty:
        st.success(
            f"✅ Cierres de Tienda Full cargados: {len(df_f26)} archivos"
        )
        st.markdown("---")

        todos_rubros_26 = []
        for lst in df_f26.get("rubros", []):
            if isinstance(lst, list):
                todos_rubros_26.extend(lst)

        if todos_rubros_26:
            df_rubros_26 = pd.DataFrame(todos_rubros_26)
            df_rubros_sum = (
                df_rubros_26.groupby("Rubro")
                .agg({"Cantidad": "sum"})
                .reset_index()
            )

            st.subheader(
                "🍔 Resumen de Unidades: Comidas y Bebidas Calientes"
            )

            mask_comidas = (
                df_rubros_sum["Rubro"]
                .str.upper()
                .str.contains("COMIDA", na=False)
            )
            df_comidas_detalle = df_rubros_sum[mask_comidas]
            total_cant_comidas = (
                df_comidas_detalle["Cantidad"].sum()
                if not df_comidas_detalle.empty
                else 0.0
            )

            # Filtro exacto para tomar únicamente el rubro de Bebidas Calientes
            mask_bebidas_cal = (
                df_rubros_sum["Rubro"]
                .str.upper()
                .str.contains("BEBIDAS CALIENTES", na=False)
            )
            df_bebidas_cal_detalle = df_rubros_sum[mask_bebidas_cal]
            total_cant_bebidas_cal = (
                df_bebidas_cal_detalle["Cantidad"].sum()
                if not df_bebidas_cal_detalle.empty
                else 0.0
            )

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.metric(
                    label="🍲 Total Unidades Comidas (Comidas + Elaboradas)",
                    value=fmt_entero(total_cant_comidas),
                )
                if not df_comidas_detalle.empty:
                    st.dataframe(
                        df_comidas_detalle.style.format(
                            {"Cantidad": fmt_entero}
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
            with col_c2:
                st.metric(
                    label="☕ Total Unidades Bebidas Calientes",
                    value=fmt_entero(total_cant_bebidas_cal),
                )
                if not df_bebidas_cal_detalle.empty:
                    st.dataframe(
                        df_bebidas_cal_detalle.style.format(
                            {"Cantidad": fmt_entero}
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("Sin registros de Bebidas Calientes.")

            st.markdown("---")
            st.subheader("📋 Detalle Completo de Unidades por Rubro (2026)")
            st.dataframe(
                df_rubros_sum.style.format({"Cantidad": fmt_entero}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(
                "No hay datos de rubros detallados en los archivos HTML"
                " cargados."
            )

        st.markdown("---")
        st.subheader("📋 Listado de Cierres Diarios")
        df_mostrar_26 = df_f26[["archivo", "cierre"]].copy()
        df_mostrar_26.columns = ["Archivo", "Cierre Nro"]
        st.dataframe(
            df_mostrar_26, use_container_width=True, hide_index=True
        )
    else:
        st.info(
            f"No hay registros de Tienda Full cargados para el mes de"
            f" **{mes_seleccionado_full}** en 2026."
        )
