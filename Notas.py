import streamlit as st 
import pandas as pd
from io import BytesIO
from datetime import datetime
import csv

# Configuración de la app
st.set_page_config(page_title="Organizador Flex Contable", layout="wide")
st.title("📄 Organizador Flex Contable")

# Función para formatear los datos
def formatear_flex(df):
    df_resultado = pd.DataFrame()

    df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
    if df['FECHA'].isna().any():
        fechas_invalidas = df[df['FECHA'].isna()]
        st.warning("⚠️ Estas fechas están mal formateadas:")
        st.dataframe(fechas_invalidas[['FECHA']])
        return None

    df['PERIODO'] = df['FECHA'].dt.strftime('%b-%y').str.upper()
    meses = df['FECHA'].dt.month.unique()
    anios = df['FECHA'].dt.year.unique()
    if len(meses) > 1 or len(anios) > 1:
        st.error("❌ Las fechas contienen más de un mes o año. Asegúrate de que todo esté en el mismo periodo.")
        return None

    df_resultado['PERIODO'] = df['FECHA'].dt.strftime('%b-%y').str.lower()
    df_resultado['FECHA']  = df['FECHA'].apply(lambda x: f"{x.day}/{x.strftime('%m/%Y')}")
    df_resultado['COMPAÑIA'] = df['COMPAÑIA'].astype(str).str.zfill(2)
    df_resultado['CENCO'] = df['CENCO'].astype(str).str.zfill(4)
    df_resultado['CUENTA CONTABLE'] = df['CUENTA CONTABLE'].astype(str).str.zfill(10)
    df_resultado['REGIONAL'] = df['REGIONAL'].astype(str).str.zfill(2)
    df_resultado['CIUDAD'] = df['CIUDAD'].astype(str).str.zfill(5)
    df_resultado['CLIENTE'] = df['CLIENTE'].astype(str)
    df_resultado['LINEA'] = df['LINEA'].astype(str).str.zfill(4)
    df_resultado['NEGOCIO'] = df['NEGOCIO'].astype(str).str.zfill(7)
    
    # Formatear VALOR correctamente
    df_resultado['VALOR'] = df['VALOR'].str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
    df_resultado['VALOR'] = df_resultado['VALOR'].apply(
        lambda x: str(int(x)) if x.is_integer() else str(f"{x:.2f}").replace(".", ",")
    )

    df_resultado['TERCERO'] = df['TERCERO'].astype(str)
    df_resultado['ATRIBUTO'] = df['ATRIBUTO'].str.upper()
    df_resultado['OBSERVACION'] = df['OBSERVACION'].str.upper()
    df_resultado['CONSTANTE'] = 0

    palabras_clave = [
        "NOTA PTE FACTURACION", "PROYECTADO", "FUEROS DE SALUD", "EMBARAZADAS", "ANTICIPADO",
        "INDEMNIDAD Y PENALIDADES", "MENOR O MAYOR VLR FACT O PEND", "COSTO PENDIENTE",
        "AJUSTE ETERNO", "BENEFICIO", "CONTINGENCIA", "EJECUCIONES", "PROVISION GASTO",
        "INDEMNIZACION", "RECLASIFICACION"
    ]
    obs_invalidas = df_resultado[~df_resultado['OBSERVACION'].isin(palabras_clave)]
    if not obs_invalidas.empty:
        st.warning("⚠️ Estas observaciones no coinciden con las palabras clave válidas:")
        st.dataframe(obs_invalidas[['OBSERVACION']])

    if (df_resultado == '#N/D').any().any():
        st.warning("⚠️ Se encontraron valores '#N/D' en el archivo.")

    return df_resultado

# Subida del archivo CSV separado por ;
archivo = st.file_uploader("📂 Sube tu archivo CSV (sin encabezados, separados por punto y coma)", type=["csv"])

if archivo:
    columnas_esperadas = [
        "PERIODO", "FECHA", "COMPAÑIA", "CENCO", "CUENTA CONTABLE", "REGIONAL",
        "CIUDAD", "CLIENTE", "LINEA", "NEGOCIO", "VALOR", "TERCERO",
        "ATRIBUTO", "OBSERVACION", "CONSTANTE"
    ]

    archivo.seek(0)  # Asegura que el archivo se lea desde el inicio

    try:
        df_raw = pd.read_csv(
            archivo,
            header=None,
            sep=";",
            dtype=str,
            quoting=csv.QUOTE_NONE,
            on_bad_lines='warn',
            encoding="latin-1"
        )

    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {e}")
        st.stop()

    if df_raw.shape[1] != len(columnas_esperadas):
        st.error(f"❌ El archivo debe tener exactamente {len(columnas_esperadas)} columnas separadas por ';'. Se encontraron {df_raw.shape[1]}.")
    else:
        df_raw.columns = columnas_esperadas
        df_raw = df_raw.fillna('')

        st.subheader("🔎 Previsualización de los datos cargados:")
        st.dataframe(df_raw.head(100), use_container_width=True)

        # Calcular total de VALOR
        try:
            total_valor = df_raw["VALOR"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
            total_valor = total_valor.astype(float).sum()
            total_formateado = f"{total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            st.info(f"💰 Total VALOR: {total_formateado}")
        except Exception:
            st.warning("⚠️ No se pudo calcular el total de la columna VALOR. Verifica que todos los valores sean numéricos.")

        if st.button("✅ Generar archivo Flex Contable"):
            df_flex = formatear_flex(df_raw)

            if df_flex is not None:
                st.success("✅ Archivo formateado correctamente.")
                st.dataframe(df_flex.head(100), use_container_width=True)

                atributos_unicos = df_flex['ATRIBUTO'].unique()
                periodo_final = df_flex['PERIODO'].iloc[0].upper()

                if len(atributos_unicos) == 1:
                    nombre_archivo = f"{atributos_unicos[0].upper()}.csv"
                else:
                    nombre_archivo = f"NOTAS CONSOLIDADAS {periodo_final}.csv"

                buffer = BytesIO()
                df_flex.to_csv(buffer, index=False, sep=";", header=False, encoding="latin-1")
                st.download_button(
                    label="📥 Descargar archivo formateado (CSV sin encabezados)",
                    data=buffer.getvalue(),
                    file_name=nombre_archivo,
                    mime="text/csv"
                )


