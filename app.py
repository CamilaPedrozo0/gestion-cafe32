import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import re

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="Gestión Horas Café 32", page_icon="☕", layout="wide")

# --- CONTROL DEL ID DE GOOGLE SHEETS DESDE LA INTERFAZ ---
st.sidebar.markdown("<h2>⚙️ Conexión Base de Datos</h2>", unsafe_allow_html=True)

# Link por defecto (vacío o el tuyo)
id_defecto = "1veKrncoLJmYwXXrNeODVembeiXT9oL9nm9le-r1ZpRg"
url_o_id_ingresado = st.sidebar.text_input("https://docs.google.com/spreadsheets/d/1veKrncoLJmYwxXrnEOdVembeiXT9oL9nm9le-r1ZpRg/edit?usp=sharing", value=id_defecto)

# FUNCIÓN INTELIGENTE: Si pegan el link entero, extrae solo el ID para que no se rompa
def extraer_id_sheets(texto):
    if "docs.google.com/spreadsheets" in texto:
        match = re.search(r'/d/([^/]+)', texto)
        if match:
            return match.group(1)
    return texto.strip()

id_sheets = extraer_id_sheets(url_o_id_ingresado)

URL_EMPLEADOS = f"https://docs.google.com/spreadsheets/d/{id_sheets}/gviz/tq?tqx=out:csv&sheet=empleados"
URL_REPORTES = f"https://docs.google.com/spreadsheets/d/{id_sheets}/gviz/tq?tqx=out:csv&sheet=reportes"

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
    if not id_sheets:
        return pd.DataFrame(columns=['legajo', 'nombre', 'puesto', 'email'])
    try:
        df = pd.read_csv(URL_EMPLEADOS)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except:
        return pd.DataFrame(columns=['legajo', 'nombre', 'puesto', 'email'])

def cargar_reportes():
    if not id_sheets:
        return pd.DataFrame(columns=['id', 'legajo', 'fecha', 'entrada', 'salida', 'tiempo_trabajado', 'tipo_dia'])
    try:
        df = pd.read_csv(URL_REPORTES)
        df.columns = df.columns.str.strip().str.lower()
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

# --- MENÚ LATERAL CLÁSICO ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 MENÚ PRINCIPAL")
menu = st.sidebar.radio(
    "Seleccioná una sección:",
    ["📊 Resumen General", "📅 Calendario de Turnos", "👤 Base de Empleados", "📤 Cargar Reporte USB", "🔍 Historial Detallado"]
)

# --- PANEL PRINCIPAL ---
st.title("☕ Gestión Horas Café 32")
st.markdown(f"**Base de datos vinculada:** `gestion horas cafe32` (ID Extraído: `{id_sheets}`)")
st.markdown("---")

# --- SECCIONES ---

if menu == "📊 Resumen General":
    st.header("Resumen General del Sistema")
    df_emp = cargar_empleados()
    df_rep = cargar_reportes()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Personal Registrado en Base", len(df_emp))
    with col2:
        st.metric("Total Fichajes en Historial", len(df_rep))
        
    st.subheader("Últimos Registros Almacenados en Google Sheets")
    if not df_rep.empty:
        st.dataframe(df_rep.tail(15), use_container_width=True, hide_index=True)
    else:
        st.info("No hay marcas históricas registradas en tu Google Sheets todavía. Si ya pegaste datos en el Excel, asegurate de que el archivo esté compartido públicamente como Lector.")

