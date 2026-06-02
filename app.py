import streamlit as st
import pandas as pd
import datetime
import calendar

# =========================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS (Color institucional #1E381F)
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
        /* Estilos para el calendario estilo oficina */
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
# INITIALIZATION DE VARIABLES DE SESIÓN (PERSISTENCIA)
# =========================================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if 'empleados' not in st.session_state:
    # Carga inicial con los 12 empleados fijos solicitados
    st.session_state['empleados'] = pd.DataFrame([
        {'legajo': 1, 'nombre': 'Camila', 'puesto': 'Barista'},
        {'legajo': 2, 'nombre': 'Jennifer', 'puesto': 'Cocina'},
        {'legajo': 3, 'nombre': 'Joel', 'puesto': 'Panadero'},
        {'legajo': 4, 'nombre': 'Ariana', 'puesto': 'Moza'},
        {'legajo': 5, 'nombre': 'Axel', 'puesto': 'Barista'},
        {'legajo': 6, 'nombre': 'Valentin', 'puesto': 'Cocinero'},
        {'legajo': 7, 'nombre': 'Pepi', 'puesto': 'Cocinero'},
        {'legajo': 8, 'nombre': 'Israel', 'puesto': 'Mozo'},
        {'legajo': 9, 'nombre': 'Lucia', 'puesto': 'Moza'},
        {'legajo': 10, 'nombre': 'Priscila', 'puesto': 'Moza'},
        {'legajo': 11, 'nombre': 'Candela', 'puesto': 'Moza'},
        {'legajo': 13, 'nombre': 'Valentina', 'puesto': 'Pastelera'}
    ])

if 'fichajes_raw' not in st.session_state:
    st.session_state['fichajes_raw'] = pd.DataFrame(columns=['legajo', 'fecha', 'hora', 'es_feriado'])

if 'feriados' not in st.session_state:
    # Base inicial de feriados (se pueden añadir dinámicamente)
    st.session_state['feriados'] = [
        datetime.date(2026, 1, 1),   # Año Nuevo
        datetime.date(2026, 3, 24),  # Memoria
        datetime.date(2026, 4, 2),   # Malvinas
        datetime.date(2026, 5, 1),   # Día del Trabajo
        datetime.date(2026, 5, 25),  # Revolución de Mayo
        datetime.date(2026, 6, 20),  # Día de la Bandera
        datetime.date(2026, 7, 9)    # Independencia
    ]

# =========================================================================
# PANTALLA DE ACCESO (LOGIN OBLIGATORIO)
# =========================================================================
if not st.session_state['autenticado']:
  st.subheader("Acceso restringido")
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
    # Enlace directo solicitado a Google Sheets
    st.markdown("### 🔗 Acceso Externo")
    st.markdown("[📊 Abrir Google Sheets](https://docs.google.com/spreadsheets/d/1veKrncoLJmYwxXrnEOdVembeiXT9oL9nm9le-r1ZpRg/edit?usp=sharing)", unsafe_allow_html=True)

# =========================================================================
# MOTOR DE PROCESAMIENTO DE ARCHIVOS PROSOFT (.TXT)
# =========================================================================
def parsear_prosoft_txt(file_upload):
    # Corrección clave para evitar el AttributeError en Streamlit
    contenido = file_upload.getvalue().decode("utf-8")
    registros = []
    
    for linea in contenido.splitlines():
        # Limpiar espacios extraños (como \xa0) y quitar el punto final
        linea_limpia = linea.replace('\xa0', ' ').strip().rstrip('.')
        if not linea_limpia or "UDISKLOG" in linea_limpia or "DateTime" in linea_limpia or "Mchn" in linea_limpia:
            continue
            
        partes = linea_limpia.split()
        if len(partes) < 7:
            continue
            
        try:
            # En tu formato, el legajo limpio está en la tercera columna (índice 2)
            # Ejemplo: '000000010' se convierte automáticamente en el entero 10
            legajo = int(partes[2])
            
            # La fecha y hora están al final de la línea debido a la separación por espacios
            fecha_str = partes[-2]  # Ejemplo: '2026/05/01'
            hora_str = partes[-1]   # Ejemplo: '07:00:00'
            
            # Conversión estricta a tipos de datos nativos
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
            # Ignora líneas de encabezados residuales o con datos corruptos
            continue
                
    return pd.DataFrame(registros)
# =========================================================================
# SECCIÓN 1: EMPLEADOS (AGREGAR / EDITAR)
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
                    # Si el legajo ya existe, se elimina la versión previa para actualizarlo
                    df_emp = df_emp[df_emp['legajo'] != legajo_input]
                    
                    nueva_linea = pd.DataFrame([{'legajo': int(legajo_input), 'nombre': nombre_input.strip(), 'puesto': puesto_input.strip()}])
                    st.session_state['empleados'] = pd.concat([df_emp, nueva_linea], ignore_index=True)
                    st.success(f"Empleado Guardado: Legajo {legajo_input} - {nombre_input}")
                    st.rerun()

    st.markdown("### Nómina Guardada en el Sistema")
    st.dataframe(st.session_state['empleados'].sort_values('legajo'), use_container_width=True, hide_index=True)

