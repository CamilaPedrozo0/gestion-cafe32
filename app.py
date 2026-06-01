import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import io
import re

# --- CONFIGURACIÓN E INTERFAZ LIMPIA ---
st.set_page_config(page_title="Gestión Café 32", page_icon="☕", layout="wide")

# Forzamos el modo oscuro real y congelamos el diseño visual
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fondo principal oscuro de la app */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0e1117 !important;
    }
    
    /* Barra lateral izquierda fija y oscura */
    [data-testid="stSidebar"] {
        background-color: #1c2331 !important;
        min-width: 260px !important;
    }
    
    /* Forzar texto blanco en toda la aplicación y barra lateral */
    .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, span, div, .stMetric * {
        color: #ffffff !important;
    }
    
    /* Asegurar lectura de las opciones del Menú desplegable */
    div[data-baseweb="select"] * {
        color: #000000 !important;
    }
    
    /* Botones visibles con texto oscuro bien definido */
    .stButton>button {
        color: #000000 !important;
        background-color: #f0f2f6 !important;
        font-weight: bold !important;
    }
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# --- CONEXIÓN COMPARTIDA A GOOGLE SHEETS ---
# COLOCÁ ACÁ TU ID LARGO DE GOOGLE SHEETS:
ID_DE_TU_HOJA = "TU_ID_AQUÍ" 

URL_EMPLEADOS = f"https://docs.google.com/spreadsheets/d/{ID_DE_TU_HOJA}/gviz/tq?tqx=out:csv&sheet=empleados"
URL_REPORTES = f"https://docs.google.com/spreadsheets/d/{ID_DE_TU_HOJA}/gviz/tq?tqx=out:csv&sheet=reportes"

# --- BASE DE FERIADOS NACIONALES ARGENTINA (2026) ---
FERIADOS_2026 = {
    date(2026, 1, 1): "Año Nuevo",
    date(2026, 2, 16): "Carnaval",
    date(2026, 2, 17): "Carnaval",
    date(2026, 3, 24): "Día de la Memoria",
    date(2026, 4, 2): "Día del Veterano y de los Caídos en la Guerra de Malvinas",
    date(2026, 4, 3): "Viernes Santo",
    date(2026, 5, 1): "Día del Trabajador",
    date(2026, 5, 25): "Día de la Revolución de Mayo",
    date(2026, 6, 20): "Paso a la Inmilitaridad del Gral. Manuel Belgrano",
    date(2026, 7, 9): "Día de la Declaración de la Independencia",
    date(2026, 8, 17): "Paso a la Inmortalidad del Gral. José de San Martín",
    date(2026, 10, 12): "Día de la Diversidad Cultural",
    date(2026, 11, 20): "Día de la Soberanía Nacional",
    date(2026, 12, 8): "Inmaculada Concepción de María",
    date(2026, 12, 25): "Navidad"
}

def es_feriado(fecha_obj):
    return FERIADOS_2026.get(fecha_obj, None)

def determinar_turno(hora_entrada_str):
    try:
        hora = int(hora_entrada_str.split(':')[0])
        return "Mañana" if 7 <= hora < 11 else "Tarde"
    except:
        return "Indefinido"

def cargar_empleados():
    try:
        df = pd.read_csv(URL_EMPLEADOS)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        return df
    except:
        return pd.DataFrame(columns=['legajo', 'nombre', 'puesto', 'email'])

def cargar_reportes():
    try:
        df = pd.read_csv(URL_REPORTES)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        return df
    except:
        return pd.DataFrame(columns=['id', 'legajo', 'fecha', 'entrada', 'salida', 'tiempo_trabajado', 'tipo_dia'])