elif menu == "📅 Calendario de Turnos":
    st.header("📅 Calendario y Planificación de Turnos")
    df_emp = cargar_empleados()
    df_rep = cargar_reportes()
    
    fecha_cal = st.date_input("Seleccioná un día para auditar:", value=date.today())
    
    nombre_feriado = es_feriado(fecha_cal)
    if nombre_feriado:
        st.info(f"🔵 DÍA FERIADO NACIONAL: {nombre_feriado}")
        
    if not df_rep.empty:
        try:
            # Normalizar fechas para comparar
            df_rep['fecha_clean'] = df_rep['fecha'].astype(str).str.replace('/', '-')
            fecha_cal_str = fecha_cal.strftime('%d-%m-%Y')
            fecha_cal_str_alt = fecha_cal.strftime('%Y-%m-%d')
            
            fichajes_dia = df_rep[(df_rep['fecha_clean'] == fecha_cal_str) | (df_rep['fecha_clean'] == fecha_cal_str_alt)]
            
            if not fichajes_dia.empty:
                if not df_emp.empty:
                    df_emp['legajo'] = df_emp['legajo'].astype(int)
                    fichajes_dia['legajo'] = fichajes_dia['legajo'].astype(int)
                    df_merge = pd.merge(fichajes_dia, df_emp, on='legajo', how='left')
                else:
                    df_merge = fichajes_dia.copy()
                    df_merge['nombre'] = "Sin Base Empleados"
                
                col_m, col_t = st.columns(2)
                with col_m:
                    st.subheader("🌅 Turno Mañana (7:00 a 11:00)")
                    m_data = df_merge[df_merge['entrada'].apply(determinar_turno) == "Mañana"]
                    if not m_data.empty:
                        st.dataframe(m_data[['legajo', 'nombre', 'entrada', 'salida', 'tiempo_trabajado']], use_container_width=True, hide_index=True)
                    else:
                        st.caption("No hay ingresos registrados en la mañana.")
                with col_t:
                    st.subheader("🌇 Turno Tarde (Post 11:00)")
                    t_data = df_merge[df_merge['entrada'].apply(determinar_turno) == "Tarde"]
                    if not t_data.empty:
                        st.dataframe(t_data[['legajo', 'nombre', 'entrada', 'salida', 'tiempo_trabajado']], use_container_width=True, hide_index=True)
                    else:
                        st.caption("No hay ingresos registrados en la tarde.")
            else:
                st.warning(f"No se encontraron registros de fichajes en Google Sheets para el día {fecha_cal.strftime('%d/%m/%Y')}.")
        except Exception as e:
            st.error(f"Error procesando el calendario: {e}")
    else:
        st.error("El historial de reportes en Google Sheets está vacío.")

elif menu == "👤 Base de Empleados":
    st.header("👤 Personal Registrado")
    df_emp = cargar_empleados()
    st.subheader("Datos actuales de la pestaña: empleados")
    if not df_emp.empty:
        st.dataframe(df_emp, use_container_width=True, hide_index=True)
    else:
        st.info("No se leyeron empleados. Asegurate de rellenar la pestaña 'empleados' en tu Excel.")

