import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import re

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="Gestión Horas Café 32", page_icon="☕", layout="wide")

# --- CONTROL DEL ID DE GOOGLE SHEETS DESDE LA INTERFAZ ---
st.sidebar.markdown("## ⚙️ Conexión Base de Datos")

# Si tenés un ID fijo lo podés poner acá, sino lo pegás directo en la pantalla de la app
id_defecto = "TU_ID_DE_GOOGLE_SHEETS_AQUI"
id_sheets = st.sidebar.text_input("Pegá acá el ID de tu Google Sheets:", value=id_defecto)

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
    if id_sheets == "TU_ID_DE_GOOGLE_SHEETS_AQUI" or not id_sheets:
        return pd.DataFrame(columns=['legajo', 'nombre', 'puesto', 'email'])
    try:
        df = pd.read_csv(URL_EMPLEADOS)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except:
        return pd.DataFrame(columns=['legajo', 'nombre', 'puesto', 'email'])

def cargar_reportes():
    if id_sheets == "TU_ID_DE_GOOGLE_SHEETS_AQUI" or not id_sheets:
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
st.markdown(f"**Base de datos vinculada:** `gestion horas cafe32` (ID: {id_sheets})")
st.markdown("---")

if id_sheets == "TU_ID_DE_GOOGLE_SHEETS_AQUI" or not id_sheets:
    st.warning("⚠️ Recordá ingresar el ID correcto de tu Google Sheets en la barra lateral izquierda para habilitar la sincronización de la base de datos.")

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
        
    st.subheader("Últimos Registros Almacenados")
    if not df_rep.empty:
        st.dataframe(df_rep.tail(10), use_container_width=True, hide_index=True)
    else:
        st.info("No hay marcas históricas registradas en tu Google Sheets todavía.")

elif menu == "📅 Calendario de Turnos":
    st.header("📅 Calendario y Planificación de Turnos")
    df_emp = cargar_empleados()
    df_rep = cargar_reportes()
    
    fecha_cal = st.date_input("Seleccioná un día para auditar:", value=date.today())
    
    nombre_feriado = es_feriado(fecha_cal)
    if nombre_feriado:
        st.info(f"🔵 DÍA FERIADO NACIONAL: {nombre_feriado}")
        
    if not df_rep.empty:
        df_rep['fecha_dt'] = pd.to_datetime(df_rep['fecha'], errors='coerce').dt.date
        fichajes_dia = df_rep[df_rep['fecha_dt'] == fecha_cal]
        
        if not fichajes_dia.empty and not df_emp.empty:
            df_merge = pd.merge(fichajes_dia, df_emp, on='legajo', how='left')
            
            col_m, col_t = st.columns(2)
            with col_m:
                st.subheader("🌅 Turno Mañana (7:00 a 11:00)")
                m_data = df_merge[df_merge['entrada'].apply(determinar_turno) == "Mañana"]
                if not m_data.empty:
                    st.dataframe(m_data[['legajo', 'nombre', 'entrada', 'salida', 'tiempo_trabajado']], use_container_width=True, hide_index=True)
                else:
                    st.caption("No hay ingresos registrados en la mañana para esta fecha.")
            with col_t:
                st.subheader("🌇 Turno Tarde (Post 11:00)")
                t_data = df_merge[df_merge['entrada'].apply(determinar_turno) == "Tarde"]
                if not t_data.empty:
                    st.dataframe(t_data[['legajo', 'nombre', 'entrada', 'salida', 'tiempo_trabajado']], use_container_width=True, hide_index=True)
                else:
                    st.caption("No hay ingresos registrados en la tarde para esta fecha.")
        else:
            st.warning("No se encontraron registros cargados en Google Sheets para el día seleccionado.")
    else:
        st.error("El historial de reportes en Google Sheets está vacío.")

