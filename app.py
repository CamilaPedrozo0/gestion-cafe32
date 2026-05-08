import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import calendar

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="GESTION DE HORAS CAFE32", layout="wide")

# Estilo CSS para el Calendario y Estética
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #4CAF50; color: white; }
    .card-manana { background-color: #2e7d32; color: white; padding: 5px; border-radius: 3px; margin-bottom: 2px; font-size: 12px; }
    .card-tarde { background-color: #ef6c00; color: white; padding: 5px; border-radius: 3px; margin-bottom: 2px; font-size: 12px; }
    .total-bold { font-size: 24px; font-weight: bold; color: #1e88e5; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
def get_connection():
    conn = sqlite3.connect('cafe32_database.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabla Empleados
    c.execute('''CREATE TABLE IF NOT EXISTS empleados 
                 (legajo INTEGER PRIMARY KEY, nombre TEXT, puesto TEXT, sector TEXT, telefono TEXT)''')
    # Tabla Registros (Fichadas)
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (legajo INTEGER, fecha TEXT, hora TEXT, tipo TEXT, UNIQUE(legajo, fecha, hora))''')
    conn.commit()

init_db()

# --- LÓGICA DE LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

def login():
    st.title("🔐 Inicio de Sesión - GESTIÓN CAFE32")
    user = st.text_input("Usuario")
    pw = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if user == "admin" and pw == "cafe32": # Cambia esto por tu clave
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

if not st.session_state.auth:
    login()
    st.stop()

# --- MENÚ LATERAL ---
st.sidebar.title("☕ GESTIÓN CAFE32")
opcion = st.sidebar.radio("Ir a:", ["Cargar Excel", "Empleados", "Reporte de Horas", "Calendario"])

# --- MODULO: CARGAR EXCEL ---
if opcion == "Cargar Excel":
    st.header("📥 Cargar Archivo Prosoft C109")
    file = st.file_uploader("Sube el Excel generado por la máquina", type=["xlsx"])
    
    if file:
        df = pd.read_excel(file, header=None)
        # Interpretamos columnas basado en la imagen: A:Legajo, B:Fecha, C:Hora, D:Tipo (Entrada/Salida)
        df = df[[0, 1, 2, 3]] 
        df.columns = ['legajo', 'fecha', 'hora', 'tipo']
        
        conn = get_connection()
        count = 0
        for _, row in df.iterrows():
            try:
                # Convertir fecha y hora a string limpio
                f = str(row['fecha']).split()[0]
                h = str(row['hora'])
                conn.execute("INSERT OR IGNORE INTO registros VALUES (?, ?, ?, ?)", 
                             (int(row['legajo']), f, h, row['tipo']))
                count += 1
            except:
                continue
        conn.commit()
        st.success(f"Se procesaron {count} registros. Se omitieron duplicados automáticamente.")

# --- MODULO: EMPLEADOS ---
elif opcion == "Empleados":
    st.header("👥 Gestión de Personal")
    
    with st.expander("➕ Crear/Modificar Empleado"):
        col1, col2 = st.columns(2)
        leg = col1.number_input("Legajo", step=1)
        nom = col2.text_input("Nombre y Apellido")
        pue = col1.text_input("Puesto")
        sec = col2.text_input("Sector")
        tel = col1.text_input("Teléfono")
        
        if st.button("Guardar en Sistema"):
            conn = get_connection()
            conn.execute("INSERT OR REPLACE INTO empleados VALUES (?,?,?,?,?)", (leg, nom, pue, sec, tel))
            conn.commit()
            st.success("Empleado guardado correctamente.")

    st.subheader("Base de Datos Actual")
    df_emp = pd.read_sql("SELECT * FROM empleados", get_connection())
    st.table(df_emp)

# --- MODULO: REPORTE DE HORAS ---
elif opcion == "Reporte de Horas":
    st.header("📊 Resumen de Horas")
    conn = get_connection()
    empleados = pd.read_sql("SELECT legajo, nombre FROM empleados", conn)
    
    if empleados.empty:
        st.warning("Primero carga empleados en el sistema.")
    else:
        sel_emp = st.selectbox("Seleccione Empleado", empleados['nombre'])
        legajo = empleados[empleados['nombre'] == sel_emp]['legajo'].values[0]
        
        col1, col2 = st.columns(2)
        f_inicio = col1.date_input("Fecha Inicio")
        f_fin = col2.date_input("Fecha Fin")
        
        if st.button("Calcular"):
            logs = pd.read_sql(f"""SELECT * FROM registros WHERE legajo={legajo} 
                               AND fecha BETWEEN '{f_inicio}' AND '{f_fin}' ORDER BY fecha, hora""", conn)
            
            total_segundos = 0
            # Agrupar por día
            for fecha, grupo in logs.groupby('fecha'):
                entrada = grupo[grupo['tipo'].str.contains('Entrada', case=False)]
                salida = grupo[grupo['tipo'].str.contains('Salida', case=False)]
                
                if not entrada.empty and not salida.empty:
                    h_ent = datetime.strptime(entrada.iloc[0]['hora'], '%H:%M:%S')
                    h_sal = datetime.strptime(salida.iloc[-1]['hora'], '%H:%M:%S')
                    dif = h_sal - h_ent
                    total_segundos += dif.total_seconds()
                    st.write(f"📅 {fecha}: {h_ent.strftime('%H:%M')} a {h_sal.strftime('%H:%M')} = **{dif}**")
            
            horas_totales = int(total_segundos // 3600)
            minutos_totales = int((total_segundos % 3600) // 60)
            st.markdown(f"<p class='total-bold'>TOTAL: {horas_totales}h {minutos_totales}min</p>", unsafe_allow_html=True)

# --- MODULO: CALENDARIO ---
elif opcion == "Calendario":
    st.header("🗓️ Calendario de Asistencia")
    hoy = datetime.now()
    mes_sel = st.selectbox("Mes", range(1, 13), index=hoy.month-1)
    
    cal = calendar.monthcalendar(hoy.year, mes_sel)
    conn = get_connection()
    
    # Dibujar Calendario
    cols = st.columns(7)
    dias = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    for i, d in enumerate(dias): cols[i].write(f"**{d}**")
    
    for semana in cal:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            if dia != 0:
                fecha_str = f"{hoy.year}-{mes_sel:02d}-{dia:02d}"
                cols[i].markdown(f"**{dia}**")
                
                # Buscar quienes trabajaron ese día
                query = f"""
                    SELECT e.nombre, r.hora 
                    FROM registros r 
                    JOIN empleados e ON r.legajo = e.legajo 
                    WHERE r.fecha = '{fecha_str}' AND r.tipo LIKE '%Entrada%'
                """
                fichadas = pd.read_sql(query, conn)
                
                for _, f in fichadas.iterrows():
                    h_fichada = datetime.strptime(f['hora'], '%H:%M:%S').time()
                    if h_fichada < datetime.strptime("11:00:00", "%H:%M:%S").time():
                        cols[i].markdown(f"<div class='card-manana'>{f['nombre']}</div>", unsafe_allow_html=True)
                    elif h_fichada > datetime.strptime("13:00:00", "%H:%M:%S").time():
                        cols[i].markdown(f"<div class='card-tarde'>{f['nombre']}</div>", unsafe_allow_html=True)