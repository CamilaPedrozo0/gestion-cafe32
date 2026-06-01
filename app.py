import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import io
import re

# --- CONFIGURACIÓN E INTERFAZ PROFESIONAL ---
st.set_page_config(page_title="Gestión Café 32", page_icon="☕", layout="wide")

# Estilos 100% controlados: Fondo oscuro profundo, textos claros y botones visibles
theme_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fondo de toda la pantalla (Modo Oscuro Real) */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0d1117 !important;
    }
    
    /* Forzar que todos los textos principales sean blancos */
    h1, h2, h3, h4, p, label, span, .stMetric * {
        color: #ffffff !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Contenedores de información (Tarjetas) */
    div[data-testid="stMetricValue"] {
        color: #ffeb3b !important; /* Resaltar números clave en amarillo */
    }
    
    /* Estilo para los botones en pantalla */
    .stButton>button {
        color: #ffffff !important;
        background-color: #238636 !important; /* Verde éxito profesional */
        border: none !important;
        padding: 0.5rem 1.5rem !important;
        border-radius: 6px !important;
        font-weight: bold !important;
    }
    .stButton>button:hover {
        background-color: #2ea043 !important;
    }
    </style>
"""
st.markdown(theme_style, unsafe_allow_html=True)

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
    date(2026, 6, 20): "Paso a la Inmortalidad del Gral. Manuel Belgrano",
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

# --- MENÚ DE NAVEGACIÓN SUPERIOR (FIJO Y VISIBLE) ---
st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>☕ GESTIÓN CAFÉ 32</h1>", unsafe_allow_html=True)
menu = st.selectbox(
    "Seleccioná la sección a la que querés ir:",
    ["📊 Resumen General", "📅 Calendario de Turnos", "👤 Base de Empleados", "📤 Cargar Reporte USB", "🔍 Historial Detallado"]
)
st.markdown("---")

# --- LÓGICA DE LAS SECCIONES ---

if menu == "📊 Resumen General":
    st.header("Resumen del Sistema")
    df_emp = cargar_empleados()
    df_rep = cargar_reportes()
    
    st.metric("Personal Activo Registrado", len(df_emp))
    st.subheader("Últimos Fichajes Guardados en Google Sheets")
    if not df_rep.empty:
        try:
            vista_rep = df_rep.tail(15)[['legajo', 'fecha', 'entrada', 'salida']].copy()
            vista_rep.columns = ['Legajo', 'Fecha', 'Hora Entrada', 'Hora Salida']
            st.dataframe(vista_rep, use_container_width=True, hide_index=True)
        except:
            st.info("Estructura correcta detectada. Esperando datos en la pestaña 'reportes'.")
    else:
        st.info("Aún no hay marcas de asistencia guardadas en tu pestaña 'reportes'.")

elif menu == "📅 Calendario de Turnos":
    st.header("Planificación y Control de Turnos Diarios")
    df_emp = cargar_empleados()
    df_rep = cargar_reportes()
    
    if not df_rep.empty and not df_emp.empty:
        fecha_cal = st.date_input("Selecciona una fecha para ver los turnos:", value=date.today())
        
        nombre_feriado = es_feriado(fecha_cal)
        if nombre_feriado:
            st.markdown(f"<div style='background-color: #1e3a8a; padding: 15px; border-radius: 5px; margin-bottom: 15px;'><h4 style='margin:0;'>🔵 ¡DÍA FERIADO NACIONAL!: {nombre_feriado}</h4></div>", unsafe_allow_html=True)
        
        df_rep['fecha_dt'] = pd.to_datetime(df_rep['fecha']).dt.date
        fichajes_dia = df_rep[df_rep['fecha_dt'] == fecha_cal]
        df_merge = pd.merge(fichajes_dia, df_emp, on='legajo', how='
