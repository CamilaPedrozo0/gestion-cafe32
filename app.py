import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import io
import re

# --- CONFIGURACIÓN E INTERFAZ INALTERABLE ---
st.set_page_config(page_title="Gestión Café 32", page_icon="☕", layout="wide")

# Forzamos contraste alto permanente para modo oscuro y modo claro
st.markdown("""
    <style>
    /* Forzar que no se oculte nada del sistema operativo o navegador */
    .stApp { background-color: #0d1117 !important; }
    h1, h2, h3, h4, p, label, span, .stMetric * { color: #ffffff !important; }
    div[data-testid="stMetricValue"] { color: #ffeb3b !important; }
    .stButton>button {
        color: #ffffff !important;
        background-color: #238636 !important;
        border: none !important;
        padding: 0.6rem 2rem !important;
        border-radius: 6px !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
# REEMPLAZA ESTO CON EL ID LARGO DE TU HOJA:
ID_DE_TU_HOJA = "TU_ID_AQUÍ" 

URL_EMPLEADOS = f"https://docs.google.com/spreadsheets/d/{ID_DE_TU_HOJA}/gviz/tq?tqx=out:csv&sheet=empleados"
URL_REPORTES = f"https://docs.google.com/spreadsheets/d/{ID_DE_TU_HOJA}/gviz/tq?tqx=out:csv&sheet=reportes"

# --- BASE DE FERIADOS NACIONALES ARGENTINA (2026) ---
FERIADOS_2026 = {
    date(2026, 1, 1): "Año Nuevo", date(2026, 2, 16): "Carnaval", date(2026, 2, 17): "Carnaval",
    date(2026, 3, 24): "Día de la Memoria", date(2026, 4, 2): "Día de Malvinas", date(2026, 4, 3): "Viernes Santo",
    date(2026, 5, 1): "Día del Trabajador", date(2026, 5, 25): "Revolución de Mayo",
    date(2026, 6, 20): "Paso a la Inmortalidad del Gral. Manuel Belgrano",
    date(2026, 7, 9): "Día de la Independencia", date(2026, 8, 17): "Gral. San Martín",
    date(2026, 10, 12): "Diversidad Cultural", date(2026, 11, 20): "Soberanía Nacional",
    date(2026, 12, 8): "Inmaculada Concepción", date(2026, 12, 25): "Navidad"
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
        return partes[0] * 3600 + partes[1] * 60 + partes[2] if len(partes) == 3 else 0
    except:
        return 0

# --- PANTALLA DE ACCESO ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>☕ CONTROL ASISTENCIA - CAFÉ 32</h2>", unsafe_allow_html=True)
        user = st.text_input("Usuario Administrador:")
        pw = st.text_input("Contraseña:", type="password")
        if st.button("Iniciar Sesión"):
            if user == "admin" and pw == "cafe32":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    st.stop()

# --- MENÚ DE NAVEGACIÓN PRINCIPAL (SIEMPRE VISIBLE ARRIBA) ---
st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>☕ SISTEMA GESTIÓN CAFÉ 32</h1>", unsafe_allow_html=True)

# Un selector grande, claro y centrado en la pantalla para cambiar de sección
menu = st.selectbox(
    " SELECCIONÁ LA SECCIÓN A LA QUE QUERÉS IR:",
    ["📊 Resumen General", "📅 Calendario de Turnos", "👤 Base de Empleados", "📤 Cargar Reporte USB", "🔍 Historial Detallado"],
    index=0
)
st.markdown("<hr style='border-color: #30363d;'>", unsafe_allow_html=True)

# --- LÓGICA DE TRABAJO DE LAS SECCIONES ---

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
            st.info("Esperando que agregues datos válidos en la pestaña 'reportes' de tu Sheets.")
    else:
        st.info("Aún no hay marcas de asistencia guardadas en la nube.")

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
        df_merge = pd.merge(fichajes_dia, df_emp, on='legajo', how='left')
        
        col_m, col_t = st.columns(2)
        with col_m:
            st.markdown("### 🌅 Turno Mañana (7am a 11am)")
            manana_data = [{"Empleado": f["nombre"] if pd.notna(f["nombre"]) else f"Legajo {f['legajo']}", "Entrada": f['entrada'], "Salida": f['salida']} for _, f in df_merge.iterrows() if determinar_turno(f['entrada']) == "Mañana"]
            if manana_data: st.dataframe(pd.DataFrame(manana_data), use_container_width=True, hide_index=True)
            else: st.caption("No hay marcas registradas en la mañana.")
                
        with col_t:
            st.markdown("### 🌇 Turno Tarde (Después de las 11am)")
            tarde_data = [{"Empleado": f["nombre"] if pd.notna(f["nombre"]) else f"Legajo {f['legajo']}", "Entrada": f['entrada'], "Salida": f['salida']} for _, f in df_merge.iterrows() if determinar_turno(f['entrada']) == "Tarde"]
            if tarde_data: st.dataframe(pd.DataFrame(tarde_data), use_container_width=True, hide_index=True)
            else: st.caption("No hay marcas registradas en la tarde.")
    else:
        st.warning("Se necesitan cargar datos válidos en las pestañas 'empleados' y 'reportes' de tu Google Sheets.")

elif menu == "👤 Base de Empleados":
    st.header("Gestión de Personal")
    df_emp = cargar_empleados()
    st.markdown(f"[➡️ Hacer clic acá para abrir tu Google Sheets directamente](https://docs.google.com/spreadsheets/d/{ID_DE_TU_HOJA})")
    
    st.subheader("Nómina de Empleados Vinculada")
    if not df_emp.empty:
        st.dataframe(df_emp, use_container_width=True, hide_index=True)
    else:
        st.warning("No se encontraron empleados. Asegúrate de tener datos en la pestaña 'empleados' de tu Sheets.")

elif menu == "📤 Cargar Reporte USB":
    st.header("Importar Datos de Reloj Fichador (.txt)")
    archivo = st.file_uploader("Arrastrá o selecciona tu archivo horarios.txt acá", type=['txt'])
    
    if archivo:
        st.info("Archivo cargado con éxito.")
        if st.button("Procesar Horarios Ahora"):
            try:
                contenido = archivo.getvalue().decode("utf-8")
                df_procesado = []
                
                # ESCÁNER LÍNEA POR LÍNEA: Ignora encabezados rotos y textos extraños automáticamente
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
                if not df.empty:
                    jornadas = []
                    for (legajo, fecha), group in df.groupby(['Legajo', 'Fecha']):
                        horas = sorted(group['Hora'].tolist())
                        entrada, salida = horas[0], horas[-1]
                        if entrada == salida: continue
                        
                        t1 = datetime.strptime(entrada, '%H:%M:%S')
                        t2 = datetime.strptime(salida, '%H:%M:%S')
                        segundos = int((t2 - t1).total_seconds())
                        
                        try:
                            p = list(map(int, fecha.split('-')))
                            if p[0] < 100: p[0] += 2000
                            f_obj = date(p[0], p[1], p[2])
                            n_f = es_feriado(f_obj)
                        except: n_f = None
                        
                        jornadas.append({
                            'id': '', 'legajo': legajo, 'fecha': fecha,
                            'entrada': entrada, 'salida': salida,
                            'tiempo_trabajado': formatear_segundos(segundos),
                            'tipo_dia': f"Feriado: {n_f}" if n_f else "Normal"
                        })
                    
                    st.success("¡Archivo interpretado correctamente sin errores!")
                    df_res = pd.DataFrame(jornadas)
                    st.dataframe(df_res, use_container_width=True, hide_index=True)
                    st.caption("💡 Seleccioná estas filas, copialas y pegalas en tu pestaña 'reportes' de Google Sheets.")
                else:
                    st.error("No se encontraron registros de marcas legibles en este archivo de texto.")
            except Exception as e:
                st.error(f"Error al procesar: {e}")

elif menu == "🔍 Historial Detallado":
    st.header("Consulta de Horas Acumuladas")
    leg = st.number_input("Ingresá el Legajo del Empleado:", min_value=1, step=1)
    f1 = st.date_input("Desde:")
    f2 = st.date_input("Hasta:")
    
    if st.button("Calcular Total de Horas"):
        df_rep = cargar_reportes()
        if not df_rep.empty:
            df_rep['legajo'] = df_rep['legajo'].astype(int)
            df_rep['fecha'] = pd.to_datetime(df_rep['fecha']).dt.date
            res = df_rep[(df_rep['legajo'] == leg) & (df_rep['fecha'] >= f1) & (df_rep['fecha'] <= f2)]
            
            if not res.empty:
                tot, fer = 0, 0
                for _, fila in res.iterrows():
                    t = fila['tiempo_trabajado']
                    seg = convertir_a_segundos(t) if ':' in str(t) else (int(t) if pd.notna(t) else 0)
                    tot += seg
                    if 'tipo_dia' in res.columns and "Feriado" in str(fila['tipo_dia']):
                        fer += seg
                
                st.markdown(f"### ⏱️ Horas totales cumplidas: `{formatear_segundos(tot)}`")
                if fer > 0:
                    st.markdown(f"### 🔵 Horas trabajadas en Feriados (Doble): `{formatear_segundos(fer)}`")
                st.dataframe(res[['fecha', 'entrada', 'salida', 'tiempo_trabajado']], use_container_width=True, hide_index=True)
            else:
                st.warning("No hay registros cargados para este legajo en las fechas seleccionadas.")
        else:
            st.warning("La planilla de reportes en Google Sheets está vacía.")
