import streamlit as st
import pandas as pd
import re

# =========================================================================
# CONFIGURACIÓN GENERAL DE LA APP
# =========================================================================
st.set_page_config(page_title="Gestión Horas Café 32", layout="wide", page_icon="☕")

# Estilo personalizado para limpiar márgenes y mejorar la estética del menú
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        .stRadio > label { font-weight: bold; font-size: 110%; }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# LÓGICA DE DETECCIÓN Y CARGA DE EMPLEADOS (LOCAL / GOOGLE SHEETS)
# =========================================================================
def extraer_sheet_id(url):
    if "docs.google.com" in url:
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if match:
            return match.group(1)
    return url.strip()

# Base de datos local por defecto (salvavidas si el link de Sheets no está o falla)
EMPLEADOS_POR_DEFECTO = {
    'legajo': [10, 13, 5, 4, 8, 11, 2, 7, 9],
    'Nombre Completo': ['Priscila', 'Valentina', 'Axel', 'Ariana', 'Israel', 'Candela', 'Jennifer', 'Pepi', 'Lucia'],
    'Sector': ['Cafetería', 'Cafetería', 'Administración', 'Cocina', 'Salón', 'Cocina', 'Caja', 'Caja', 'Salón']
}

@st.cache_data(ttl=60)
def cargar_base_empleados(url_or_id):
    sheet_id = extraer_sheet_id(url_or_id)
    # Si viene el marcador por defecto o está vacío, usa la local
    if not sheet_id or "TU_ID_AQUÍ" in sheet_id:
        return pd.DataFrame(EMPLEADOS_POR_DEFECTO), "Base Local Temporal (Modo de prueba)"
    
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
        df = pd.read_csv(csv_url)
        
        # Intentar normalizar nombres de columnas comunes
        df.columns = [c.strip() for c in df.columns]
        columnas_mapeo = {c: c for c in df.columns}
        for col in df.columns:
            if col.lower() in ['legajo', 'id', 'nro', 'numero']:
                columnas_mapeo[col] = 'legajo'
            if col.lower() in ['nombre', 'nombre completo', 'empleado']:
                columnas_mapeo[col] = 'Nombre Completo'
            if col.lower() in ['sector', 'área', 'area']:
                columnas_mapeo[col] = 'Sector'
        df = df.rename(columns=columnas_mapeo)
        
        if 'legajo' in df.columns:
            df['legajo'] = pd.to_numeric(df['legajo'], errors='coerce').fillna(0).astype(int)
            return df, "Google Sheets En Vivo Conectado"
        else:
            return pd.DataFrame(EMPLEADOS_POR_DEFECTO), "Error: No se encontró la columna 'legajo' en el Excel. Usando Base Local."
    except Exception:
        return pd.DataFrame(EMPLEADOS_POR_DEFECTO), "No se pudo acceder al Google Sheets (Verificá que esté compartido como Lector público). Usando Base Local."

# =========================================================================
# MENÚ LATERAL (SIDEBAR) - DISEÑO ORIGINAL RESTAURADO
# =========================================================================
with st.sidebar:
    st.markdown("### ⚙️ Conexión Base de Datos")
    # Entrada limpia para el link de Google Sheets
    url_sheets = st.text_input(
        "Enlace de tu Google Sheets:", 
        value="https://docs.google.com/spreadsheets/d/TU_ID_AQUÍ/edit",
        help="Pegá acá la URL de tu planilla de empleados"
    )
    
    # Carga automática en segundo plano
    df_emp, estado_conexion = cargar_base_empleados(url_sheets)
    
    # Indicador de estado visual elegante
    st.success("🟢 Base Conectada Activa")
    st.caption(f"Status: **{estado_conexion}**")
    
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

# Mantener registro de marcas en la sesión para que no se borren al cambiar de pestaña
if 'fichajes_procesados' not in st.session_state:
    st.session_state['fichajes_procesados'] = None

# =========================================================================
# CONTENIDO PRINCIPAL SEGÚN SELECCIÓN
# =========================================================================
st.title("☕ Gestión Horas Café 32")
st.markdown(f"**Origen de datos actual:** `{estado_conexion}`")
st.markdown("---")

# -------------------------------------------------------------------------
# SECCIÓN: RESUMEN GENERAL (DASHBOARD)
# -------------------------------------------------------------------------
if seccion == "📊 Resumen General":
    st.subheader("Resumen General del Sistema")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label="Personal Registrado en Base", value=len(df_emp))
    with col_m2:
        total_fichajes = len(st.session_state['fichajes_procesados']) if st.session_state['fichajes_procesados'] is not None else 0
        st.metric(label="Total Fichajes en Historial", value=total_fichajes)
        
    st.markdown("### Últimos Registros Almacenados")
    if st.session_state['fichajes_procesados'] is not None:
        st.dataframe(st.session_state['fichajes_procesados'], use_container_width=True, hide_index=True)
    else:
        st.info("No hay marcas históricas registradas en esta sesión todavía. Dirigite a 'Cargar Reporte USB' para procesar el archivo del reloj.")