def formatear_segundos(segundos):
    hrs = int(segundos // 3600)
    mins = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    return f"{hrs:02d}:{mins:02d}:{segs:02d}"

def convertir_a_segundos(tiempo_str):
    try:
        partes = list(map(int, str(tiempo_str).split(':')))
        if len(partes) == 3:
            return partes[0] * 3600 + partes[1] * 60 + partes[2]
        return 0
    except:
        return 0

# --- LOGIN SEGURO ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>☕ Café 32</h1>", unsafe_allow_html=True)
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            if user == "admin" and pw == "cafe32":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    st.stop()

# --- BARRA LATERAL FIJA ---
st.sidebar.markdown("<h2 style='text-align: center; color: white;'>☕ Café 32</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = st.sidebar.selectbox(
    "Ir a:", 
    ["📊 Resumen General", "📅 Calendario de Turnos", "👤 Base de Empleados", "📤 Cargar Reporte USB", "🔍 Historial Detallado"]
)

# --- LÓGICA DE LAS SECCIONES ---

if menu == "📊 Resumen General":
    st.header("Resumen del Sistema")
    df_emp = cargar_empleados()
    df_rep = cargar_reportes()
    
    st.metric("Personal Activo Registrado", len(df_emp))
    st.subheader("Últimos Fichajes Procesados")
    if not df_rep.empty:
        try:
            vista_rep = df_rep.tail(15)[['legajo', 'fecha', 'entrada', 'salida']].copy()
            vista_rep.columns = ['Legajo', 'Fecha', 'Hora Entrada', 'Hora Salida']
            st.dataframe(vista_rep, use_container_width=True, hide_index=True)
        except:
            st.info("Estructura detectada. Esperando registros en tu Google Sheets.")
    else:
        st.info("Aún no hay marcas de asistencia guardadas.")

elif menu == "📅 Calendario de Turnos":
    st.header("Planificación y Control de Turnos Diarios")
    df_emp = cargar_empleados()
    df_rep = cargar_reportes()
    
    if not df_rep.empty and not df_emp.empty:
        st.subheader("Filtro de visualización")
        fecha_cal = st.date_input("Selecciona una fecha para ver los turnos:", value=date.today())
        
        nombre_feriado = es_feriado(fecha_cal)
        if nombre_feriado:
            st.markdown(f"<div style='background-color: #1e3a8a; padding: 15px; border-radius: 5px; margin-bottom: 15px;'><h4 style='margin:0;'>🔵 ¡DÍA FERIADO NACIONAL!: {nombre_feriado}</h4></div>", unsafe_allow_html=True)
        
        df_rep['fecha_dt'] = pd.to_datetime(df_rep['fecha']).dt.date
        fichajes_dia = df_rep[df_rep['fecha_dt'] == fecha_cal]
        
        df_merge = pd.merge(fichajes_dia, df_emp, on='legajo', how='left')
        
        col_m, col_t = st.columns(2)
        with col_m:
            st.markdown("### 🌅 Turno Mañana (Entradas 7am a 11am)")
            manana_data = [{"Empleado": fila['nombre'] if pd.notna(fila['nombre']) else f"Legajo {fila['legajo']}", "Entrada": fila['entrada'], "Salida": fila['salida']} for _, fila in df_merge.iterrows() if determinar_turno(fila['entrada']) == "Mañana"]
            if manana_data: st.dataframe(pd.DataFrame(manana_data), use_container_width=True, hide_index=True)
            else: st.caption("No hay empleados en el turno mañana.")
                
        with col_t:
            st.markdown("### 🌇 Turno Tarde (Entradas después de las 11am)")
            tarde_data = [{"Empleado": fila['nombre'] if pd.notna(fila['nombre']) else f"Legajo {fila['legajo']}", "Entrada": fila['entrada'], "Salida": fila['salida']} for _, fila in df_merge.iterrows() if determinar_turno(fila['entrada']) == "Tarde"]
            if tarde_data: st.dataframe(pd.DataFrame(tarde_data), use_container_width=True, hide_index=True)
            else: st.caption("No hay empleados en el turno tarde.")
    else:
        st.warning("Se necesita cargar empleados y reportes previos en tu Google Sheets.")

elif menu == "👤 Base de Empleados":
    st.header("Gestión de Personal")
    df_emp = cargar_empleados()
    st.markdown(f"[➡️ Abrir tu Google Sheets](https://docs.google.com/spreadsheets/d/{ID_DE_TU_HOJA})")
    
    st.subheader("Nómina Actual de Empleados")
    if not df_emp.empty:
        st.dataframe(df_emp, use_container_width=True, hide_index=True)
    else:
        st.warning("No hay empleados registrados en tu planilla de Google.")

elif menu == "📤 Cargar Reporte USB":
    st.header("Importar Datos de Reloj Fichador (.txt / .xlsx)")
    archivo = st.file_uploader("Sube el archivo aquí", type=['xlsx', 'txt'])
    df_emp = cargar_empleados()
    
    if archivo:
        st.info("Archivo detectado. Listo para procesar.")
        if st.button("Procesar y Calcular Horarios"):
            try:
                df = None
                nombre_archivo = archivo.name.lower()
                
                if nombre_archivo.endswith('.xlsx'):
                    df = pd.read_excel(archivo, header=None, skiprows=2, usecols='A:E')
                    df.columns = ['Legajo', 'Fecha', 'Hora', 'Estado', 'Nombre']
                    df['Legajo'] = df['Legajo'].astype(int)
                
                elif nombre_archivo.endswith('.txt'):
                    contenido = archivo.getvalue().decode("utf-8")
                    df_procesado = []
                    
                    # PROCESADOR SEGURO LÍNEA POR LÍNEA CONTRA EL ERROR DE CAMPOS
                    for linea in contenido.splitlines():
                        linea = linea.strip()
                        if not linea: continue
                        partes = re.split(r'\s+', linea)
                        
                        indice_fecha = -1
                        for i, parte in enumerate(partes):
                            if '/' in parte and len(parte) >= 8:
                                indice_fecha = i
                                break
                                
                        if indice_fecha != -1 and len(partes) > (indice_fecha + 1):
                            try:
                                legajo_int = None
                                for p in partes[:indice_fecha]:
                                    if p.isdigit(): legajo_int = int(p)
                                if legajo_int is None: continue
                                    
                                fecha_str = partes[indice_fecha].replace('/', '-')
                                hora_str = partes[indice_fecha + 1].replace('.', ':')
                                if len(hora_str) == 5: hora_str += ":00"
                                    
                                datetime.strptime(hora_str, '%H:%M:%S')
                                df_procesado.append({'Legajo': legajo_int, 'Fecha': fecha_str, 'Hora': hora_str})
                            except: continue
                    
                    df = pd.DataFrame(df_procesado)

                if df is not None and not df.empty:
                    jornadas_calculadas = []
                    for (legajo, fecha), group in df.groupby(['Legajo', 'Fecha']):
                        horas_ordenadas = sorted(group['Hora'].tolist())
                        entrada, salida = horas_ordenadas[0], horas_ordenadas[-1]
                        if entrada == salida: continue 
                            
                        t1 = datetime.strptime(entrada, '%H:%M:%S')
                        t2 = datetime.strptime(salida, '%H:%M:%S')
                        segundos_trabajados = int((t2 - t1).total_seconds())
                        
                        try:
                            fecha_partes = list(map(int, fecha.split('-')))
                            if fecha_partes[0] < 100: fecha_partes[0] += 2000
                            fecha_obj = date(fecha_partes[0], fecha_partes[1], fecha_partes[2])
                            nombre_f = es_feriado(fecha_obj)
                        except: nombre_f = None
                        
                        jornadas_calculadas.append({
                            'legajo': legajo, 'fecha': fecha, 'entrada': entrada, 'salida': salida,
                            'tiempo_trabajado': formatear_segundos(segundos_trabajados),
                            'tipo_dia': f"Feriado: {nombre_f}" if nombre_f else "Normal"
                        })
                    
                    if jornadas_calculadas:
                        st.success("¡Archivo procesado con éxito!")
                        df_res_final = pd.DataFrame(jornadas_calculadas)
                        st.dataframe(df_res_final, use_container_width=True, hide_index=True)
                        st.caption("💡 Copiá estas filas a tu pestaña 'reportes' de Google Sheets.")
                    else:
                        st.warning("No se encontraron marcas de entrada/salida completas.")
                else:
                    st.error("No se pudo extraer información del archivo.")
            except Exception as e:
                st.error(f"Error de procesamiento: {e}")

elif menu == "🔍 Historial Detallado":
    st.header("Consulta de Tiempos Exactos")
    leg = st.number_input("Legajo del Empleado", min_value=1, step=1)
    f1 = st.date_input("Desde")
    f2 = st.date_input("Hasta")
    
    if st.button("Calcular Tiempo Exacto"):
        df_rep = cargar_reportes()
        if not df_rep.empty:
            try:
                df_rep['legajo'] = df_rep['legajo'].astype(int)
                df_rep['fecha'] = pd.to_datetime(df_rep['fecha']).dt.date
                res = df_rep[(df_rep['legajo'] == leg) & (df_rep['fecha'] >= f1) & (df_rep['fecha'] <= f2)]
                
                if not res.empty:
                    segundos_totales, segundos_feriados = 0, 0
                    for _, fila in res.iterrows():
                        t = fila['tiempo_trabajado']
                        seg = convertir_a_segundos(t) if ':' in str(t) else (int(t) if pd.notna(t) else 0)
                        segundos_totales += seg
                        if 'tipo_dia' in res.columns and "Feriado" in str(fila['tipo_dia']):
                            segundos_feriados += seg
                    
                    st.markdown(f"### Tiempo total cumplido: `{formatear_segundos(segundos_totales)}`")
                    if segundos_feriados > 0:
                        st.markdown(f"Total Horas en Feriados: `{formatear_segundos(segundos_feriados)}`")
                    st.dataframe(res[['fecha', 'entrada', 'salida', 'tiempo_trabajado']], use_container_width=True, hide_index=True)
                else:
                    st.warning("No hay registros guardados para este legajo.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("La base de datos en Google Sheets está vacía.")
