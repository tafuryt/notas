import streamlit as st  
import pandas as pd
from io import BytesIO
from datetime import datetime

# Configuración de la app
st.set_page_config(page_title="Organizador Flex Contable", layout="wide")
st.title("📄 Organizador Flex Contable")

# Función para formatear los datos
def formatear_flex(df):
    df_resultado = pd.DataFrame()

    # Convertir FECHA a datetime
    df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')

    # Validación de fechas inválidas
    if df['FECHA'].isna().any():
        fechas_invalidas = df[df['FECHA'].isna()]
        st.warning("⚠️ Estas fechas están mal formateadas:")
        st.dataframe(fechas_invalidas[['FECHA']])
        return None

    # Generar PERIODO desde la FECHA
    df['PERIODO'] = df['FECHA'].dt.strftime('%b-%y').str.upper()

    # Validar que todas las fechas correspondan al mismo mes y año
    meses = df['FECHA'].dt.month.unique()
    anios = df['FECHA'].dt.year.unique()

    if len(meses) > 1 or len(anios) > 1:
        st.error("❌ Las fechas contienen más de un mes o año. Asegúrate de que todo esté en el mismo periodo.")
        return None

    # Formatear campos
    df_resultado['PERIODO'] = df['FECHA'].dt.strftime('%b-%y').str.lower()
    df_resultado['FECHA'] = df['FECHA'].dt.strftime('%d/%m/%Y')
    df_resultado['COMPAÑIA'] = df['COMPAÑIA'].astype(str).str.zfill(2)
    df_resultado['CENCO'] = df['CENCO'].astype(str).str.zfill(4)
    df_resultado['CUENTA CONTABLE'] = df['CUENTA CONTABLE'].astype(str).str.zfill(10)
    df_resultado['REGIONAL'] = df['REGIONAL'].astype(str).str.zfill(2)
    df_resultado['CIUDAD'] = df['CIUDAD'].astype(str).str.zfill(5)
    df_resultado['CLIENTE'] = df['CLIENTE'].astype(str).str.zfill(9)
    df_resultado['LINEA'] = df['LINEA'].astype(str).str.zfill(4)
    df_resultado['NEGOCIO'] = df['NEGOCIO'].astype(str).str.zfill(7)
    df_resultado['VALOR'] = df['VALOR'].apply(lambda x: f"{float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    df_resultado['TERCERO'] = df['TERCERO'].astype(str).str.zfill(9)
    df_resultado['ATRIBUTO'] = df['ATRIBUTO'].str.upper()
    df_resultado['OBSERVACION'] = df['OBSERVACION'].str.upper()
    df_resultado['CONSTANTE'] = 0

    # Validar OBSERVACION
    palabras_clave = [
        "NOTA PTE FACTURACION", "PROYECTADO", "FUEROS DE SALUD", "EMBARAZADAS", "ANTICIPADO",
        "INDEMNIDADES Y PENALIDADES", "MENOR O MAYOR VLR FACT O PEND", "COSTO PENDIENTE",
        "AJUSTE ETERNO", "BENEFICIO", "CONTINGENCIA", "EJECUCIONES", "PROVISION GASTO",
        "INDEMNIZACION", "RECLASIFICACION"
    ]
    obs_invalidas = df_resultado[~df_resultado['OBSERVACION'].isin(palabras_clave)]
    if not obs_invalidas.empty:
        st.warning("⚠️ Estas observaciones no coinciden con las palabras clave válidas:")
        st.dataframe(obs_invalidas[['OBSERVACION']])

    # Validación de #N/D
    if (df_resultado == '#N/D').any().any():
        st.warning("⚠️ Se encontraron valores '#N/D' en el archivo.")

    return df_resultado

# Subida del archivo sin encabezados, separado por ;
archivo = st.file_uploader("📂 Sube tu archivo CSV (sin encabezados, separados por punto y coma)", type=["csv"])

if archivo:
    columnas_esperadas = [
        "PERIODO", "FECHA", "COMPAÑIA", "CENCO", "CUENTA CONTABLE", "REGIONAL",
        "CIUDAD", "CLIENTE", "LINEA", "NEGOCIO", "VALOR", "TERCERO",
        "ATRIBUTO", "OBSERVACION", "CONSTANTE"
    ]

    contenido = archivo.read().decode("utf-8").replace(",", ";")
    df_raw = pd.read_csv(BytesIO(contenido.encode()), header=None, sep=";", dtype=str)

    if df_raw.shape[1] != len(columnas_esperadas):
        st.error(f"❌ El archivo debe tener exactamente {len(columnas_esperadas)} columnas separadas por ';'. Se encontraron {df_raw.shape[1]}.")
    else:
        df_raw.columns = columnas_esperadas
        df_raw = df_raw.fillna('')

        st.subheader("🔎 Previsualización de los datos cargados:")
        st.dataframe(df_raw.head(), use_container_width=True)

        if st.button("✅ Generar archivo Flex Contable"):
            df_flex = formatear_flex(df_raw)

            if df_flex is not None:
                st.success("✅ Archivo formateado correctamente.")
                st.dataframe(df_flex.head(), use_container_width=True)

                # Generar nombre del archivo según el atributo
                atributos_unicos = df_flex['ATRIBUTO'].unique()
                periodo_final = df_flex['PERIODO'].iloc[0].upper()

                if len(atributos_unicos) == 1:
                    nombre_archivo = f"{atributos_unicos[0].upper()}.csv"
                else:
                    nombre_archivo = f"NOTAS CONSOLIDADAS {periodo_final}.csv"

                # Exportar
                buffer = BytesIO()
                df_flex.to_csv(buffer, index=False, sep=";", header=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 Descargar archivo formateado (CSV sin encabezados)",
                    data=buffer.getvalue(),
                    file_name=nombre_archivo,
                    mime="text/csv"
                )

              