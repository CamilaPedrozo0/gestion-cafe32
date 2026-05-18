import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os

# --- CONFIGURACIÓN E INTERFAZ LIMPIA ---
st.set_page_config(page_title="Gestión Café 32", page_icon="☕", layout="wide")

# Ocultar menús técnicos de Streamlit para que parezca una web oficial
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {background-color: #2c3e50;}
    /* Texto blanco para legibilidad en modo oscuro */
    .stMarkdown, p, h1, h2, h3, label {color: #ffffff !important;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# --- CONEXIÓN A BASE DE DATOS (PERMANENTE Y APTA PARA LA NUBE) ---
# Si está en la nube de Streamlit, usa la carpeta temporal /tmp para evitar el OperationalError
if os.path.exists('/tmp'):
    db_path = '/tmp/cafe32_database.db'
else:
    db_path = 'cafe32_database.db'

conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS empleados (legajo INTEGER PRIMARY KEY, nombre TEXT, puesto TEXT, email TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS reportes (id INTEGER PRIMARY KEY AUTOINCREMENT, legajo INTEGER, fecha DATE, entrada TEXT, salida TEXT, total_segundos INTEGER)')
conn.commit()

# Función para ver el tiempo exacto en HH:MM:SS
def formatear_segundos(segundos):
    hrs = int(segundos // 3600)
    mins = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    return f"{hrs:02d}:{mins:02d}:{segs:02d}"

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

# --- BARRA LATERAL CON TU NUEVA TAZA ---
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
    df_emp = pd.read_sql_query("SELECT * FROM empleados", conn)
    df_rep = pd.read_sql_query("SELECT * FROM reportes", conn)
    
    col1, col2 = st.columns(2)
    col1.metric("Empleados en Base", len(df_emp))
    total_s = df_rep['total_segundos'].sum() if not df_rep.empty else 0
    col2.metric("Total Horas Registradas", formatear_segundos(total_s))
    
    st.subheader("Últimos Registros")
    st.dataframe(df_rep.tail(10), use_container_width=True)

elif menu == "👤 Base de Empleados":
    st.header("Gestión de Personal")
    with st.expander("➕ Agregar Nuevo Empleado"):
        with st.form("nuevo_emp"):
            l = st.number_input("Número de Legajo (según Prosoft)", min_value=1, step=1)
            n = st.text_input("Nombre completo")
            p = st.text_input("Puesto / Función")
            e = st.text_input("Correo electrónico")
            if st.form_submit_button("Guardar Empleado"):
                c.execute("INSERT OR REPLACE INTO empleados VALUES (?,?,?,?)", (l, n, p, e))
                conn.commit()
                st.success(f"Empleado {n} guardado.")
    
    st.subheader("Nómina Actual (Guardada en Base de Datos)")
    st.dataframe(pd.read_sql_query("SELECT * FROM empleados", conn), use_container_width=True)

elif menu == "📤 Cargar Reporte USB":
    st.header("Importar Datos de Reloj Prosoft")
    archivo = st.file_uploader("Sube el archivo Excel aquí", type=['xlsx'])
    
    if archivo:
        st.info("Archivo detectado. Listo para procesar.")
        if st.button("Procesar y Guardar Permanente"):
            try:
                df = pd.read_excel(archivo, header=None, skiprows=2, usecols='A:E')
                df.columns = ['Legajo', 'Fecha', 'Hora', 'Estado', 'Nombre']
                registros_cargados = 0
                
                for legajo, group in df.groupby('Legajo'):
                    c.execute("SELECT legajo FROM empleados WHERE legajo=?", (int(legajo),))
                    if c.fetchone():
                        for fecha, dia_group in group.groupby('Fecha'):
                            entrada = dia_group[dia_group['Estado'].str.contains('Entrada', case=False, na=False)]['Hora'].min()
                            salida = dia_group[dia_group['Estado'].str.contains('Salida', case=False, na=False)]['Hora'].max()
                            
                            if pd.notnull(entrada) and pd.notnull(salida):
                                fmt = '%H:%M:%S'
                                t1 = datetime.strptime(str(entrada), fmt)
                                t2 = datetime.strptime(str(salida), fmt)
                                if t2 < t1:
                                    t2 += timedelta(days=1)
                                    
                                segundos_trabajados = int((t2 - t1).total_seconds())
                                fecha_str = pd.to_datetime(fecha).date().strftime('%Y-%m-%d')
                                
                                c.execute("""INSERT INTO reportes (legajo, fecha, entrada, salida, total_segundos) 
                                             VALUES (?, ?, ?, ?, ?)""", 
                                          (int(legajo), fecha_str, str(entrada), str(salida), segundos_trabajados))
                                registros_cargados += 1
                                
                conn.commit()
                if registros_cargados > 0:
                    st.success(f"¡Éxito! Se procesaron y guardaron {registros_cargados} jornadas de trabajo.")
                else:
                    st.warning("Se leyó el archivo pero ningún número de legajo coincidía con los Empleados registrados. Recuerda cargarlos primero en la pestaña '👤 Base de Empleados'.")
            except Exception as e:
                st.error(f"Hubo un problema al leer la estructura del Excel: {e}")

elif menu == "🔍 Historial Detallado":
    st.header("Consulta de Tiempos Exactos")
    leg = st.number_input("Legajo del Empleado", min_value=1)
    f1 = st.date_input("Desde")
    f2 = st.date_input("Hasta")
    
    if st.button("Calcular Tiempo Exacto"):
        query = f"SELECT * FROM reportes WHERE legajo={leg} AND fecha BETWEEN '{f1}' AND '{f2}'"
        res = pd.read_sql_query(query, conn)
        if not res.empty:
            segundos_totales = res['total_segundos'].sum()
            st.markdown(f"### Total Trabajado: **{formatear_segundos(segundos_totales)}**")
            st.table(res[['fecha', 'entrada', 'salida']])
        else:
            st.warning("No hay registros para este legajo en las fechas seleccionadas.")
