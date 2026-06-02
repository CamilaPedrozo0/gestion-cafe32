import streamlit as st
import pandas as pd
import re

# =========================================================================
# 🚨 CONFIGURACIÓN: PEGÁ TU LINK DE GOOGLE SHEETS ACÁ ADENTRO 👇
# =========================================================================
URL_SISTEMA = "https://docs.google.com/spreadsheets/d/1veKrncoLJmYwxXrnEOdVembeiXT9oL9nm9le-r1ZpRg/edit?usp=sharing"
# =========================================================================

st.set_page_config(page_title="Gestión Horas Café 32", layout="wide", page_icon="☕")

# Estilo para limpiar márgenes
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        .stRadio > label { font-weight: bold; font-size: 110%; }
    </style>
""", unsafe_allow_html=True)

# Inicializar memoria interna de la app
if 'empleados_manuales' not in st.session_state:
    st.session_state['empleados_manuales'] = pd.DataFrame(columns=['legajo', 'Nombre Completo', 'Sector'])

if 'fichajes_procesados' not in st.session_state:
    st.session_state['fichajes_procesados'] = None

# Lógica de extracción de ID
def extraer_sheet_id(url):
    if "docs.google.com" in url:
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if match:
            return match.group(1)
    return url.strip()

# Lista oficial con sectores en limpio (-) para que los edites vos
EMPLEADOS_POR_DEFECTO = {
    'legajo': [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 13],
    'Nombre Completo': ['Camila', 'Jennifer', 'Joel', 'Ariana', 'Axel', 'Pepi', 'Israel', 'Lucia', 'Priscila', 'Candela', 'Valentina'],
    'Sector': ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-']
}

@st.cache_data(ttl=5)
def cargar_base_sheets(url_or_id):
    sheet_id = extraer_sheet_id(url_or_id)
    if not sheet_id or "TU_ID_AQUÍ" in sheet_id:
        return None, "Usando lista interna (No se configuró Sheets)"
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
        df = pd.read_csv(csv_url)
        df.columns = [c.strip() for c in df.columns]
        columnas_mapeo = {}
        for col in df.columns:
            if col.lower() in ['legajo', 'id', 'nro', 'numero']:
                columnas_mapeo[col] = 'legajo'
            if col.lower() in ['nombre', 'nombre completo', 'empleado']:
                columnas_mapeo[col] = 'Nombre Completo'
            if col.lower() in ['sector', 'área', 'area']:
                columnas_mapeo[col] = 'Sector'
        df = df.rename(columns=columnas_mapeo)
        if 'legajo' in df.columns and 'Nombre Completo' in df.columns:
            df['legajo'] = pd.to_numeric(df['legajo'], errors='coerce').fillna(0).astype(int)
            return df[['legajo', 'Nombre Completo', 'Sector']], "Conectado a Google Sheets"
    except Exception:
        return None, "Sheets no detectado o privado. Usando lista interna."
    return None, "Columnas de Sheets no compatibles. Usando lista interna."

# Procesar la base de datos de fondo usando el link oculto de la Línea 7
df_base_sheets, estado_conexion = cargar_base_sheets(URL_SISTEMA)
if df_base_sheets is not None:
    df_base = df_base_sheets
else:
    df_base = pd.DataFrame(EMPLEADOS_POR_DEFECTO)

# Unificar listas (Prioriza siempre lo último que edites o agregues en la app)
df_manual = st.session_state['empleados_manuales']
df_emp = pd.concat([df_base, df_manual]).drop_duplicates(subset=['legajo'], keep='last')
df_emp['legajo'] = df_emp['legajo'].astype(int)

# =========================================================================
# MENÚ LATERAL (SIDEBAR CLEAN - SIN LINKS A LA VISTA)
# =========================================================================
with st.sidebar:
    st.markdown("### ⚙️ Estado del Sistema")
    if df_base_sheets is not None:
        st.success("🟢 Base en línea vinculada")
    else:
        st.info(f"ℹ️ {estado_conexion}")
        
    st.markdown("---")
    st.markdown("### 📑 MENÚ PRINCIPAL")
    
    seccion = st.radio(
        "Seleccioná una sección:",
        [
            "📊 Resumen General", 
            "📅 Calendario de Turnos", 
            "👥 Base de Empleados", 
            "📥 Cargar Reporte USB", 
            "🔍 Historial Detallado"
        ]
    )

# =========================================================================
# CONTENIDO CENTRAL
# =========================================================================
st.title("☕ GESTIÓN DE HORAS - CAFE32")
st.markdown("---")

# 1. RESUMEN GENERAL
if seccion == "📊 Resumen General":
    st.subheader("Resumen General del Sistema")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label="Personal Activo Registrado", value=len(df_emp))
    with col_m2:
        total_fichajes = len(st.session_state['fichajes_procesados']) if st.session_state['fichajes_procesados'] is not None else 0
        st.metric(label="Últimos Fichajes Procesados", value=total_fichajes)
        
    st.markdown("### Historial de la Sesión")
    if st.session_state['fichajes_procesados'] is not None:
        st.dataframe(st.session_state['fichajes_procesados'], use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay marcas de asistencia guardadas. Dirigite a 'Cargar Reporte USB' para procesar el archivo.")

# 2. CALENDARIO
elif seccion == "📅 Calendario de Turnos":
    st.subheader("📅 Planificación y Control de Turnos")
    st.info("Espacio reservado para turnos y diagramas horarios.")

# 3. BASE DE EMPLEADOS (AGREGAR Y EDITAR MANAL)
elif seccion == "👥 Base de Empleados":
    st.subheader("👥 Registro y Nómina de Personal")
    
    with st.expander("➕ Agregar nuevo empleado / Editar Sector de uno existente", expanded=False):
        with st.form("form_nuevo_empleado"):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_legajo = st.number_input("Número de Legajo (ID del Reloj):", min_value=1, max_value=9999, step=1)
                nuevo_nombre = st.text_input("Nombre Completo:")
            with col2:
                nuevo_sector = st.selectbox("Sector asignado:", ["Cafetería", "Cocina", "Salón", "Caja", "Administración", "-"])
            
            boton_guardar = st.form_submit_button("Guardar Cambios")
            
            if boton_guardar:
                if nuevo_nombre.strip() == "":
                    st.error("Por favor, poné un nombre válido.")
                else:
                    nueva_fila = pd.DataFrame([{
                        'legajo': int(nuevo_legajo),
                        'Nombre Completo': nuevo_nombre.strip(),
                        'Sector': nuevo_sector
                    }])
                    st.session_state['empleados_manuales'] = pd.concat([st.session_state['empleados_manuales'], nueva_fila], ignore_index=True)
                    st.success(f"¡Datos guardados para {nuevo_nombre} (Legajo {nuevo_legajo})!")
                    st.rerun()

    st.markdown("### 📋 Lista General de Personal Activo")
    st.dataframe(df_emp.sort_values(by='legajo'), use_container_width=True, hide_index=True)

# 4. CARGAR REPORTE USB (MOTOR TXT PROSOFT)
elif seccion == "📥 Cargar Reporte USB":
    st.subheader("📥 Conversor de Archivo Fichador Prosoft")
    st.write("Subí el archivo `.txt` del reloj para cruzar las marcas de tiempo.")
    
    uploaded_file = st.file_uploader("Subir archivo .txt", type=["txt"])
    
    if uploaded_file is not None:
        try:
            contenido = uploaded_file.getvalue().decode("utf-8")
            lineas_procesadas = []
            
            for linea in contenido.splitlines():
                linea_limpia = linea.replace('\xa0', ' ').strip().rstrip('.')
                if "UDISKLOG" in linea_limpia or "DateTime" in linea_limpia or not linea_limpia:
                    continue
                
                partes = linea_limpia.split()
                if len(partes) < 4:
                    continue
                
                fecha_idx = -1
                hora_idx = -1
                for idx, token in enumerate(partes):
                    if ('/' in token or '-' in token) and len(token) >= 8:
                        if idx + 1 < len(partes) and ':' in partes[idx + 1]:
                            fecha_idx = idx
                            hora_idx = idx + 1
                            break
                
                if fecha_idx != -1 and hora_idx != -1:
                    try:
                        if fecha_idx >= 3:
                            legajo_id = int(partes[2])
                            nombre_reloj = " ".join(partes[3:fecha_idx])
                        else:
                            legajo_id = int(partes[0])
                            nombre_reloj = " ".join(partes[1:fecha_idx])
                        
                        lineas_procesadas.append({
                            'legajo': legajo_id,
                            'Nombre Reloj': nombre_reloj,
                            'Fecha': partes[fecha_idx],
                            'Hora': partes[hora_idx]
                        })
                    except ValueError:
                        continue

            df_fichajes = pd.DataFrame(lineas_procesadas)
            
            if not df_fichajes.empty:
                df_fichajes['legajo'] = df_fichajes['legajo'].astype(int)
                df_resultado = pd.merge(df_fichajes, df_emp, on='legajo', how='left')
                
                if 'Nombre Completo' in df_resultado.columns:
                    df_resultado['Nombre Completo'] = df_resultado['Nombre Completo'].fillna("⚠️ LEGAJO NO REGISTRADO")
                if 'Sector' in df_resultado.columns:
                    df_resultado['Sector'] = df_resultado['Sector'].fillna("-")
                
                columnas_finales = ['legajo', 'Nombre Completo', 'Sector', 'Fecha', 'Hora', 'Nombre Reloj']
                columnas_visibles = [c for c in columnas_finales if c in df_resultado.columns]
                
                st.session_state['fichajes_procesados'] = df_resultado[columnas_visibles]
                
                st.success(f"✔️ ¡Se procesaron {len(df_fichajes)} marcas con éxito!")
                st.dataframe(st.session_state['fichajes_procesados'], use_container_width=True, hide_index=True)
            else:
                st.error("❌ El archivo TXT no contiene marcas compatibles o legajos válidos.")
        except Exception as e:
            st.error(f"Error procesando el archivo: {e}")

# 5. HISTORIAL DETALLADO
elif seccion == "🔍 Historial Detallado":
    st.subheader("🔍 Auditoría Detallada de Asistencias")
    if st.session_state['fichajes_procesados'] is not None:
        st.dataframe(st.session_state['fichajes_procesados'], use_container_width=True, hide_index=True)
    else:
        st.info("Historial vacío. Cargá el archivo `.txt` desde la sección 'Cargar Reporte USB'.")
