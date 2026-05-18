import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
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
    /* Texto blanco para legibilidad en modo oscuro (Celular y PC) */
    .stMarkdown, p, h1, h2, h3, label {color: #ffffff !important;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# --- CONEXIÓN A BASE DE DATOS (NUBE) ---
if os.path.exists('/tmp'):
    db_path = '/tmp/cafe32_database.db'
else:
    db_path = 'cafe32_database.db'

conn = sqlite3.connect(db_path, check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS empleados (legajo INTEGER PRIMARY KEY, nombre TEXT, puesto TEXT, email TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS reportes (id INTEGER PRIMARY KEY AUTOINCREMENT, legajo INTEGER, fecha DATE, entrada TEXT, salida TEXT, total_segundos INTEGER)')
conn.commit()

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
    df_emp = pd.read_sql_query("SELECT * FROM empleados", conn)
    df_rep = pd.read_sql_query("SELECT legajo, fecha, entrada, salida FROM reportes", conn)
    
    # Dejamos solo la métrica de personal activo, quitando las horas globales sumadas
    st.metric("Personal Activo Registrado", len(df_emp))
    
    st.subheader("Últimos Fichajes Procesados")
    if not df_rep.empty:
        st.dataframe(df_rep.tail(15), use_container_width=True)
    else:
        st.info("Aún no hay marcas de asistencia guardadas. Sube un archivo en la pestaña de carga.")

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
                st.success(f"Empleado {n} guardado con éxito.")
    
    st.subheader("Nómina Actual")
    st.dataframe(pd.read_sql_query("SELECT * FROM empleados", conn), use_container_width=True)

elif menu == "📤 Cargar Reporte USB":
    st.header("Importar Datos de Reloj Fichador (.txt / .xlsx)")
    archivo = st.file_uploader("Sube el archivo aquí", type=['xlsx', 'txt'])
    
    if archivo:
        st.info("Archivo detectado. Listo para procesar.")
        if st.button("Procesar y Guardar Permanente"):
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
                                fecha_str = partes[indice_fecha].replace('/', '-')
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
                    registros_cargados = 0
                    
                    for (legajo, fecha), group in df.groupby(['Legajo', 'Fecha']):
                        c.execute("SELECT legajo FROM empleados WHERE legajo=?", (int(legajo),))
                        if c.fetchone():
                            horas_ordenadas = sorted(group['Hora'].tolist())
                            
                            entrada = horas_ordenadas[0]
                            salida = horas_ordenadas[-1]
                            
                            if entrada == salida:
                                continue 
                                
                            fmt = '%H:%M:%S'
                            t1 = datetime.strptime(entrada, fmt)
                            t2 = datetime.strptime(salida, fmt)
                            
                            segundos_trabajados = int((t2 - t1).total_seconds())
                            
                            c.execute("SELECT id FROM reportes WHERE legajo=? AND fecha=?", (int(legajo), str(fecha)))
                            existe = c.fetchone()
                            
                            if existe:
                                c.execute("""UPDATE reportes SET entrada=?, salida=?, total_segundos=? 
                                             WHERE legajo=? AND fecha=?""",
                                          (str(entrada), str(salida), segundos_trabajados, int(legajo), str(fecha)))
                            else:
                                c.execute("""INSERT INTO reportes (legajo, fecha, entrada, salida, total_segundos) 
                                             VALUES (?, ?, ?, ?, ?)""", 
                                          (int(legajo), str(fecha), str(entrada), str(salida), segundos_trabajados))
                            
                            registros_cargados += 1
                                
                    conn.commit()
                    if registros_cargados > 0:
                        st.success(f"¡Éxito! Se procesaron {registros_cargados} jornadas de trabajo correctamente.")
                    else:
                        st.warning("No se guardaron datos nuevos. Verifica que los legajos existan en la base de empleados.")
                else:
                    st.error("No se pudo extraer información válida del archivo.")
                    
            except Exception as e:
                st.error(f"Error general en el sistema: {e}")

elif menu == "🔍 Historial Detallado":
    st.header("Consulta de Tiempos Exactos")
    leg = st.number_input("Legajo del Empleado", min_value=1)
    f1 = st.date_input("Desde")
    f2 = st.date_input("Hasta")
    
    if st.button("Calcular Tiempo Exacto"):
        query = f"SELECT fecha, entrada, salida, total_segundos FROM reportes WHERE legajo={leg} AND fecha BETWEEN '{f1}' AND '{f2}'"
        res = pd.read_sql_query(query, conn)
        if not res.empty:
            segundos_totales = res['total_segundos'].sum()
            
            # Muestra el total por empleado en formato ultra exacto HH:MM:SS
            st.markdown(f"### Total Trabajado en el período: `{formatear_segundos(segundos_totales)}`")
            
            # Mostramos la tabla limpia para que el jefe vea las marcas diarias
            st.table(res[['fecha', 'entrada', 'salida']])
        else:
            st.warning("No hay registros de asistencias para este legajo en las fechas seleccionadas.")
