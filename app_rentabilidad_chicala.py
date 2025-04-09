
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📊 Análisis de Rentabilidad - Proyecto de Obra")

# Cargar archivo de cronograma
st.sidebar.header("Carga de Archivos")
uploaded_cronograma = st.sidebar.file_uploader("📁 Cargar Cronograma (.xlsx)", type=["xlsx"])
uploaded_avance = st.sidebar.file_uploader("📁 Cargar Avance Físico (.xlsx)", type=["xlsx"])

if uploaded_cronograma:
    try:
        excel_data = pd.ExcelFile(uploaded_cronograma)
        df = excel_data.parse("Programación Chicalá")
        header_row = df.iloc[2]
        df_cleaned = df[3:].copy()
        df_cleaned.columns = header_row

        df_filtered = df_cleaned[["Codigo", "Descripción", "Inicio", "Fin", "Duración (días)", "Costo ($)"]].copy()
        df_filtered["Inicio"] = pd.to_datetime(df_filtered["Inicio"], errors='coerce')
        df_filtered["Fin"] = pd.to_datetime(df_filtered["Fin"], errors='coerce')
        df_filtered["Duración (días)"] = pd.to_numeric(df_filtered["Duración (días)"], errors='coerce')
        df_filtered["Costo ($)"] = pd.to_numeric(df_filtered["Costo ($)"], errors='coerce')
        df_filtered["Costo por día"] = df_filtered["Costo ($)"] / df_filtered["Duración (días)"]

        st.success("✅ Cronograma cargado correctamente.")
        st.dataframe(df_filtered.head())

        # Expandir a diario
        cost_per_day_data = []
        for _, row in df_filtered.iterrows():
            if pd.notnull(row["Inicio"]) and pd.notnull(row["Duración (días)"]) and pd.notnull(row["Costo por día"]):
                for day in range(int(row["Duración (días)"])):
                    date = row["Inicio"] + pd.Timedelta(days=day)
                    cost_per_day_data.append({
                        "Fecha": date,
                        "Costo Diario": row["Costo por día"]
                    })

        df_costs_daily = pd.DataFrame(cost_per_day_data)
        df_costs_daily = df_costs_daily.groupby("Fecha").sum().sort_index()
        df_costs_daily["Costo Acumulado"] = df_costs_daily["Costo Diario"].cumsum()
        df_costs_weekly = df_costs_daily.resample("W").sum()
        df_costs_weekly["Costo Acumulado"] = df_costs_weekly["Costo Diario"].cumsum()

        ingreso_total = df_filtered["Costo ($)"].sum()
        df_costs_weekly["Ingreso Acumulado"] = ingreso_total * (
            (df_costs_weekly.index - df_costs_weekly.index.min()) / 
            (df_costs_weekly.index.max() - df_costs_weekly.index.min())
        )

        if uploaded_avance:
            avance_real_df = pd.read_excel(uploaded_avance)
            avance_real_df["Fecha"] = pd.to_datetime(avance_real_df["Fecha"])
            df_comparado = df_costs_weekly.reset_index().merge(
                avance_real_df, how="left", left_on="Fecha", right_on="Fecha"
            ).set_index("Fecha")

            df_comparado["Avance Real ($)"] = df_comparado["Avance Físico (%)"] * ingreso_total / 100
            st.success("✅ Avance físico cargado correctamente.")
        else:
            df_comparado = df_costs_weekly.copy()
            df_comparado["Avance Real ($)"] = None

        # Mostrar gráfico
        st.subheader("📈 Curva de Costo vs Ingreso vs Avance Físico")

        fig, ax = plt.subplots(figsize=(14, 7))
        ax.plot(df_comparado.index, df_comparado["Costo Acumulado"], label="Costo Acumulado (COP)", marker='o')
        ax.plot(df_comparado.index, df_comparado["Ingreso Acumulado"], linestyle='--', label="Ingreso Proyectado (COP)")
        if "Avance Real ($)" in df_comparado:
            ax.plot(df_comparado.index, df_comparado["Avance Real ($)"], linestyle='-.', marker='s', label="Avance Físico Real ($)")
        ax.set_title("Costo vs Ingreso vs Avance Físico Real", fontsize=16)
        ax.set_xlabel("Fecha")
        ax.set_ylabel("COP")
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.ticklabel_format(axis='y', style='plain')
        ax.legend()
        st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
else:
    st.info("📤 Por favor, carga el cronograma del proyecto en formato Excel.")