# =========================================================================
# SECCIÓN 2: CALENDARIO DE OFICINA (DOBLE COLOR + FERIADOS DE CONTROL)
# =========================================================================
elif seccion == "📅 CALENDARIO":
    st.header("📅 Calendario Mensual de Turnos")
    
    df_fichajes = st.session_state['fichajes_raw']
    
    col_c1, col_c2 = st.columns(2)
    anio_sel = col_c1.selectbox("Año:", [2026, 2027, 2025], index=0)
    mes_sel = col_c2.selectbox("Mes:", list(range(1, 13)), index=datetime.date.today().month - 1)
    
    # Procesar turnos por día si hay marcas cargadas
    marcas_del_mes = {}
    if not df_fichajes.empty:
        df_fichajes['fecha_dt'] = pd.to_datetime(df_fichajes['fecha'])
        df_mes = df_fichajes[(df_fichajes['fecha_dt'].dt.year == anio_sel) & (df_fichajes['fecha_dt'].dt.month == mes_sel)]
        
        if not df_mes.empty:
            # Entrada es la hora mínima del empleado en el día
            entradas = df_mes.groupby(['fecha', 'legajo'])['hora'].min().reset_index()
            df_nombres = st.session_state['empleados']
            entradas = pd.merge(entradas, df_nombres, on='legajo', how='left')
            
            for _, row in entradas.iterrows():
                dia = row['fecha'].day
                nombre_emp = row['nombre'] if pd.notna(row['nombre']) else f"Legajo {row['legajo']}"
                hora_entrada = row['hora'].time()
                
                # Clasificación de color por horario de entrada solicitado
                if 7 <= hora_entrada.hour < 11:
                    tipo_turno = "manana"
                else:
                    tipo_turno = "tarde"
                    
                es_fer = row['fecha'] in st.session_state['feriados']
                
                if dia not in marcas_del_mes:
                    marcas_del_mes[dia] = []
                marcas_del_mes[dia].append({'nombre': nombre_emp, 'turno': tipo_turno, 'feriado': es_fer})

    # Renderizador del calendario estructural cuadrado
    cal = calendar.Calendar(firstweekday=6) # Comienza en Domingo
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
                
                # Si el día es feriado, agregar indicador visual general
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
# SECCIÓN 3: GESTIÓN DE HORAS NETAS Y FILTRO ESPECÍFICO
# =========================================================================
elif seccion == "📊 GESTION HORAS":
    st.header("📊 Resumen Diario Límpio y Horas Acumuladas")
    
    df_fichajes = st.session_state['fichajes_raw']
    
    if df_fichajes.empty:
        st.warning("No hay registros en memoria. Cargá un archivo .txt en la pestaña correspondiente.")
    else:
        col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
        f_inicio = col_f1.date_input("Fecha Inicial de Cálculo:", value=df_fichajes['fecha'].min())
        f_fin = col_f2.date_input("Fecha Final de Cálculo:", value=df_fichajes['fecha'].max())
        
        # Filtro opcional por legajo específico
        opciones_emp = {0: "TODOS LOS EMPLEADOS"}
        for _, r in st.session_state['empleados'].iterrows():
            opciones_emp[r['legajo']] = f"Legajo {r['legajo']} - {r['nombre']}"
            
        legajo_sel = col_f3.selectbox("Filtrar por Empleado Específico:", options=list(opciones_emp.keys()), format_func=lambda x: opciones_emp[x])

        # Filtrar datos por el rango temporal
        mask = (df_fichajes['fecha'] >= f_inicio) & (df_fichajes['fecha'] <= f_fin)
        df_filtrado = df_fichajes[mask]
        
        if legajo_sel != 0:
            df_filtrado = df_filtrado[df_filtrado['legajo'] == legajo_sel]

        if df_filtrado.empty:
            st.info("Sin registros para los filtros seleccionados.")
        else:
            # Agrupar por empleado y día para obtener el cálculo limpio (Max - Min)
            agrupado = df_filtrado.groupby(['legajo', 'fecha'])['hora'].agg(['min', 'max']).reset_index()
            agrupado['horas_num'] = (agrupado['max'] - agrupado['min']).dt.total_seconds() / 3600
            
            # Incorporar nombres y feriados
            agrupado = pd.merge(agrupado, st.session_state['empleados'], on='legajo', how='left')
            agrupado['es_feriado'] = agrupado['fecha'].apply(lambda x: x in st.session_state['feriados'])
            
            # Formatear salida estructurada limpia
            lineas_reporte = []
            for _, row in agrupado.iterrows():
                nom_final = row['nombre'] if pd.notna(row['nombre']) else f"Desconocido (Leg. {row['legajo']})"
                f_str = row['fecha'].strftime('%d/%m')
                e_str = row['min'].strftime('%H:%M')
                s_str = row['max'].strftime('%H:%M')
                h_netas = round(row['horas_num'], 1)
                
                txt_feriado = " [FERIADO TRABAJADO]" if row['es_feriado'] else ""
                lineas_reporte.append({
                    'Empleado': nom_final,
                    'Día': f_str,
                    'Rango Horario': f"{e_str} a {s_str}",
                    'Horas Calculadas': f"{h_netas} h",
                    'Detalle Extra': txt_feriado,
                    'horas_valor': row['horas_num']
                })
                
            df_reporte_limpio = pd.DataFrame(lineas_reporte)
            
            # Indicadores numéricos grandes en pantalla
            total_horas_periodo = df_reporte_limpio['horas_valor'].sum()
            st.markdown(f"<div style='background-color:#1E381F; padding:20px; border-radius:10px; margin-bottom:25px; text-align:center;'>"
                        f"<h1 style='color:white; margin:0;'>TOTAL ACUMULADO: {round(total_horas_periodo, 1)} Horas</h1>"
                        f"</div>", unsafe_allow_html=True)
            
            st.subheader("📋 Vista de Marcas en Limpio")
            
            # Mostrar tabla con color azul destacado para registros de feriados
            def destacar_feriados(row):
                return ['background-color: #CCE5FF; color: #004085; font-weight: bold;' if row['Detalle Extra'] != '' else '' for _ in row]
                
            st.dataframe(df_reporte_limpio[['Empleado', 'Día', 'Rango Horario', 'Horas Calculadas', 'Detalle Extra']].style.apply(destacar_feriados, axis=1), use_container_width=True, hide_index=True)

