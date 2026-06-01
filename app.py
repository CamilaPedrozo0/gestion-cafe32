import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import re

# --- CONFIGURACIÓN E INTERFAZ LIMPIA ---
st.set_page_config(page_title="Gestión Café 32", page_icon="☕", layout="wide")

hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {background-color: #2c3e50;}
    .stMarkdown, p, h1, h2, h3, label {color: #ffffff !important;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# --- CONEXIÓN COMPARTIDA A GOOGLE SHEETS ---
# COLOCÁ ACÁ TU ID LARGO DE GOOGLE SHEETS:
ID_DE_TU_HOJA = "TU_ID_AQUÍ" 

URL_EMPLEADOS = f"https://docs.google.com/spreadsheets/d/{ID_DE_TU_HOJA}/gviz/tq?tqx=out:csv&sheet=empleados"
URL_REPORTES = f"https://docs.google.com/spreadsheets/d/{ID_DE_TU_HOJA}/gviz/tq?tqx=out:csv&sheet=reportes"

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
        return pd.DataFrame(columns=['id', 'legajo', 'fecha', 'entrada', 'salida', 'tiempo_trabajado'])

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

# --- BARRA LATERAL ---
try:
    st.sidebar.image("logo.png", use_container_width=True)
except:
    st.sidebar.markdown("<h1 style='text-align: center;'>☕</h1>", unsafe_allow_html=True)

st.sidebar.markdown("<h2 style='text-align: center; color: white;'>Café 32</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = st.sidebar.selectbox("Ir a:", ["📊 Resumen General", "👤 Base de Empleados", "📤 Cargar Reporte USB", "🔍 Historial Detallado"])

# --- LÓGICA DE LAS SECCIONES ---

if menu == "📊 Resumen General":
    st.header("Resumen del Sistema")
    df_emp = cargar_empleados()
    df_rep = cargar_reportes()
    
    st.metric("Personal Activo Registrado", len(df_emp))
    st.subheader("Últimos Fichajes Procesados")
    if not df_rep.empty:
        vista_rep = df_rep.tail(15)[['legajo', 'fecha', 'entrada', 'salida']].copy()
        vista_rep.columns = ['Legajo', 'Fecha', 'Hora Entrada', 'Hora Salida']
        st.dataframe(vista_rep, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay marcas de asistencia guardadas.")

elif menu == "👤 Base de Empleados":
    st.header("Gestión de Personal")
    df_emp = cargar_empleados()
    
    st.info("💡 Recordá que para que no se borren nunca, los empleados se cargan directamente en tu Google Sheets en la pestaña 'empleados'.")
    st.markdown(f"[➡️ Abrir tu Google Sheets en Celular o PC](https://docs.google.com/spreadsheets/d/{ID_DE_TU_HOJA})")
    
    st.subheader("Nómina Actual de Empleados")
    if not df_emp.empty:
        vista_emp = df_emp.copy()
        vista_emp.columns = ['Legajo', 'Nombre Completo', 'Puesto / Función', 'Email']
        st.dataframe(vista_emp, use_container_width=True, hide_index=True)
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
                    
                    for linea in contenido.splitlines():
                        linea = linea.strip()
                        if not linea:
                            continue
                            
                        partes = re.split(r'\s+', linea)
                        indice_fecha = -1
                        for i, parte in enumerate(partes):
                            if '/' in parte and len(parte) >= 8:
                                indice_fecha = i
                                break
                                
                        if indice_fecha != -1 and indice_fecha >= 1:
                            try:
                                legajo_int = int(partes[2]) 
                                fecha_str = pandas_fecha = partes[indice_fecha].replace('/', '-')
                                hora_str = partes[indice_fecha + 1].replace('.', '')
                                datetime.strptime(hora_str, '%H:%M:%S')
                                
                                df_procesado.append({
                                    'Legajo': legajo_int,
                                    'Fecha': fecha_str,
                                    'Hora': hora_str
                                })
                            except:
                                continue
                    
                    df = pd.DataFrame(df_procesado)

                if df is not None and not df.empty:
                    jornadas_calculadas = []
                    
                    for (legajo, fecha), group in df.groupby(['Legajo', 'Fecha']):
                        if legajo in df_emp['legajo'].values:
                            horas_ordenadas = sorted(group['Hora'].tolist())
                            entrada = horas_ordenadas[0]
                            salida = horas_ordenadas[-1]
                            
                            if entrada == salida:
                                continue 
                                
                            fmt = '%H:%M:%S'
                            t1 = datetime.strptime(entrada, fmt)
                            t2 = datetime.strptime(salida, fmt)
                            segundos_trabajados = int((t2 - t1).total_seconds())
                            
                            jornadas_calculadas.append({
                                'Legajo': legajo,
                                'Fecha': fecha,
                                'Entrada': entrada,
                                'Salida': salida,
                                'Tiempo Real': formatear_segundos(segundos_trabajados)
                            })
                    
                    if jornadas_calculadas:
                        st.success("¡Archivo procesado con éxito!")
                        st.subheader("Resultados listos para revisar:")
                        st.dataframe(pd.DataFrame(jornadas_calculadas), use_container_width=True, hide_index=True)
                        st.caption("💡 Tip: Copiá estas filas a tu pestaña 'reportes' de Google Sheets para guardar el historial permanente.")
                    else:
                        st.warning("No se encontraron jornadas válidas o los legajos del archivo no coinciden con tus empleados de Google Sheets.")
                else:
                    st.error("No se pudo extraer información válida del archivo.")
            except Exception as e:
                st.error(f"Error al procesar: {e}")

elif menu == "🔍 Historial Detallado":
    st.header("Consulta de Tiempos Exactos")
    leg = st.number_input("Legajo del Empleado", min_value=1, step=1)
    f1 = st.date_input("Desde")
    f2 = st.date_input("Hasta")
    
    if st.button("Calcular Tiempo Exacto"):
        df_rep = cargar_reportes()
        if not df_rep.empty:
            df_rep['legajo'] = df_rep['legajo'].astype(int)
            df_rep['fecha'] = pd.to_datetime(df_rep['fecha']).dt.date
            
            res = df_rep[(df_rep['legajo'] == leg) & (df_rep['fecha'] >= f1) & (df_rep['fecha'] <= f2)]
            
            if not res.empty:
                # Sumamos el tiempo interpretando las horas cargadas en formato texto o segundos
                segundos_totales = 0
                for t in res['tiempo_trabajado']:
                    if ':' in str(t):
                        segundos_totales += convertir_a_segundos(t)
                    else:
                        try: segundos_totales += int(t)
                        except: pass
                        
                st.markdown(f"### Tiempo total cumplido: `{formatear_segundos(segundos_totales)}`")
                
                vista_final = res[['fecha', 'entrada', 'salida']].copy()
                vista_final.columns = ['Fecha', 'Hora Entrada', 'Hora Salida']
                st.table(vista_final)
            else:
                st.warning("No hay registros guardados para este legajo en esas fechas.")
        else:
            st.warning("La base de datos de reportes en Google Sheets está vacía.")
