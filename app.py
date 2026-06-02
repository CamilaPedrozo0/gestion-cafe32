import pandas as pd
import re

# Supongamos que 'uploaded_file' es el archivo que subís en Streamlit
if uploaded_file is not None:
    # 1. Leer todo el contenido del archivo de texto
    contenido = uploaded_file.getvalue().decode("utf-8")
    lineas_limpias = []
    
    # 2. Procesar línea por línea
    for linea in contenido.splitlines():
        # Ignoramos las líneas vacías o los encabezados del reloj
        if "UDISKLOG" in linea or "No" in linea or "DateTime" in linea or not linea.strip():
            continue
        
        # Quitamos el molesto punto (.) que tiene el archivo al final de cada hora
        linea_limpia = linea.strip().rstrip('.')
        
        # Separamos la línea por las tabulaciones (\t)
        partes = [p.strip() for p in linea_limpia.split('\t') if p.strip()]
        
        # Si la línea tiene la cantidad de datos correcta (ej: No, Mchn, EnNo, Name, Mode, IOMd, DateTime)
        if len(partes) >= 6:
            no_registro = partes[0]
            mchn = partes[1]
            
            # EnNo (Enroll Number) suele ser el número de Legajo real en el reloj (ej: 000000010 -> 10)
            legajo_id = int(partes[2]) 
            
            nombre_empleado = partes[3].strip()
            
            # La fecha y hora siempre están al final de la línea
            fecha_hora_texto = partes[-1] 
            
            # Guardamos los datos limpios en nuestra lista
            lineas_limpias.append({
                'legajo': legajo_id,
                'nombre_reloj': nombre_empleado,
                'fecha_hora_original': fecha_hora_texto
            })
            
    # 3. Convertir todo a una tabla (DataFrame) de Pandas
    fichajes_dia = pd.DataFrame(lineas_limpias)
    
    if not fichajes_dia.empty:
        # Limpiamos los espacios raros de la fecha/hora y la convertimos a formato real de Python
        fichajes_dia['fecha_hora'] = pd.to_datetime(
            fichajes_dia['fecha_hora_original'].str.replace(r'\xa0', ' ', regex=True), 
            format='%Y/%m/%d %H:%M:%S', 
            errors='coerce'
        )
        
        # Creamos columnas separadas de Fecha y Hora por si las necesitás para sumar
        fichajes_dia['Fecha'] = fichajes_dia['fecha_hora'].dt.date
        fichajes_dia['Hora'] = fichajes_dia['fecha_hora'].dt.time
        
        st.success(f"¡Éxito! Se procesaron {len(fichajes_dia)} registros de asistencia.")
        
        # 4. Cruzamos los datos con tu base de datos de empleados de Google Sheets (Línea 175 corregida)
        df_merge = pd.merge(fichajes_dia, df_emp, on='legajo', how='left')
        
        # Aquí ya podés mostrar la tabla resultante en Streamlit
        st.dataframe(df_merge)
        
    else:
        st.error("No se encontraron marcas válidas en el archivo .txt. Verifica el formato.")