elif menu == "👤 Base de Empleados":
    st.header("👤 Personal Registrado")
    if id_sheets != "TU_ID_DE_GOOGLE_SHEETS_AQUI" and id_sheets:
        st.markdown(f"[➡️ Abrir planilla 'gestion horas cafe32' en Google Drive](https://docs.google.com/spreadsheets/d/{id_sheets})")
    
    df_emp = cargar_empleados()
    st.subheader("Pestaña actual: empleados")
    if not df_emp.empty:
        st.dataframe(df_emp[['legajo', 'nombre', 'puesto', 'email']], use_container_width=True, hide_index=True)
    else:
        st.info("Sin registros visuales. Completá las filas en Google Sheets para sincronizar la nómina.")

elif menu == "📤 Cargar Reporte USB":
    st.header("📤 Procesar Archivo del Reloj Fichador")
    st.markdown("Subí el archivo `.txt` extraído del reloj Prosoft. La app lo va a procesar en el acto de forma autónoma.")
    
    archivo = st.file_uploader("Seleccioná el archivo horarios.txt", type=['txt'])
    
    if archivo:
        try:
            contenido = archivo.getvalue().decode("utf-8")
            df_procesado = []
            
            # ESCÁNER ROBUSTO LÍNEA POR LÍNEA (Ignora textos inválidos automáticamente)
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
                
                # Forzar las columnas idénticas a la pestaña de reportes del usuario
                df_res = df_res[['id', 'legajo', 'fecha', 'entrada', 'salida', 'tiempo_trabajado', 'tipo_dia']]
                st.dataframe(df_res, use_container_width=True, hide_index=True)
                
                st.markdown("### 📥 ¿Cómo pasar esto a tu Google Sheets?")
                st.info("Como Google Sheets actúa de base de datos segura, seleccioná las filas de arriba con el mouse, copialas (Ctrl+C) y pegalas directamente al final de tu pestaña **'reportes'**.")
                if id_sheets != "TU_ID_DE_GOOGLE_SHEETS_AQUI" and id_sheets:
                    st.markdown(f"[➡️ Hacer clic acá para abrir tu planilla gestion horas cafe32 y pegar los datos](https://docs.google.com/spreadsheets/d/{id_sheets})")
            else:
                st.error("No se encontraron registros de fichajes válidos con formato de Legajo, Fecha y Hora en este archivo.")
        except Exception as e:
            st.error(f"Error crítico al leer el archivo: {e}")

elif menu == "🔍 Historial Detallado":
    st.header("🔍 Auditoría e Historial de Horas Acumuladas")
    df_rep = cargar_reportes()
    
    leg_busqueda = st.number_input("Ingresá el Legajo del Empleado a consultar:", min_value=1, step=1)
    f_desde = st.date_input("Desde el día:", value=date.today() - timedelta(days=30))
    f_hasta = st.date_input("Hasta el día:", value=date.today())
    
    if st.button("Calcular Resumen de Horas"):
        if not df_rep.empty:
            try:
                df_rep['legajo'] = df_rep['legajo'].astype(int)
                df_rep['fecha_dt'] = pd.to_datetime(df_rep['fecha'], errors='coerce').dt.date
                
                resultado = df_rep[(df_rep['legajo'] == leg_busqueda) & (df_rep['fecha_dt'] >= f_desde) & (df_rep['fecha_dt'] <= f_hasta)]
                
                if not resultado.empty:
                    segundos_totales = 0
                    segundos_feriados = 0
                    for _, fila in resultado.iterrows():
                        t_str = fila['tiempo_trabajado']
                        seg = convertir_a_segundos(t_str)
                        segundos_totales += seg
                        if "Feriado" in str(fila['tipo_dia']):
                            segundos_feriados += seg
                            
                    st.markdown(f"### ⏱️ Tiempo total cumplido en el período: `{formatear_segundos(segundos_totales)}`")
                    if segundos_feriados > 0:
                        st.markdown(f"### 🔵 Horas acumuladas en días Feriados: `{formatear_segundos(segundos_feriados)}`")
                    
                    st.dataframe(resultado[['fecha', 'entrada', 'salida', 'tiempo_trabajado', 'tipo_dia']], use_container_width=True, hide_index=True)
                else:
                    st.warning("No se encontraron registros para ese legajo en el rango de fechas seleccionado.")
            except Exception as e:
                st.error(f"Ocurrió un inconveniente al filtrar los datos: {e}")
        else:
            st.warning("La base de datos de reportes en Google Sheets no contiene registros.")