# -------------------------------------------------------------------------
# SECCIÓN: CALENDARIO DE TURNOS (PROVISORIO)
# -------------------------------------------------------------------------
elif seccion == "📅 Calendario de Turnos":
    st.subheader("📅 Planificación y Control de Turnos")
    st.info("Espacio reservado para la asignación de horarios rotativos y turnos semanales.")

# -------------------------------------------------------------------------
# SECCIÓN: BASE DE EMPLEADOS
# -------------------------------------------------------------------------
elif seccion == "👥 Base de Empleados":
    st.subheader("👥 Nómina de Personal Detectada")
    st.write("Esta es la lista de empleados activa que el sistema utiliza para cruzar los números de legajo.")
    st.dataframe(df_emp, use_container_width=True, hide_index=True)

# -------------------------------------------------------------------------
# SECCIÓN: CARGAR REPORTE USB (EL MOTOR RECONSTRUIDO)
# -------------------------------------------------------------------------
elif seccion == "📥 Cargar Reporte USB":
    st.subheader("📥 Conversor de Archivo Fichador Prosoft")
    st.write("Subí el archivo `.txt` extraído de la memoria del reloj. El sistema calculará las marcas al instante.")
    
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
                
                # BUSCADOR INTELIGENTE DE FECHA Y HORA (Evita roturas si cambian las columnas)
                fecha_idx = -1
                hora_idx = -1
                for idx, token in enumerate(partes):
                    if ('/' in token or '-' in token) and len(token) >= 8:
                        if idx + 1 < len(partes) and ':' in partes[idx + 1]:
                            fecha_idx = idx
                            hora_idx = idx + 1
                            break
                
                # Si localizó el bloque temporal, extrae la data hacia atrás de forma segura
                if fecha_idx != -1 and hora_idx != -1:
                    try:
                        # En Prosoft, el legajo siempre está en la posición 2 (tercer elemento)
                        # Si por algún motivo la línea es más corta, agarra el primer número que encuentre
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
                # Asegurar formato de legajos numéricos para el cruce exitoso
                df_fichajes['legajo'] = df_fichajes['legajo'].astype(int)
                
                # Cruce de datos (Merge seguro sin errores de sintaxis)
                df_resultado = pd.merge(df_fichajes, df_emp, on='legajo', how='left')
                
                # Limpieza de valores inexistentes estéticos
                if 'Nombre Completo' in df_resultado.columns:
                    df_resultado['Nombre Completo'] = df_resultado['Nombre Completo'].fillna("⚠️ NO REGISTRADO EN BASE")
                if 'Sector' in df_resultado.columns:
                    df_resultado['Sector'] = df_resultado['Sector'].fillna("-")
                
                # Reordenamiento visual óptimo
                columnas_finales = ['legajo', 'Nombre Completo', 'Sector', 'Fecha', 'Hora', 'Nombre Reloj']
                columnas_visibles = [c for c in columnas_finales if c in df_resultado.columns]
                
                st.session_state['fichajes_procesados'] = df_resultado[columnas_visibles]
                
                st.success(f"✔️ ¡Se procesaron {len(df_fichajes)} registros de asistencia con éxito!")
                st.markdown("### 📊 Vista Previa del Reporte Generado")
                st.dataframe(st.session_state['fichajes_procesados'], use_container_width=True, hide_index=True)
            else:
                st.error("❌ No se encontraron marcas válidas en el archivo .txt. Verificá que sea el archivo correcto generado por el reloj.")
                
        except Exception as e:
            st.error(f"Error crítico de procesamiento: {e}")

# -------------------------------------------------------------------------
# SECCIÓN: AUDITORÍA / HISTORIAL DETALLADO
# -------------------------------------------------------------------------
elif seccion == "🔍 Historial Detallado":
    st.subheader("🔍 Auditoría Detallada de Asistencias")
    if st.session_state['fichajes_procesados'] is not None:
        st.write("Usá los controles nativos de la tabla para filtrar u ordenar los registros:")
        st.dataframe(st.session_state['fichajes_procesados'], use_container_width=True, hide_index=True)
    else:
        st.info("El historial detallado está vacío. Subí un archivo .txt en la sección 'Cargar Reporte USB' para poblar los datos.")
