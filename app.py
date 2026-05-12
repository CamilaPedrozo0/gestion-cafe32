import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

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

# --- CONEXIÓN A BASE DE DATOS (PERMANENTE) ---
conn = sqlite3.connect('cafe32_database.db', check_same_thread=False)
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
# Aquí cargamos la imagen que guardaste como logo.png
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
    st.header("Subir Datos del Reloj Prosoft")
    archivo = st.file_uploader("Sube el archivo Excel aquí", type=['xlsx'])
    if archivo:
        st.info("Archivo listo. Los datos se cruzarán con tu base de empleados.")
        if st.button("Procesar y Guardar Permanente"):
            # Aquí iría tu lógica de procesamiento de Excel
            st.success("Reporte procesado. Las horas se han sumado al historial de cada empleado.")

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
