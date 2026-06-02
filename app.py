import streamlit as st
import pandas as pd

# =========================================================================
# CONFIGURACIÓN DE LA PÁGINA
# =========================================================================
st.set_page_config(page_title="GESTION DE HORAS CAFE32", layout="wide", page_icon="☕")

# Título principal de la aplicación
st.title("☕ GESTIÓN DE HORAS - CAFE32")
st.markdown("---")

# =========================================================================
# CONTROL DE LA BASE DE DATOS (MANTENER EMPLEADOS EN MEMORIA)
# =========================================================================
# Usamos el estado de Streamlit (session_state) para que los empleados no se borren al hacer clic
if 'base_empleados' not in st.session_state:
    # Cargamos una lista inicial basada en tu archivo de texto para que ya funcione de una
    datos_iniciales = {
        'legajo': [10, 13, 5, 4, 8, 11, 2, 7, 9],
        'Nombre Completo': ['Priscila', 'Valentina', 'Axel', 'Ariana', 'Israel', 'Candela', 'Jennifer', 'Pepi', 'Lucia'],
        'Sector': ['Cafetería', 'Cafetería', 'Administración', 'Cocina', 'Salón', 'Cocina', 'Caja', 'Caja', 'Salón'],
        'Contacto': ['-', '-', '-', '-', '-', '-', '-', '-', '-']
    }
    st.session_state['base_empleados'] = pd.DataFrame(datos_iniciales)

# Forzamos siempre que la columna legajo sea un número entero
st.session_state['base_empleados']['legajo'] = st.session_state['base_empleados']['legajo'].astype(int)
df_emp = st.session_state['base_empleados']


# =========================================================================
# DISEÑO DE PESTAÑAS (NAVEGACIÓN INTERNA)
# =========================================================================
tab1, tab2 = st.tabs(["📊 Procesar Fichajes (TXT)", "👥 Base de Empleados (150 Máx)"])

