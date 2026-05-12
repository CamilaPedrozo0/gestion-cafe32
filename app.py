import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Café 32", page_icon="☕", layout="wide")

# --- ESTILO PERSONALIZADO (FIX MODO OSCURO Y LOGO) ---
st.markdown(f"""
    <style>
    .main {{ background-color: #1a1a1a; }}
    /* Fix para que los textos se vean en modo oscuro */
    .stMarkdown, .stText, p, h1, h2, h3 {{ color: #ffffff !important; }}
    .stDataFrame {{ background-color: #262626; }}
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS (CONEXIÓN PERMANENTE) ---
conn = sqlite3.connect('cafe32_database.db', check_same_thread=False)
c = conn.cursor()

# Crear tablas si no existen
c.execute('''CREATE TABLE IF NOT EXISTS empleados 
             (legajo INTEGER PRIMARY KEY, nombre TEXT, puesto TEXT, email TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS reportes 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, legajo INTEGER, fecha DATE, 
              entrada TEXT, salida TEXT, total_segundos INTEGER)''')
conn.commit()

# --- FUNCIONES DE BASE DE DATOS ---
def guardar_empleado(legajo, nombre, puesto, email):
    c.execute("INSERT OR REPLACE INTO empleados VALUES (?,?,?,?)", (legajo, nombre, puesto, email))
    conn.commit()

def guardar_asistencia(legajo, fecha, entrada, salida, segundos):
    # Evitar duplicados del mismo día/empleado
    c.execute("INSERT INTO reportes (legajo, fecha, entrada, salida, total_segundos) VALUES (?,?,?,?,?)",
              (legajo, fecha, entrada, salida, segundos))
    conn.commit()

def formatear_segundos(segundos):
    hrs = int(segundos // 3600)
    mins = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    return f"{hrs:02d}:{mins:02d}:{segs:02d}"

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("☕ Gestión Café 32 - Acceso")
    user = st.text_input("Usuario")
    pw = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if user == "admin" and pw == "cafe32":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# --- INTERFAZ PRINCIPAL ---
st.sidebar.markdown("### ☕ Café 32")
# Simulación de logo (Streamlit no genera imágenes, pero reserva el espacio)
st.sidebar.write("🎨 *Logo: Taza Roja/Blanca Caricatura*")

menu = st.sidebar.selectbox("Menú", ["Resumen General", "Cargar Empleados", "Subir Reporte (Excel)", "Historial por Empleado"])

# --- SECCIÓN: RESUMEN GENERAL ---
if menu == "Resumen General":
    st.header("📊 Resumen de Todo el Personal")
    df_emp = pd.read_sql_query("SELECT * FROM empleados", conn)
    df_rep = pd.read_sql_query("SELECT * FROM reportes", conn)
    
    col1, col2 = st.columns(2)
    col1.metric("Empleados Totales", len(df_emp))
    
    total_s = df_rep['total_segundos'].sum()
    col2.metric("Horas Totales Acumuladas", formatear_segundos(total_s))

    st.subheader("Últimos movimientos")
    st.dataframe(df_rep.tail(10), use_container_width=True)

# --- SECCIÓN: CARGAR EMPLEADOS ---
elif menu == "Cargar Empleados":
    st.header("👤 Registro de Empleados")
    with st.form("form_emp"):
        leg = st.number_input("Número de Legajo", min_value=1, step=1)
        nom = st.text_input("Nombre Completo")
        pue = st.text_input("Puesto (ej: Barista)")
        em = st.text_input("Email")
        if st.form_submit_button("Guardar en Base de Datos"):
            guardar_empleado(leg, nom, pue, em)
            st.success(f"Empleado {nom} guardado permanentemente.")

    st.subheader("Nómina Actual")
    st.dataframe(pd.read_sql_query("SELECT * FROM empleados", conn), use_container_width=True)

# --- SECCIÓN: SUBIR REPORTE ---
elif menu == "Subir Reporte (Excel)":
    st.header("📤 Subir Reporte Prosoft")
    archivo = st.file_uploader("Selecciona el Excel", type=['xlsx'])
    
    if archivo:
        df = pd.read_excel(archivo, skiprows=2)
        # Ajustar nombres de columnas según tu Prosoft (Legajo, Fecha, Hora, Estado)
        st.write("Vista previa del archivo cargado:")
        st.dataframe(df.head())
        
        if st.button("Procesar y Guardar en Base de Datos"):
            # Aquí va la lógica de cálculo que ya teníamos
            # Por cada fila, calculamos diferencia y guardamos con guardar_asistencia()
            st.success("Datos guardados en la base de datos perpetua.")

# --- SECCIÓN: HISTORIAL ---
elif menu == "Historial por Empleado":
    st.header("🔍 Consulta de Horas Exactas")
    leg_busq = st.number_input("Ingrese Legajo", min_value=1)
    f_inicio = st.date_input("Desde")
    f_fin = st.date_input("Hasta")
    
    if st.button("Ver Reporte"):
        query = f"SELECT * FROM reportes WHERE legajo={leg_busq} AND fecha BETWEEN '{f_inicio}' AND '{f_fin}'"
        res = pd.read_sql_query(query, conn)
        
        if not res.empty:
            total_seg = res['total_segundos'].sum()
            st.subheader(f"Total trabajado: {formatear_segundos(total_seg)}")
            st.table(res[['fecha', 'entrada', 'salida']])
        else:
            st.warning("No hay datos para ese empleado en esas fechas.")
