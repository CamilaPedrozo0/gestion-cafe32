import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import calendar

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="GESTION DE HORAS CAFE32", layout="wide")

# Estética Profesional (CSS)
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1a73e8; color: white; font-weight: bold; }
    .card-manana { background-color: #1b5e20; color: white; padding: 4px; border-radius: 4px; margin: 2px; font-size: 11px; text-align: center; }
    .card-tarde { background-color: #e65100; color: white; padding: 4px; border-radius: 4px; margin: 2px; font-size: 11px; text-align: center; }
    .total-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #1a73e8; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def get_db_connection():
    conn = sqlite3.connect('cafe32_v2.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Tabla Empleados (Con legajo como llave única)
    c.execute('''CREATE TABLE IF NOT EXISTS empleados 
                 (legajo INTEGER PRIMARY KEY, nombre TEXT, puesto TEXT, sector TEXT, telefono TEXT)''')
    # Tabla Registros (Evita duplicados por legajo, fecha y hora exacta)
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (legajo INTEGER, fecha TEXT, hora TEXT, tipo TEXT, UNIQUE(legajo, fecha, hora))''')
    conn.commit()

init_db()

# --- 3. SISTEMA DE LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Acceso GESTIÓN CAFE32")
    user = st.text_input("Usuario Admin")
    pw = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if user == "admin" and pw == "cafe32":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Error: Usuario o clave incorrectos")
    st.stop()

# --- 4. MENÚ LATERAL ---
st.sidebar.title("☕ CAFE32")
opcion = st.sidebar.radio("MENÚ", ["📥 Cargar Datos", "👥 Empleados", "📊 Reporte de Horas", "🗓️ Calendario"])
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.auth = False
    st.rerun()

# --- 5. LÓGICA: CARGAR DATOS (SOPORTE PARA TXT DE PROSOFT) ---
if opcion == "📥 Cargar Datos":
    st.header("Cargar Fichadas (Resumen Prosoft TXT)")
    st.info("Subí el archivo TXT tal cual sale de la máquina. El sistema asignará Entrada/Salida automáticamente.")
    
    file = st.file_uploader("Arrastrá tu archivo TXT o Excel aquí", type=["xlsx", "txt"])
    
    if file:
        try:
            if file.name.endswith('.xlsx'):
                # Lógica para Excel (Hoja1)
                df = pd.read_excel(file)
                # ... (mantener lógica de excel si la usas)
            else:
                # 1. Leemos el TXT usando espacios como separador (\s+)
                # Saltamos la primera línea (UDISKLOG...)
                df_raw = pd.read_csv(file, sep='\s+', skiprows=1, header=None, engine='python')
                
                # De acuerdo a tu imagen, las columnas son:
                # Col 2 (EnNo) -> Legajo
                # Col 6 (Date) -> Fecha
                # Col 7 (Time) -> Hora
                df = df_raw[[2, 6, 7]].copy()
                df.columns = ['legajo', 'fecha', 'hora']
                
                # Limpieza de datos
                df['legajo'] = df['legajo'].astype(str).str.lstrip('0') # Quitamos ceros a la izquierda
                df['fecha'] = df['fecha'].str.replace('/', '-') # Normalizamos formato fecha
                
            # --- LÓGICA INTELIGENTE DE ENTRADA/SALIDA ---
            # Ordenamos por legajo, día y hora para que no haya errores
            df = df.sort_values(by=['legajo', 'fecha', 'hora'])
            
            # Contamos las veces que aparece el empleado en el mismo día
            # El registro 0 será Entrada, el 1 será Salida, el 2 Entrada, etc.
            df['n_fichada'] = df.groupby(['legajo', 'fecha']).cumcount()
            df['tipo'] = df['n_fichada'].apply(lambda x: 'Entrada' if x % 2 == 0 else 'Salida')
            
            # Guardado en Base de Datos
            conn = get_db_connection()
            count = 0
            for _, row in df.iterrows():
                try:
                    l, f, h, t = str(row['legajo']), str(row['fecha']), str(row['hora']), row['tipo']
                    # INSERT OR IGNORE evita duplicados si subís el mismo archivo dos veces
                    conn.execute("INSERT OR IGNORE INTO registros VALUES (?, ?, ?, ?)", (l, f, h, t))
                    count += 1
                except: continue
            
            conn.commit()
            st.success(f"✅ ¡Procesado con éxito! Se cargaron {count} registros correctamente.")
            
        except Exception as e:
            st.error(f"Error al leer el formato del TXT: {e}")
            st.warning("Verificá que el archivo TXT tenga las columnas: No, Mchn, EnNo, Name, Mode, IOMd, DateTime.")
# --- 6. LÓGICA: EMPLEADOS ---
elif opcion == "👥 Empleados":
    st.header("Gestión de Personal")
    
    with st.expander("➕ Alta/Modificación de Empleado"):
        c1, c2 = st.columns(2)
        leg = c1.number_input("Número de Legajo", step=1, value=1)
        nom = c2.text_input("Nombre Completo")
        pue = c1.text_input("Puesto / Cargo")
        sec = c2.text_input("Sector")
        tel = st.text_input("Teléfono de contacto")
        
        if st.button("Guardar Empleado"):
            conn = get_db_connection()
            conn.execute("INSERT OR REPLACE INTO empleados VALUES (?,?,?,?,?)", (leg, nom, pue, sec, tel))
            conn.commit()
            st.success(f"Empleado {nom} guardado.")

    st.subheader("Base de Datos")
    df_emp = pd.read_sql("SELECT * FROM empleados", get_db_connection())
    st.dataframe(df_emp, use_container_width=True)

# --- 7. LÓGICA: REPORTE DE HORAS ---
elif opcion == "📊 Reporte de Horas":
    st.header("Reporte Individual de Horas")
    conn = get_db_connection()
    emp_df = pd.read_sql("SELECT legajo, nombre FROM empleados", conn)
    
    if emp_df.empty:
        st.warning("No hay empleados cargados.")
    else:
        sel_nom = st.selectbox("Seleccionar Empleado", emp_df['nombre'])
        legajo = emp_df[emp_df['nombre'] == sel_nom]['legajo'].values[0]
        
        col_f1, col_f2 = st.columns(2)
        desde = col_f1.date_input("Desde", datetime.now() - timedelta(days=7))
        hasta = col_f2.date_input("Hasta", datetime.now())
        
        if st.button("Generar Reporte"):
            query = f"SELECT * FROM registros WHERE legajo={legajo} AND fecha BETWEEN '{desde}' AND '{hasta}' ORDER BY fecha, hora"
            logs = pd.read_sql(query, conn)
            
            total_sec = 0
            st.write(f"### Detalle para {sel_nom}:")
            
            for f, grupo in logs.groupby('fecha'):
                # Buscamos la primera entrada y la última salida del día
                entradas = grupo[grupo['tipo'].str.contains('Entrada', case=False, na=False)]
                salidas = grupo[grupo['tipo'].str.contains('Salida', case=False, na=False)]
                
                if not entradas.empty and not salidas.empty:
                    e_t = datetime.strptime(entradas.iloc[0]['hora'], '%H:%M:%S')
                    s_t = datetime.strptime(salidas.iloc[-1]['hora'], '%H:%M:%S')
                    diff = s_t - e_t
                    total_sec += diff.total_seconds()
                    st.write(f"📅 {f}: **{e_t.strftime('%H:%M')}** a **{s_t.strftime('%H:%M')}** ➔ {diff}")
            
            h = int(total_sec // 3600)
            m = int((total_sec % 3600) // 60)
            st.markdown(f"<div class='total-box'><h3>Total Acumulado: <b>{h}h {m}min</b></h3></div>", unsafe_allow_html=True)

# --- 8. LÓGICA: CALENDARIO ---
elif opcion == "🗓️ Calendario":
    st.header("Calendario Visual de Asistencia")
    st.write("🟢 Antes de 11:00 AM | 🟠 Después de 1:00 PM")
    
    hoy = datetime.now()
    cal = calendar.monthcalendar(hoy.year, hoy.month)
    
    conn = get_db_connection()
    
    # Dibujar encabezados de días
    cols = st.columns(7)
    for i, d in enumerate(["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]):
        cols[i].write(f"**{d}**")
    
    for semana in cal:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            if dia != 0:
                fecha_str = f"{hoy.year}-{hoy.month:02d}-{dia:02d}"
                cols[i].write(f"**{dia}**")
                
                # Buscar fichadas de entrada para este día
                query = f"""SELECT e.nombre, r.hora FROM registros r 
                            JOIN empleados e ON r.legajo = e.legajo 
                            WHERE r.fecha = '{fecha_str}' AND r.tipo LIKE '%Entrada%' """
                res = pd.read_sql(query, conn)
                
                for _, r in res.iterrows():
                    h_f = datetime.strptime(r['hora'], '%H:%M:%S').time()
                    if h_f < datetime.strptime("11:00:00", "%H:%M:%S").time():
                        cols[i].markdown(f"<div class='card-manana'>{r['nombre']}</div>", unsafe_allow_html=True)
                    elif h_f > datetime.strptime("13:00:00", "%H:%M:%S").time():
                        cols[i].markdown(f"<div class='card-tarde'>{r['nombre']}</div>", unsafe_allow_html=True)