# =========================================================================
# SECCIÓN 4: RECEPTOR DE ARCHIVOS
# =========================================================================
# =========================================================================
# SECCIÓN 4: RECEPTOR DE ARCHIVOS Y COMPARTIDO AUTOMÁTICO A GOOGLE SHEETS
# =========================================================================
elif seccion == "📥 CARGAR ARCHIVO":
    st.header("📥 Carga de Archivos de Fichajes (Prosoft)")
    st.markdown("Subí el reporte generado por el reloj para actualizar el sistema y sincronizar con Google Sheets.")
    
    file_upload = st.file_uploader("Seleccionar archivo .txt:", type=["txt"])
    
    if file_upload is not None:
        df_nuevos_datos = parsear_prosoft_txt(file_upload)
        
        if not df_nuevos_datos.empty:
            st.session_state['fichajes_raw'] = df_nuevos_datos
            st.success(f"¡Sincronización interna completada! Se leyeron {len(df_nuevos_datos)} marcas.")
            
            # --- MOTOR DE CARGA AUTOMÁTICA A GOOGLE SHEETS ---
            st.info("🔄 Subiendo datos procesados a la pestaña 'reportes' de Google Sheets...")
            try:
                from streamlit_gsheets import GSheetsConnection
                
                # Conectar usando el secreto del sistema
                conn = st.connection("gsheets", type=GSheetsConnection)
                
                # 1. Preparar el cálculo neto diario igual que en la pestaña de gestión para subirlo limpio
                df_calculado = df_nuevos_datos.groupby(['legajo', 'fecha'])['hora'].agg(['min', 'max']).reset_index()
                df_calculado['tiempo_trabajado'] = ((df_calculado['max'] - df_calculado['min']).dt.total_seconds() / 3600).round(2)
                
                # Formatemos las columnas para que coincidan con tu Excel
                df_para_sheets = pd.DataFrame({
                    'id': range(1, len(df_calculado) + 1),
                    'legajo': df_calculado['legajo'],
                    'fecha': df_calculado['fecha'].astype(str),
                    'entrada': df_calculado['min'].dt.strftime('%H:%M:%S'),
                    'salida': df_calculado['max'].dt.strftime('%H:%M:%S'),
                    'tiempo_trabajado': df_calculado['tiempo_trabajado'],
                    'tipo_dia': df_calculado['fecha'].apply(lambda x: 'Feriado' if x in st.session_state['feriados'] else 'Normal')
                })
                
                # 2. Guardar datos directamente en la pestaña "reportes"
                conn.update(worksheet="reportes", data=df_para_sheets)
                st.success("✨ ¡Sincronización Exitosa! Los datos ya están guardados en tu Google Sheets.")
                
            except Exception as e:
                st.error(f"No se pudo automatizar la subida a Sheets. Error: {e}")
                st.info("Asegurate de tener instalada la librería 'streamlit-google-sheets-connection' en tu archivo requirements.txt")
            
            # Mostrar resumen de control en pantalla
            st.dataframe(df_nuevos_datos, use_container_width=True, hide_index=True)
        else:
            st.error("El formato del archivo no contiene registros legibles de legajos y tiempos.")