elif menu == "📤 Cargar Reporte USB":
    st.header("📤 Procesar Archivo del Reloj Fichador")
    st.markdown("Subí tu archivo `.txt`. La app calculará todo de forma autónoma e inmediata.")
    
    archivo = st.file_uploader("Seleccioná tu archivo horarios.txt", type=['txt'])
    
    if archivo:
        try:
            contenido = archivo.getvalue().decode("utf-8")
            df_procesado = []
            
            for linea in contenido.splitlines():
                linea = linea.strip()
                if not linea: continue
                
                match_fecha = re.search(r'(\d{1,2})[/--](\d{1,2})[/--](\d{4})', linea)
                match_hora = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', linea)
                
                if match_fecha and match_hora:
                    fecha_str = match_fecha.group(0).replace('/', '-')
                    hora_str = match_hora.group(0)
                    
                    partes_antes = linea.split(match_fecha.group(0))[0].strip()
                    numeros = re.findall(r'\b\d+\b', partes_antes)
                    
                    if numeros:
                        legajo_int = int(numeros[0])
                        df_procesado.append({'legajo': legajo_int, 'fecha': fecha_str, 'hora': hora_str})
            
            df_raw = pd.DataFrame(df_procesado)
            
            if not df_raw.empty:
                jornadas_finales = []
                for (legajo, fecha), group in df_raw.groupby(['legajo', 'fecha']):
                    horas_ordenadas = sorted(group['hora'].tolist())
                    entrada = horas_ordenadas[0]
                    salida = horas_ordenadas[-1]
                    
                    if entrada == salida: continue
                    
                    t1 = datetime.strptime(entrada, '%H:%M:%S')
                    t2 = datetime.strptime(salida, '%H:%M:%S')
                    segundos = int((t2 - t1).total_seconds())
                    
                    try:
                        p = list(map(int, fecha.split('-')))
                        fecha_obj = date(p[2], p[1], p[0]) if p[0] < 1000 else date(p[0], p[1], p[2])
                        nom_feriado = es_feriado(fecha_obj)
                    except:
                        nom_feriado = None
                        
                    jornadas_finales.append({
                        'id': '',
                        'legajo': int(legajo),
                        'fecha': fecha,
                        'entrada': entrada,
                        'salida': salida,
                        'tiempo_trabajado': formatear_segundos(segundos),
                        'tipo_dia': f"Feriado: {nom_feriado}" if nom_feriado else "Normal"
                    })
                
                st.success("¡Archivo analizado con éxito!")
                df_res = pd.DataFrame(jornadas_finales)
                df_res = df_res[['id', 'legajo', 'fecha', 'entrada', 'salida', 'tiempo_trabajado', 'tipo_dia']]
                
                st.dataframe(df_res, use_container_width=True, hide_index=True)
                
                st.markdown("### 📥 PASO SEGUIDO:")
                st.info("Seleccioná la tabla de arriba completa con el mouse, apretá Copiar (Ctrl+C) y pegala abajo de todo en tu pestaña 'reportes' de Google Sheets.")
            else:
                st.error("No se encontraron registros legibles de marcas.")
        except Exception as e:
            st.error(f"Error procesando archivo: {e}")

elif menu == "🔍 Historial Detallado":
    st.header("🔍 Auditoría e Historial de Horas Acumuladas")
    df_rep = cargar_reportes()
    
    leg_busqueda = st.number_input("Legajo del Empleado:", min_value=1, step=1)
    f_desde = st.date_input("Desde:", value=date.today() - timedelta(days=30))
    f_hasta = st.date_input("Hasta:", value=date.today())
    
    if st.button("Calcular Horas"):
        if not df_rep.empty:
            try:
                df_rep['legajo'] = df_rep['legajo'].astype(int)
                df_rep['fecha_clean'] = df_rep['fecha'].astype(str).str.replace('/', '-')
                
                # Intentar parsear las fechas guardadas para filtrar
                def parse_fecha(x):
                    for fmt in ('%d-%m-%Y', '%Y-%m-%d'):
                        try: return datetime.strptime(x, fmt).date()
                        except: pass
                    return None
                
                df_rep['fecha_obj'] = df_rep['fecha_clean'].apply(parse_fecha)
                resultado = df_rep[(df_rep['legajo'] == leg_busqueda) & (df_rep['fecha_obj'] >= f_desde) & (df_rep['fecha_obj'] <= f_hasta)]
                
                if not resultado.empty:
                    segundos_totales = sum(resultado['tiempo_trabajado'].apply(convertir_a_segundos))
                    st.markdown(f"### ⏱️ Horas Totales Registradas: `{formatear_segundos(segundos_totales)}`")
                    st.dataframe(resultado[['fecha', 'entrada', 'salida', 'tiempo_trabajado', 'tipo_dia']], use_container_width=True, hide_index=True)
                else:
                    st.warning("No hay registros para este legajo en el rango seleccionado.")
            except Exception as e:
                st.error(f"Error al filtrar: {e}")
        else:
            st.warning("La base de datos de reportes en Google Sheets está vacía.")
