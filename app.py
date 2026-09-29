import streamlit as st
import pandas as pd
import datetime
import calendar

# =========================================================================
# CONFIGURACIÓN DE PAGINA (Color #1E381F)
# =========================================================================
st.set_page_config(page_title="Gestión Horas - Café 32", layout="wide", page_icon="☕")

st.markdown("""
    <style>
        /* Color de fondo del menú lateral */
        [data-testid="stSidebar"] {
            background-color: #1E381F !important;
        }
        [data-testid="stSidebar"] * {
            color: #FFFFFF !important;
        }
        /* Botones primarios con el color de la app */
        .stButton>button {
            background-color: #1E381F;
            color: white;
            border-radius: 6px;
        }
        /* Estilos para el calendario  */
        .calendar-box {
            border: 1px solid #E0E0E0;
            padding: 8px;
            min-height: 110px;
            background-color: #F9F9F9;
            border-radius: 4px;
        }
        .day-number {
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 4px;
            color: #333333;
        }
        .badge-manana {
            background-color: #5CB386;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            display: block;
            margin-bottom: 2px;
            font-weight: 500;
        }
        .badge-tarde {
            background-color: #ffc340;
            color: black;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            display: block;
            margin-bottom: 2px;
            font-weight: 500;
        }
        .badge-feriado {
            background-color: #007BFF;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            display: block;
            margin-bottom: 2px;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# VARIABLES DE SESIÓN (PERSISTENCIA)
# =========================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if 'empleados' not in st.session_state:
    st.session_state['empleados'] = pd.DataFrame([
        {'legajo': 1, 'nombre': 'Camila', 'puesto': 'Barista'},
        {'legajo': 2, 'nombre': 'Jennifer', 'puesto': 'Cocina'},
        {'legajo': 3, 'nombre': 'Joel', 'puesto': 'Panadero'},
        {'legajo': 4, 'nombre': 'Ariana', 'puesto': 'Moza'},
        {'legajo': 5, 'nombre': 'Axel', 'puesto': 'Barista'},
        {'legajo': 7, 'nombre': 'Pepi', 'puesto': 'Cocinero'},
        {'legajo': 8, 'nombre': 'Israel', 'puesto': 'Mozo'},
        {'legajo': 9, 'nombre': 'Lucia', 'puesto': 'Moza'},
        {'legajo': 10, 'nombre': 'Priscila', 'puesto': 'Moza'},
        {'legajo': 11, 'nombre': 'Candela', 'puesto': 'Moza'},
        {'legajo': 12, 'nombre': 'Agustina', 'puesto': 'Cocinero'},
        {'legajo': 13, 'nombre': 'Valentina', 'puesto': 'Pastelera'},
        {'legajo': 14, 'nombre': 'Melania', 'puesto': 'Moza'},
    ])

if 'fichajes_raw' not in st.session_state:
    st.session_state['fichajes_raw'] = pd.DataFrame(columns=['legajo', 'fecha', 'hora', 'es_feriado'])

if 'feriados' not in st.session_state:
    st.session_state['feriados'] = [
        datetime.date(2026, 1, 1),   # Año Nuevo
        datetime.date(2026, 3, 24),  # Memoria
        datetime.date(2026, 4, 2),   # Malvinas
        datetime.date(2026, 5, 1),   # Día del Trabajo
        datetime.date(2026, 5, 25),  # Revolución de Mayo
        datetime.date(2026, 6, 20),  # Día de la Bandera
        datetime.date(2026, 7, 9),   # Independencia
        datetime.date(2026, 9, 28)   # Día del Empleado de Comercio
    ]

# =========================================================================
# LOGIN OBLIGATORIO
# =========================================================================
if not st.session_state['autenticado']:
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("<h2 style='text-align: center; color: #1E381F;'>☕ CONTROL DE ASISTENCIA</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            usuario = st.text_input("Usuario Administrador:")
            clave = st.text_input("Contraseña:", type="password")
            btn_login = st.form_submit_button("Ingresar al Sistema")
            
            if btn_login:
                if usuario.lower() == "admin" and clave == "cafe32":
                    st.session_state['autenticado'] = True
                    st.success("Acceso concedido.")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifique el usuario o la contraseña.")
    st.stop()

# =========================================================================
# MENÚ FIJO IZQUIERDO (SIDEBAR COMPACTO)
# =========================================================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>CAFÉ 32</h2>", unsafe_allow_html=True)
    
    seccion = st.radio(
        "Navegación:",
        ["👥 Empleados", "📅 CALENDARIO", "📊 GESTION HORAS", "📥 CARGAR ARCHIVO"]
    )
    
    st.markdown("---")
    st.markdown("### 🔗 Acceso Externo")
    st.markdown("[📊 Abrir Google Sheets](https://docs.google.com/spreadsheets/d/1veKrncoLJmYwxXrnEOdVembeiXT9oL9nm9le-r1ZpRg/edit?usp=sharing)", unsafe_allow_html=True)

# =========================================================================
# MOTOR DE PROCESAMIENTO DE ARCHIVOS PROSOFT (.TXT)
# =========================================================================
def parsear_prosoft_txt(file_upload):
    contenido = file_upload.getvalue().decode("utf-8")
    registros = []
    
    for linea in contenido.splitlines():
        linea_limpia = linea.replace('\xa0', ' ').strip().rstrip('.')
        if not linea_limpia or "UDISKLOG" in linea_limpia or "DateTime" in linea_limpia or "Mchn" in linea_limpia:
            continue
            
        partes = linea_limpia.split()
        if len(partes) < 5:
            continue
            
        try:
            legajo = int(partes[2])
            fecha_str = partes[-2]  
            hora_str = partes[-1]   
            
            fecha_dt = pd.to_datetime(fecha_str, format='%Y/%m/%d').date()
            hora_dt = pd.to_datetime(hora_str, format='%H:%M:%S').time()
            
            es_feriado = fecha_dt in st.session_state['feriados']
            
            registros.append({
                'legajo': legajo,
                'fecha': fecha_dt,
                'hora': datetime.datetime.combine(fecha_dt, hora_dt),
                'es_feriado': es_feriado
            })
        except Exception:
            continue
                
    return pd.DataFrame(registros)

# =========================================================================
# SECCIÓN 1: EMPLEADOS
# =========================================================================
if seccion == "👥 Empleados":
    st.header("👥 Administración de Personal")
    
    with st.expander("➕ Registrar o Editar Empleado desde la App", expanded=False):
        with st.form("form_empleado"):
            legajo_input = st.number_input("Número de Legajo (ID Reloj):", min_value=1, step=1)
            nombre_input = st.text_input("Nombre Completo:")
            puesto_input = st.text_input("Puesto / Función:")
            btn_guardar = st.form_submit_button("Guardar Datos")
            
            if btn_guardar:
                if not nombre_input.strip():
                    st.error("El nombre no puede estar vacío.")
                else:
                    df_emp = st.session_state['empleados']
                    df_emp = df_emp[df_emp['legajo'] != legajo_input]
                    
                    nueva_linea = pd.DataFrame([{'legajo': int(legajo_input), 'nombre': nombre_input.strip(), 'puesto': puesto_input.strip()}])
                    st.session_state['empleados'] = pd.concat([df_emp, nueva_linea], ignore_index=True)
                    st.success(f"Empleado Guardado: Legajo {legajo_input} - {nombre_input}")
                    st.rerun()

    st.markdown("### Nómina Guardada en el Sistema")
    st.dataframe(st.session_state['empleados'].sort_values('legajo'), use_container_width=True, hide_index=True)

    # APARTADO EXCLUSIVO PARA CAMILA (Muestra DÍAS)
    st.markdown("---")
    st.subheader("☕ Reporte Exclusivo de Asistencia: Camila")
    df_fich_all = st.session_state['fichajes_raw']
    
    df_camila = df_fich_all[df_fich_all['legajo'] == 1].copy()
    
    if df_fich_all.empty:
        st.info("Aún no hay registros de fichajes cargados en el sistema.")
    elif df_camila.empty:
        st.info("Camila (Legajo 1) no registra marcaciones en los archivos cargados.")
    else:
        df_camila['fecha_dt'] = pd.to_datetime(df_camila['fecha']).dt.date
        dias_totales = df_camila['fecha_dt'].nunique()
        
        st.markdown(f"<div style='background-color:#1E381F; padding:15px; border-radius:10px; margin-bottom:20px; text-align:center;'>"
                    f"<h2 style='color:white; margin:0;'>TOTAL ACUMULADO: {dias_totales} DIAS</h2>"
                    f"</div>", unsafe_allow_html=True)
        
        df_camila = df_camila.sort_values('hora')
        df_camila_mostrar = df_camila[['fecha', 'hora']].copy()
        df_camila_mostrar['Fecha'] = pd.to_datetime(df_camila_mostrar['fecha']).dt.strftime('%d/%m/%Y')
        df_camila_mostrar['Hora de Fichaje'] = pd.to_datetime(df_camila_mostrar['hora']).dt.strftime('%H:%M:%S')
        df_camila_mostrar = df_camila_mostrar[['Fecha', 'Hora de Fichaje']].reset_index(drop=True)
        
        st.markdown(f"**Registros individuales de marcación (Legajo 1):**")
        st.dataframe(df_camila_mostrar, use_container_width=True, hide_index=True)

# =========================================================================
# SECCIÓN 2: CALENDARIO DE TURNOS
# =========================================================================
elif seccion == "📅 CALENDARIO":
    st.header("📅 Calendario Mensual de Turnos")
    
    df_fichajes = st.session_state['fichajes_raw']
    
    col_c1, col_c2 = st.columns(2)
    anio_sel = col_c1.selectbox("Año:", [2026, 2027, 2025], index=0)
    mes_sel = col_c2.selectbox("Mes:", list(range(1, 13)), index=datetime.date.today().month - 1)
    
    marcas_del_mes = {}
    if not df_fichajes.empty:
        df_fichajes['fecha_dt'] = pd.to_datetime(df_fichajes['fecha'])
        df_mes = df_fichajes[(df_fichajes['fecha_dt'].dt.year == anio_sel) & (df_fichajes['fecha_dt'].dt.month == mes_sel)]
        
        if not df_mes.empty:
            entradas = df_mes.groupby(['fecha', 'legajo'])['hora'].min().reset_index()
            df_nombres = st.session_state['empleados']
            entradas = pd.merge(entradas, df_nombres, on='legajo', how='left')
            
            for _, row in entradas.iterrows():
                dia = row['fecha'].day
                nombre_emp = row['nombre'] if pd.notna(row['nombre']) else f"Legajo {row['legajo']}"
                hora_entrada = row['hora'].time()
                
                if 7 <= hora_entrada.hour < 11:
                    tipo_turno = "manana"
                else:
                    tipo_turno = "tarde"
                    
                es_fer = row['fecha'] in st.session_state['feriados']
                
                if dia not in marcas_del_mes:
                    marcas_del_mes[dia] = []
                marcas_del_mes[dia].append({'nombre': nombre_emp, 'turno': tipo_turno, 'feriado': es_fer})

    cal = calendar.Calendar(firstweekday=6)
    mes_matriz = cal.monthdatescalendar(anio_sel, mes_sel)
    
    dias_semana = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
    cols_header = st.columns(7)
    for idx, d_nom in enumerate(dias_semana):
        cols_header[idx].markdown(f"<h4 style='text-align: center; margin:0; color:#1E381F;'>{d_nom}</h4>", unsafe_allow_html=True)
        
    for semana in mes_matriz:
        cols_semana = st.columns(7)
        for i, el_dia in enumerate(semana):
            if el_dia.month == mes_sel:
                html_contenido = f"<div class='calendar-box'><div class='day-number'>{el_dia.day}</div>"
                
                if el_dia in st.session_state['feriados']:
                    html_contenido += f"<span class='badge-feriado'>Feriado</span>"
                
                if el_dia.day in marcas_del_mes:
                    for m in marcas_del_mes[el_dia.day]:
                        if m['feriado']:
                            html_contenido += f"<span class='badge-feriado'>{m['nombre']} (F)</span>"
                        elif m['turno'] == "manana":
                            html_contenido += f"<span class='badge-manana'>{m['nombre']}</span>"
                        else:
                            html_contenido += f"<span class='badge-tarde'>{m['nombre']}</span>"
                            
                html_contenido += "</div>"
                cols_semana[i].markdown(html_contenido, unsafe_allow_html=True)
            else:
                cols_semana[i].markdown("<div style='border: 1px solid #F0F0F0; min-height: 110px;'></div>", unsafe_allow_html=True)

# =========================================================================
# SECCIÓN 3: GESTIÓN DE HORAS
# =========================================================================
elif seccion == "📊 GESTION HORAS":
    st.header("📊 Resumen Diario Limpio y Horas Acumuladas")
    
    df_fichajes = st.session_state['fichajes_raw']
    
    if df_fichajes.empty:
        st.warning("No hay registros en memoria. Cargá un archivo .txt en la pestaña correspondiente.")
    else:
        col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
        f_inicio = col_f1.date_input("Fecha Inicial de Cálculo:", value=df_fichajes['fecha'].min())
        f_fin = col_f2.date_input("Fecha Final de Cálculo:", value=df_fichajes['fecha'].max())
        
        opciones_emp = {0: "TODOS LOS EMPLEADOS"}
        for _, r in st.session_state['empleados'].iterrows():
            opciones_emp[r['legajo']] = f"Legajo {r['legajo']} - {r['nombre']}"
            
        legajo_sel = col_f3.selectbox("Filtrar por Empleado Específico:", options=list(opciones_emp.keys()), format_func=lambda x: opciones_emp[x])

        mask = (df_fichajes['fecha'] >= f_inicio) & (df_fischajes['fecha'] <= f_fin) if 'df_fischajes' in locals() else (df_fichajes['fecha'] >= f_inicio) & (df_fichajes['fecha'] <= f_fin)
        df_filtrado = df_fichajes[mask]
        
        if legajo_sel != 0:
            df_filtrado = df_filtrado[df_filtrado['legajo'] == legajo_sel]

        if df_filtrado.empty:
            st.info("Sin registros para los filtros seleccionados.")
        else:
            lineas_reporte = []
            
            for (legajo, fecha), grupo in df_filtrado.groupby(['legajo', 'fecha']):
                grupo_ordenado = grupo.sort_values('hora').reset_index(drop=True)
                
                rangos_str = []
                horas_totales_dia = 0.0
                
                i = 0
                while i < len(grupo_ordenado) - 1:
                    t_in = grupo_ordenado.loc[i, 'hora']
                    t_out = grupo_ordenado.loc[i+1, 'hora']
                    
                    duracion_bloque = (t_out - t_in).total_seconds() / 3600
                    if duracion_bloque > 0:
                        horas_totales_dia += duracion_bloque
                        rangos_str.append(f"{t_in.strftime('%H:%M')} a {t_out.strftime('%H:%M')}")
                    i += 2
                
                if i < len(grupo_ordenado):
                    t_in = grupo_ordenado.loc[i, 'hora']
                    rangos_str.append(f"{t_in.strftime('%H:%M')} (Sin par)")

                info_emp = st.session_state['empleados'][st.session_state['empleados']['legajo'] == legajo]
                if not info_emp.empty:
                    nom_final = info_emp.iloc[0]['nombre']
                else:
                    nom_final = f"Desconocido (Leg. {legajo})"
                
                f_str = fecha.strftime('%d/%m')
                rango_horario_completo = " y ".join(rangos_str) if rangos_str else "Sin registrar"
                h_netas = round(horas_totales_dia, 1)
                
                es_fer = fecha in st.session_state['feriados']
                txt_feriado = " [FERIADO TRABAJADO]" if es_fer else ""
                
                lineas_reporte.append({
                    'Empleado': nom_final,
                    'Día': f_str,
                    'Rango Horario': rango_horario_completo,
                    'Horas Calculadas': f"{h_netas} h",
                    'Detalle Extra': txt_feriado,
                    'horas_valor': horas_totales_dia
                })
                
            df_reporte_limpio = pd.DataFrame(lineas_reporte)
            
            total_horas_periodo = df_reporte_limpio['horas_valor'].sum()
            st.markdown(f"<div style='background-color:#1E381F; padding:20px; border-radius:10px; margin-bottom:25px; text-align:center;'> "
                        f"<h1 style='color:white; margin:0;'>TOTAL ACUMULADO: {round(total_horas_periodo, 1)} Horas</h1>"
                        f"</div>", unsafe_allow_html=True)
            
            st.subheader("📋 Vista de Marcas en Limpio")
            
            def destacar_feriados(row):
                return ['background-color: #CCE5FF; color: #004085; font-weight: bold;' if row['Detalle Extra'] != '' else '' for _ in row]
                
            st.dataframe(df_reporte_limpio[['Empleado', 'Día', 'Rango Horario', 'Horas Calculadas', 'Detalle Extra']].style.apply(destacar_feriados, axis=1), use_container_width=True, hide_index=True)

# =========================================================================
# SECCIÓN 4: RECEPTOR DE ARCHIVOS
# =========================================================================
elif seccion == "📥 CARGAR ARCHIVO":
    st.header("📥 Carga de Archivos de Fichajes (Prosoft)")
    st.markdown("Subí el reporte generado por el reloj para actualizar el sistema de manera inmediata.")
    
    file_upload = st.file_uploader("Seleccionar archivo .txt:", type=["txt"])
    
    if file_upload is not None:
        df_nuevos_datos = parsear_prosoft_txt(file_upload)
        
        if not df_nuevos_datos.empty:
            st.session_state['fichajes_raw'] = df_nuevos_datos
            st.success(f"¡Sincronización interna completada! Se leyeron exitosamente {len(df_nuevos_datos)} marcas horarias.")
            
            df_mostrar = df_nuevos_datos.copy()
            df_mostrar['hora'] = df_mostrar['hora'].dt.strftime('%H:%M:%S')
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
        else:
            st.error("El formato del archivo no contiene registros legibles de legajos y tiempos.")