# =========================================================================
# PESTAÑA 1: PROCESAR ASISTENCIA DESDE EL TXT
# =========================================================================
with tab1:
    st.subheader("📥 Subir archivo del Reloj Prosoft C109")
    st.write("Subí el archivo de texto directamente como sale del pendrive del reloj.")
    
    uploaded_file = st.file_uploader("Seleccionar archivo .txt", type=["txt"], key="procesador_txt")

    if uploaded_file is not None:
        try:
            # Leer el archivo de texto completo
            contenido = uploaded_file.getvalue().decode("utf-8")
            lineas_procesadas = []
            
            # Recorrer cada línea del TXT limpiando las impurezas del reloj
            for linea in contenido.splitlines():
                # Omitir líneas vacías o encabezados del sistema Prosoft
                if "UDISKLOG" in linea or "No" in linea or "DateTime" in linea or not linea.strip():
                    continue
                
                # Quitar el punto final (.) de la hora y espacios invisibles raros (\xa0)
                linea_limpia = linea.replace('\xa0', ' ').strip().rstrip('.')
                
                # Separar la línea por columnas de espacio
                partes = linea_limpia.split()
                
                # Si la línea tiene los datos requeridos
                if len(partes) >= 7:
                    try:
                        # Convertir EnNo (000000010) a entero (10)
                        legajo_id = int(partes[2])
                        
                        # Capturar el nombre del reloj de forma segura
                        nombre_reloj = " ".join(partes[3:-4]) if len(partes) > 7 else partes[3]
                        
                        # Unir la fecha y la hora finales
                        fecha_texto = partes[-2]
                        hora_texto = partes[-1]
                        fecha_hora_combinada = f"{fecha_texto} {hora_texto}"
                        
                        lineas_procesadas.append({
                            'legajo': legajo_id,
                            'Nombre Reloj': nombre_reloj,
                            'Fecha_Hora_Original': fecha_hora_combinada
                        })
                    except ValueError:
                        continue

            # Crear tabla con las marcas encontradas
            fichajes_dia = pd.DataFrame(lineas_procesadas)
            
            if not fichajes_dia.empty:
                # Convertir a formato de tiempo real de Python
                fichajes_dia['Fecha_Hora'] = pd.to_datetime(
                    fichajes_dia['Fecha_Hora_Original'], 
                    format='%Y/%m/%d %H:%M:%S', 
                    errors='coerce'
                )
                
                # Formatear la vista final para comodidad visual
                fichajes_dia['Fecha'] = fichajes_dia['Fecha_Hora'].dt.strftime('%d/%m/%Y')
                fichajes_dia['Hora'] = fichajes_dia['Fecha_Hora'].dt.strftime('%H:%M:%S')
                fichajes_dia = fichajes_dia.drop(columns=['Fecha_Hora_Original'])
                
                st.success(f"✔️ ¡Fichajes leídos correctamente! Se encontraron {len(fichajes_dia)} registros.")
                
                # CRUCE DE DATOS CON TU BASE DE EMPLEADOS (LA FAMOSA LÍNEA 175 CORREGIDA)
                df_merge = pd.merge(fichajes_dia, df_emp, on='legajo', how='left')
                
                st.markdown("### 📊 Reporte Cruzado Final")
                st.write("Si el 'Nombre Completo' aparece como 'Inexistente o Vacío', significa que el legajo no está cargado en la Base de Empleados.")
                
                # Reorganizar el orden de las columnas para tu pantalla
                columnas_ordenadas = ['legajo', 'Nombre Completo', 'Sector', 'Fecha', 'Hora', 'Nombre Reloj']
                columnas_visibles = [c for c in columnas_ordenadas if c in df_merge.columns]
                
                # Rellenar datos de empleados no encontrados para que no aparezca como "NaN" feo
                if 'Nombre Completo' in df_merge.columns:
                    df_merge['Nombre Completo'] = df_merge['Nombre Completo'].fillna("⚠️ NO REGISTRADO EN BASE")
                if 'Sector' in df_merge.columns:
                    df_merge['Sector'] = df_merge['Sector'].fillna("-")
                
                # Mostrar el resultado final en la app
                st.dataframe(df_merge[columnas_visibles], use_container_width=True)
                
            else:
                st.error("❌ No se pudieron extraer marcas válidas del archivo. Revisá que sea el TXT correcto.")
                
        except Exception as e:
            st.error(f"Error crítico al procesar el archivo: {e}")

# =========================================================================
# PESTAÑA 2: GESTIÓN DE LA BASE DE DATOS DE EMPLEADOS
# =========================================================================
with tab2:
    st.subheader("👥 Registro y Control de Personal")
    
    # Formulario para dar de alta nuevos empleados en el sistema
    with st.expander("➕ Registrar Nuevo Empleado"):
        with st.form("nuevo_empleado_form"):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_legajo = st.number_input("Número de Legajo (Igual al del Reloj):", min_value=1, max_value=9999, step=1)
                nuevo_nombre = st.text_input("Nombre Completo del Empleado:")
            with col2:
                nuevo_sector = st.selectbox("Sector asignado:", ["Cafetería", "Cocina", "Salón", "Caja", "Administración", "Limpieza"])
                nuevo_contacto = st.text_input("Teléfono / Contacto (Opcional):", value="-")
                
            boton_guardar = st.form_submit_button("Guardar Empleado")
            
            if boton_guardar:
                if nuevo_nombre.strip() == "":
                    st.error("El nombre no puede estar vacío.")
                elif nuevo_legajo in df_emp['legajo'].values:
                    st.error(f"El número de legajo {nuevo_legajo} ya pertenece a otro empleado.")
                else:
                    # Añadir el nuevo registro a la tabla general
                    nueva_fila = pd.DataFrame([{
                        'legajo': int(nuevo_legajo),
                        'Nombre Completo': nuevo_nombre.strip(),
                        'Sector': nuevo_sector,
                        'Contacto': nuevo_contacto.strip()
                    }])
                    st.session_state['base_empleados'] = pd.concat([df_emp, nueva_fila], ignore_index=True)
                    st.success(f"¡{nuevo_nombre} fue guardado con éxito!")
                    st.rerun()

    # Mostrar la nómina actual de empleados cargados
    st.markdown
