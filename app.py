import streamlit as st
import pandas as pd
import re

# =========================================================================
# CONFIGURACIÓN GENERAL DE LA APP
# =========================================================================
st.set_page_config(page_title="Gestión Horas Café 32", layout="wide", page_icon="☕")

# Estilo personalizado para limpiar márgenes superiores
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        .stRadio > label { font-weight: bold; font-size: 110%; }
    </style>
""", unsafe_allow_html=True)

# Inicializar la memoria de empleados manuales si no existe para que no se borren
if 'empleados_manuales' not in st.session_state:
    st.session_state['empleados_manuales'] = pd.DataFrame(columns=['legajo', 'Nombre Completo', 'Sector'])

# =========================================================================
# LÓGICA DE CARGA AUTOMÁTICA DE EMPLEADOS
# =========================================================================
def extraer_sheet_id(url):
    if "docs.google.com" in url:
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if match:
            return match.group(1)
    return url.strip()

# Tu lista oficial cargada directamente en el código de forma indestructible
EMPLEADOS_POR_DEFECTO = {
    'legajo': [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 13],
    'Nombre Completo': ['Camila', 'Jennifer', 'Joel', 'Ariana', 'Axel', 'Pepi', 'Israel', 'Lucia', 'Priscila', 'Candela', 'Valentina'],
    'Sector': ['Salón', 'Caja', 'Cafetería', 'Cocina', 'Administración', 'Caja', 'Salón', 'Salón', 'Cafetería', 'Cocina', 'Cafetería']
}

@st.cache_data(ttl=10)
def cargar_base_sheets(url_or_id):
    sheet_id = extraer_sheet_id(url_or_id)
    if not sheet_id or "TU_ID_AQUÍ" in sheet_id:
        return None, "Usando lista interna del sistema (No se ingresó Google Sheets)"
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
            return df[['legajo', 'Nombre Completo', 'Sector']], "Google Sheets Conectado Correctamente"
    except Exception:
        return None, "Error de enlace o no está público. Usando lista interna."
    return None, "Columnas inválidas en Sheets. Usando lista interna."

# =========================================================================
# PANEL LATERAL DE CONTROL (SIDEBAR)
# =========================================================================
with st.sidebar:
    st.markdown("### ⚙️ Conexión Base de Datos")
    # ACÁ ES DONDE SE PEGA EL LINK DEL GOOGLE SHEETS 👇
    url_sheets = st.text_input(
        "Enlace de tu Google Sheets:", 
        value="https://docs.google.com/spreadsheets/d/TU_ID_AQUÍ/edit",
        help="Pegá la URL completa de tu Google Sheet compartido como Lector público."
    )
    
    df_base_sheets, estado_conexion = cargar_base_sheets(url_sheets)
    
    if df_base_sheets is not None:
        df_base = df_base_sheets
        st.success("🟢 Base Sheets Activa")
    else:
        df_base = pd.DataFrame(EMPLEADOS_POR_DEFECTO)
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

# Unificar datos base (Sistemas/Sheets) con los que agregues manualmente en caliente
df_manual = st.session_state['empleados_manuales']
df_emp = pd.concat([df_base, df_manual]).drop_duplicates(subset=['legajo'], keep='last')
df_emp['legajo'] = df_emp['legajo'].astype(int)

if 'fichajes_procesados' not in st.session_state:
    st.session_state['fichajes_procesados'] = None

# =========================================================================
# CONTENIDO CENTRAL DE LA APLICACIÓN
# =========================================================================
st.title("☕ GESTIÓN DE HORAS - CAFE32")
st.markdown("---")

# 1. SECCIÓN: RESUMEN GENERAL
if seccion == "📊 Resumen General":
    st.subheader("Resumen General del Sistema")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label="Personal Total Registrado", value=len(df_emp))
    with col_m2:
        total_fichajes = len(st.session_state['fichajes_procesados']) if st.session_state['fichajes_procesados'] is not None else 0
        st.metric(label="Total Fichajes en esta Sesión", value=total_fichajes)
        
    st.markdown("### Últimos Registros Procesados")
    if st.session_state['fichajes_procesados'] is not None:
        st.dataframe(st.session_state['fichajes_procesados'], use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay marcas de asistencia guardadas en esta sesión. Dirigite a 'Cargar Reporte USB' para procesar el archivo.")

# 2. SECCIÓN: CALENDARIO DE TURNOS
elif seccion == "📅 Calendario de Turnos":
    st.subheader("📅 Planificación y Control de Turnos")
    st.info("Espacio reservado para la asignación de horarios rotativos y turnos semanales.")

# 3. SECCIÓN: BASE DE EMPLEADOS (CON FORMULARIO MANUAL INCORPORADO)
elif seccion == "👥 Base de Empleados":
    st.subheader("👥 Registro y Nómina de Personal")
    
    # FORMULARIO MANUAL INTEGRADO DIRECTAMENTE ACÁ
    with st.expander("➕ Registrar / Agregar Nuevo Empleado Manualmente", expanded=False):
        with st.form("form_nuevo_empleado"):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_legajo = st.number_input("Número de Legajo (Igual al del Reloj):", min_value=1, max_value=9999, step=1)
                nuevo_nombre = st.text_input("Nombre Completo del Empleado:")
            with col2:
                nuevo_sector = st.selectbox("Sector asignado:", ["Cafetería", "Cocina", "Salón", "Caja", "Administración", "Limpieza"])
            
            boton_guardar = st.form_submit_button("Guardar Empleado")
            
            if boton_guardar:
                if nuevo_nombre.strip() == "":
                    st.error("El nombre no puede estar vacío.")
                else:
                    nueva_fila = pd.DataFrame([{
                        'legajo': int(nuevo_legajo),
                        'Nombre Completo': nuevo_nombre.strip(),
                        'Sector': nuevo_sector
                    }])
                    st.session_state['empleados_manuales'] = pd.concat([st.session_state['empleados_manuales'], nueva_fila], ignore_index=True)
                    st.success(f"¡{nuevo_nombre} fue agregado con éxito al sistema local!")
                    st.rerun()

    st.markdown("### 📋 Lista General de Personal Activo")
    st.write("Esta tabla combina la lista automática/Sheets junto con los empleados que cargues a mano arriba.")
    st.dataframe(df_emp.sort_values(by='legajo'), use_container_width=True, hide_index=True)

# 4. SECCIÓN: CARGAR REPORTE USB (EL MOTOR REPARADO)
elif seccion == "📥 Cargar Reporte USB":
    st.subheader("📥 Conversor de Archivo Fichador Prosoft")
    st.write("Subí el archivo `.txt` extraído de la memoria del reloj para cruzarlo con el personal.")
    
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
                    df_resultado['Nombre Completo'] = df_resultado['Nombre Completo'].fillna("⚠️ NO REGISTRADO EN BASE")
                if 'Sector' in df_resultado.columns:
                    df_resultado['Sector'] = df_resultado['Sector'].fillna("-")
                
                columnas_finales = ['legajo', 'Nombre Completo', 'Sector', 'Fecha', 'Hora', 'Nombre Reloj']
                columnas_visibles = [c for c in columnas_finales if c in df_resultado.columns]
                
                st.session_state['fichajes_procesados'] = df_resultado[columnas_visibles]
                
                st.success(f"✔️ ¡Se procesaron {len(df_fichajes)} marcas con éxito!")
                st.dataframe(st.session_state['fichajes_procesados'], use_container_width=True, hide_index=True)
            else:
                st.error("❌ No se encontraron marcas válidas en el archivo .txt. Verificá el formato.")
        except Exception as e:
            st.error(f"Error crítico en el motor de lectura: {e}")

# 5. SECCIÓN: HISTORIAL DETALLADO
elif seccion == "🔍 Historial Detallado":
    st.subheader("🔍 Auditoría Detallada de Asistencias")
    if st.session_state['fichajes_procesados'] is not None:
        st.dataframe(st.session_state['fichajes_procesados'], use_container_width=True, hide_index=True)
    else:
        st.info("El historial está vacío. Cargá un archivo en la sección 'Cargar Reporte USB' primero.")
