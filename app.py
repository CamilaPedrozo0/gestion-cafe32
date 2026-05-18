import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
import io

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
                
                # MODO EXCEL (Como venía antes)
                if nombre_archivo.endswith('.xlsx'):
                    df = pd.read_excel(archivo, header=None, skiprows=2, usecols='A:E')
                    df.columns = ['Legajo', 'Fecha', 'Hora', 'Estado', 'Nombre']
                    # Convertir legajo a entero por seguridad
                    df['Legajo'] = df['Legajo'].astype(int)
                
                # MODO TXT NUEVO (Calibrado para el formato Prosoft crudo)
                elif nombre_archivo.endswith('.txt'):
                    contenido = archivo.getvalue().decode("utf-8")
                    # Separado por tabulaciones (\t)
                    raw_df = pd.read_csv(io.StringIO(contenido), header=None, sep='\t', engine='python')
                    
                    # Estructuramos las columnas según tus datos reales
                    df_procesado = []
                    for idx, row in raw_df.iterrows():
                        try:
                            legajo_int = int(row[2]) # Columna 000000001
                            fecha_hora_str = str(row[6]).strip() # Columna 2026/05/01  16:35:02
                            
                            # Separamos la fecha de la hora
                            dt_obj = datetime.strptime(fecha_hora_str, '%Y/%M/%d %H:%M:%S')
                            fecha_limpia = dt_obj.strftime('%Y-%m-%d')
                            hora_limpia = dt_obj.strftime('%H:%M:%S')
                            
                            df_procesado.append({
                                'Legajo': legajo_int,
                                'Fecha': fecha_limpia,
                                'Hora': hora_limpia
                            })
                        except:
                            continue # Si una línea está en blanco o rota, la salta sin romper la app
                    
                    df = pd.DataFrame(df_procesado)

                if df is not None and not df.empty:
                    registros_cargados = 0
                    
                    # Agrupamos por empleado y fecha para buscar entradas y salidas automáticas
                    for (legajo, fecha), group in df.groupby(['Legajo', 'Fecha']):
                        c.execute("SELECT legajo FROM empleados WHERE legajo=?", (int(legajo),))
                        if c.fetchone():
                            # Ordenamos las marcas de tiempo de ese día
                            horas_ordenadas = sorted(group['Hora'].tolist())
                            
                            entrada = horas_ordenadas[0] # La primera del día
                            salida = horas_ordenadas[-1] # La última del día
                            
                            # Si solo fichó una vez en todo el día, no podemos calcular diferencia
                            if entrada == salida:
                                continue 
                                
                            fmt = '%H:%M:%S'
                            t1 = datetime.strptime(entrada, fmt)
                            t2 = datetime.strptime(salida, fmt)
                            
                            segundos_trabajados = int((t2 - t1).total_seconds())
                            
                            # Evitar duplicar la misma jornada si vuelven a subir el mismo archivo
                            c.execute("SELECT id FROM reportes WHERE legajo=? AND fecha=?", (int(legajo), str(fecha)))
                            if not c.fetchone():
                                c.execute("""INSERT INTO reportes (legajo, fecha, entrada, salida, total_segundos) 
                                             VALUES (?, ?, ?, ?, ?)""", 
                                          (int(legajo), str(fecha), str(entrada), str(salida), segundos_trabajados))
                                registros_cargados += 1
                                
                    conn.commit()
                    if registros_cargados > 0:
                        st.success(f"¡Éxito! Se procesaron {registros_cargados} jornadas de trabajo correctamente.")
                    else:
                        st.warning("No se detectaron jornadas nuevas o los empleados no están registrados en la pestaña '👤 Base de Empleados'.")
                else:
                    st.error("No se pudieron extraer datos válidos del archivo.")
                    
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")

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
            st.warning("No hay registros para este legajo.")
