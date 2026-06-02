import streamlit as st
import pandas as pd
import datetime

# --- CONFIGURACIÓN ---
# REEMPLAZA ESTO POR TU LINK DE GOOGLE SHEETS
URL_SHEETS = "TU_URL_AQUÍ"

st.set_page_config(page_title="Gestión de Horas - Café 32", layout="wide")
st.title("⏱️ Calculadora de Horas - Café 32")

# Función para cargar empleados desde Sheets
@st.cache_data(ttl=60)
def cargar_empleados(url):
    try:
        # Convertimos el link de edición a link de CSV
        if "/d/" in url:
            sheet_id = url.split("/d/")[1].split("/")[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
            df = pd.read_csv(csv_url)
            # Aseguramos que las columnas sean legibles
            df.columns = [c.lower().strip() for c in df.columns]
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error cargando Sheets: {e}")
        return pd.DataFrame()

# Función para procesar el TXT del reloj
def procesar_txt(archivo):
    contenido = archivo.getvalue().decode("utf-8")
    data = []
    for linea in contenido.splitlines():
        partes = linea.split()
        if len(partes) >= 3:
            try:
                # Asume estructura: Legajo (col 0), Fecha (col -2), Hora (col -1)
                legajo = int(partes[0])
                fecha_str = partes[-2]
                hora_str = partes[-1]
                fecha = pd.to_datetime(fecha_str)
                hora = pd.to_datetime(f"{fecha_str} {hora_str}")
                data.append({'legajo': legajo, 'fecha': fecha, 'hora': hora})
            except:
                continue
    return pd.DataFrame(data)

# --- LÓGICA PRINCIPAL ---
df_empleados = cargar_empleados(URL_SHEETS)

uploaded_file = st.file_uploader("Subir archivo .txt del reloj", type=["txt"])

if uploaded_file:
    df_fichajes = procesar_txt(uploaded_file)
    
    if not df_fichajes.empty:
        # Cálculo: Agrupamos por legajo y fecha, sacamos min (entrada) y max (salida)
        df_agrupado = df_fichajes.groupby(['legajo', 'fecha'])['hora'].agg(['min', 'max']).reset_index()
        df_agrupado['horas_totales'] = (df_agrupado['max'] - df_agrupado['min']).dt.total_seconds() / 3600
        
        # Unimos con los nombres de los empleados (Sheets)
        # Si 'legajo' no coincide, igual mantiene los fichajes
        df_final = pd.merge(df_agrupado, df_empleados, on='legajo', how='left')
        
        st.subheader("Reporte de Asistencia")
        
        # Filtro de fechas
        col1, col2 = st.columns(2)
        start_date = col1.date_input("Desde", value=df_fichajes['fecha'].min().date())
        end_date = col2.date_input("Hasta", value=df_fichajes['fecha'].max().date())
        
        # Filtrado
        df_final['fecha'] = pd.to_datetime(df_final['fecha'])
        mask = (df_final['fecha'].dt.date >= start_date) & (df_final['fecha'].dt.date <= end_date)
        df_filtrado = df_final[mask]
        
        # Visualización Detallada
        st.dataframe(df_filtrado[['legajo', 'nombre', 'fecha', 'min', 'max', 'horas_totales']], use_container_width=True)
        
        # Resumen Acumulado
        st.subheader("Resumen Total de Horas por Empleado")
        resumen = df_filtrado.groupby(['legajo', 'nombre'])['horas_totales'].sum().reset_index()
        st.dataframe(resumen, use_container_width=True)
    else:
        st.error("No se detectaron datos válidos en el archivo TXT.")
