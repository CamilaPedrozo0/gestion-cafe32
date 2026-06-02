import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import re

# --- CONFIGURACIÓN DE LA APP (TEMA OSCURO / LIMPIO) ---
st.set_page_config(page_title="Gestión Horas Café 32", page_icon="☕", layout="wide")

# --- LIMPIEZA VISUAL DE INTERFAZ (CSS MINIMALISTA) ---
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        h1 { color: #F39C12; font-weight: 700; }
        h2 { color: #E67E22; font-weight: 600; }
        .stMetric { background-color: #1E272C; padding: 15px; border-radius: 10px; border: 1px solid #34495E; }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE BASE DE DATOS EN LA BARRA LATERAL ---
st.sidebar.markdown("### ⚙️ Conexión segura")

id_defecto = "1veKrncoLJmYwXXrNeODVembeiXT9oL9nm9le-r1ZpRg"
url_ingresada = st.sidebar.text_input("Enlace de tu Google Sheets:", value=id_defecto, help="Podés pegar el link completo o solo el ID.")

def extraer_id_sheets(texto):
    if "docs.google.com/spreadsheets" in texto:
        match = re.search(r'/d/([^/]+)', texto)
        if match: return match.group(1)
    return texto.strip()

id_sheets = extraer_id_sheets(url_ingresada)

URL_EMPLEADOS = f"https://docs.google.com/spreadsheets/d/{id_sheets}/gviz/tq?tqx=out:csv&sheet=empleados"
URL_REPORTES = f"https://docs.google.com/spreadsheets/d/{id_sheets}/gviz/tq?tqx=out:csv&sheet=reportes"

# --- CALENDARIO DE FERIADOS ARGENTINA (2026) ---
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
    if not id_sheets: return pd.DataFrame(columns=['legajo', 'nombre', 'puesto', 'email'])
    try:
        df = pd.read_csv(URL_EMPLEADOS)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except: return pd.DataFrame(columns=['legajo', 'nombre', 'puesto', 'email'])

def cargar_reportes():
    if not id_sheets: return pd.DataFrame(columns=['id', 'legajo', 'fecha', 'entrada', 'salida', 'tiempo_trabajado', 'tipo_dia'])
    try:
        df = pd.read_csv(URL_REPORTES)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except: return pd.DataFrame(columns=['id', 'legajo', 'fecha', 'entrada', 'salida', 'tiempo_trabajado', 'tipo_dia'])

def formatear_segundos(segundos):
    hrs = int(segundos // 3600)
    mins = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    return f"{hrs:02d}:{mins:02d}:{segs:02d}"

def convertir_a_segundos(tiempo_str):
    try:
        partes = list(map(int, str(tiempo_str).split(':')))
        return partes[0] * 3600 + partes[1] * 60 + partes[2] if len(partes) == 3 else 0
    except: return 0

# --- MENÚ LATERAL ESTILIZADO ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 MENÚ PRINCIPAL")
menu = st.sidebar.radio(
    "Navegación:",
    ["📊 Resumen Dashboard", "📅 Control de Turnos", "👤 Nómina de Empleados", "📤 Procesar Disco USB", "🔍 Auditoría de Horas"],
    label_visibility="collapsed"
)

# --- ENCABEZADO PRINCIPAL LIMPIO ---
st.title("☕ Gestión Horas Café 32")
if id_sheets:
    st.sidebar.success("● Base Conectada Activa")
else:
    st.sidebar.error("○ Sin conexión a Google Sheets")

# --- DESARROLLO DE SECCIONES ---

if menu == "📊 Resumen Dashboard":
    st.subheader("Estado General del Negocio")
    df_emp = cargar_empleados()
    df_rep = cargar_reportes()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Personal en Plantilla", value=len(df_emp))
    with col2:
        st.metric(label="Fichajes Almacenados", value=len(df_rep))
        
    st.markdown("### 🗓️ Últimos movimientos registrados")
    if not df_rep.empty:
        st.dataframe(df_rep.tail(12), use_container_width=True, hide_index=True)
    else:
        st.info("Aún no registraste marcas en tu planilla. Importá tu primer archivo USB para empezar.")

elif menu == "📅 Control de Turnos":
    st.subheader("📅 Planificación Diario y Feriados")
    df_emp = cargar_empleados()
    df_rep = cargar_reportes()
    
    col_f, col_b = st.columns([1, 2])
    with col_f:
        fecha_cal = st.date_input("Día a auditar:", value=date.today())
    
    nombre_feriado = es_feriado(fecha_cal)
    if nombre_feriado:
        st.warning(f"🎉 Día Feriado Detectado: {nombre_feriado}")
        
    if not df_rep.empty:
        try:
            df_rep['fecha_clean'] = df_rep['fecha'].astype(str).str.replace('/', '-')
            f_str1 = fecha_cal.strftime('%d-%m-%Y')
            f_str2 = fecha_cal.strftime('%Y-%m-%d')
            
            fichajes_dia = df_rep[(df_rep['fecha_clean'] == f_str1) | (df_rep['fecha_clean'] == f_str2)]
            
            if not fichajes_dia.empty:
                if not df_emp.empty:
                    df_emp['legajo'] = df_emp['legajo'].astype(int)
                    fichajes_dia['legajo'] = fichajes_dia['legajo'].astype(int)
                    df_merge = pd.merge(fichajes_dia, df_emp, on='legajo', how='left')
                else:
                    df_merge = fichajes_dia.copy()
                    df_merge['nombre'] = "No asociado"
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### 🌅 Turno Mañana")
                    m_data = df_merge[df_merge['entrada'].apply(determinar_turno) == "Mañana"]
                    if not m_data.empty:
                        st.dataframe(m_data[['legajo', 'nombre', 'entrada', 'salida', 'tiempo_trabajado']], use_container_width=True, hide_index=True)
                    else:
                        st.caption("Sin actividad por la mañana.")
                with c2:
                    st.markdown("#### 🌇 Turno Tarde")
                    t_data = df_merge[df_merge['entrada'].apply(determinar_turno) == "Tarde"]
                    if not t_data.empty:
                        st.dataframe(t_data[['legajo', 'nombre', 'entrada', 'salida', 'tiempo_trabajado']], use_container_width=True, hide_index=True)
                    else:
                        st.caption("Sin actividad por la tarde.")
            else:
                st.info("No hay marcas de asistencia en la base de datos para este día.")
        except Exception as e:
            st.error(f"Inconveniente en procesamiento: {e}")
    else:
        st.error("La base de datos está vacía.")

elif menu == "👤 Nómina de Empleados":
    st.subheader("👤 Personal de Café 32")
    df_emp = cargar_empleados()
    
    if id_sheets:
        st.link_button("📂 Modificar/Agregar en Google Sheets", f"https://docs.google.com/spreadsheets/d/{id_sheets}")
        
    st.markdown("#### Datos Sincronizados de la pestaña 'empleados':")
    if not df_emp.empty:
        st.dataframe(df_emp, use_container_width=True, hide_index=True)
    else:
        st.info("No se registran datos. Completá la pestaña 'empleados' de tu documento.")

elif menu == "📤 Procesar Disco USB":
    st.subheader("📤 Conversor de Archivo Fichador Prosoft")
    st.markdown("Subí el `.txt` extraído de la memoria del reloj. El sistema calculará horas netas y feriados al instante.")
    
    archivo = st.file_uploader("Arrastrá el archivo aquí:", type=['txt'], label_visibility="collapsed")
    
    if archivo:
        try:
            contenido = archivo.getvalue().decode("utf-8")
            df_procesado = []
            
            for linea in contenido.splitlines():
                linea = linea.strip()
                if not linea: continue
                
                # REPARACIÓN AQUÍ: Se eliminó el guion doble problemático
                match_fecha = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', linea)
                match_hora = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', linea)
                
                if match_fecha and match_hora:
                    fecha_str = match_fecha.group(0).replace('/', '-')
                    hora_str = match_hora.group(0)
                    partes_antes = linea.split(match_fecha.group(0))[0].strip()
                    numeros = re.findall(r'\b\d+\b', partes_antes)
                    
                    if numeros:
                        df_procesado.append({'legajo': int(numeros[0]), 'fecha': fecha_str, 'hora': hora_str})
            
            df_raw = pd.DataFrame(df_procesado)
            
            if not df_raw.empty:
                jornadas = []
                for (legajo, fecha), group in df_raw.groupby(['legajo', 'fecha']):
                    horas = sorted(group['hora'].tolist())
                    entrada, salida = horas[0], horas[-1]
                    if entrada == salida: continue
                    
                    t1 = datetime.strptime(entrada, '%H:%M:%S')
                    t2 = datetime.strptime(salida, '%H:%M:%S')
                    segundos = int((t2 - t1).total_seconds())
                    
                    try:
                        p = list(map(int, fecha.split('-')))
                        f_obj = date(p[2], p[1], p[0]) if p[0] < 1000 else date(p[0], p[1], p[2])
                        nom_f = es_feriado(f_obj)
                    except: nom_f = None
                        
                    jornadas.append({
                        'id': '', 'legajo': int(legajo), 'fecha': fecha,
                        'entrada': entrada, 'salida': salida,
                        'tiempo_trabajado': formatear_segundos(segundos),
                        'tipo_dia': f"Feriado: {nom_f}" if nom_f else "Normal"
                    })
                
                st.success("🎉 ¡Procesamiento Exitoso!")
                df_res = pd.DataFrame(jornadas)[['id', 'legajo', 'fecha', 'entrada', 'salida', 'tiempo_trabajado', 'tipo_dia']]
                st.dataframe(df_res, use_container_width=True, hide_index=True)
                
                with st.container(border=True):
                    st.markdown("#### 📥 ¿Cómo pasar esto a la Base de Datos?")
                    st.caption("1. Seleccioná y copiá la tabla de arriba (Ctrl + C).")
                    st.caption("2. Abrí tu base de datos presionando el botón de abajo.")
                    st.caption("3. Parate al final de la pestaña **'reportes'** y pegá los datos (Ctrl + V).")
                    if id_sheets:
                        st.link_button("🚀 Abrir Base de Datos 'gestion horas cafe32'", f"https://docs.google.com/spreadsheets/d/{id_sheets}")
            else:
                st.error("No se encontraron marcas válidas en el archivo .txt.")
        except Exception as e:
            st.error(f"Error al interpretar archivo: {e}")

elif menu == "🔍 Auditoría de Horas":
    st.subheader("🔍 Filtro de Horas Acumuladas")
    df_rep = cargar_reportes()
    
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1: leg_busqueda = st.number_input("Número de Legajo:", min_value=1, step=1)
        with c2: f_desde = st.date_input("Desde:", value=date.today() - timedelta(days=30))
        with c3: f_hasta = st.date_input("Hasta:", value=date.today())
        
        ejecutar = st.button("📊 Calcular Liquidación")
        
    if ejecutar:
        if not df_rep.empty:
            try:
                df_rep['legajo'] = df_rep['legajo'].astype(int)
                df_rep['fecha_clean'] = df_rep['fecha'].astype(str).str.replace('/', '-')
                
                def parse_fecha(x):
                    for fmt in ('%d-%m-%Y', '%Y-%m-%d'):
                        try: return datetime.strptime(x, fmt).date()
                        except: pass
                    return None
                
                df_rep['fecha_obj'] = df_rep['fecha_clean'].apply(parse_fecha)
                res = df_rep[(df_rep['legajo'] == leg_busqueda) & (df_rep['fecha_obj'] >= f_desde) & (df_rep['fecha_obj'] <= f_hasta)]
                
                if not res.empty:
                    segundos_totales = sum(res['tiempo_trabajado'].apply(convertir_a_segundos))
                    
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.metric("Tiempo Total Cumplido", formatear_segundos(segundos_totales))
                    with col_m2:
                        st.metric("Días Computados", len(res))
                        
                    st.dataframe(res[['fecha', 'entrada', 'salida', 'tiempo_trabajado', 'tipo_dia']], use_container_width=True, hide_index=True)
                else:
                    st.warning("No existen registros asociados a esos parámetros en el rango indicado.")
            except Exception as e:
                st.error(f"Fallo de cálculo: {e}")
        else:
            st.warning("Historial sin registros almacenados.")
