import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# Configuração inicial da página
st.set_page_config(page_title="Dashboard UFV Pôr do Sol", layout="wide")

# Função para carregar e tratar os dados
@st.cache_data
def load_data():
    file_path = "Dados Brutos - UFV PDS.xlsx"
    df_raw = pd.read_excel(file_path, sheet_name=0)

    # Extrair e tratar dados de geração
    df_gen = df_raw.iloc[2:, 1:11].copy()
    cols = ['Date'] + [f'Inversor_{i}' for i in range(1, 9)] + ['Generation_Total']
    df_gen.columns = cols
    df_gen['Date'] = pd.to_datetime(df_gen['Date'])
    for col in cols[1:]:
        df_gen[col] = pd.to_numeric(df_gen[col], errors='coerce')

    # Extrair e tratar dados de irradiação
    df_irr = df_raw.iloc[2:, [12, 13]].copy()
    df_irr.columns = ['Date', 'Irradiation']
    df_irr['Date'] = pd.to_datetime(df_irr['Date'])
    df_irr['Irradiation'] = pd.to_numeric(df_irr['Irradiation'], errors='coerce')

    # Mesclar e limpar
    df = pd.merge(df_gen, df_irr, on='Date', how='inner')
    df = df.dropna()
    df['Month_Year'] = df['Date'].dt.to_period('M').astype(str)
    
    return df

# Carregamento dos dados
try:
    df = load_data()
except Exception as e:
    st.error("Erro ao carregar o arquivo 'Dados Brutos - UFV PDS.xlsx'. Verifique se o arquivo está no mesmo diretório.")
    st.stop()

# --- BARRA LATERAL (Filtros) ---
st.sidebar.header("Filtros")
min_date = df['Date'].min().date()
max_date = df['Date'].max().date()

start_date, end_date = st.sidebar.date_input(
    "Selecione o Período",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Aplicar filtro de data
mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
df_filtered = df.loc[mask]

# --- CABEÇALHO ---
st.title("📊 Dashboard Operacional - UFV Pôr do Sol")
st.markdown("Análise de Geração de Energia e Irradiação")
st.divider()

# --- MÉTRICAS GERAIS ---
col1, col2, col3, col4 = st.columns(4)

total_gerado = df_filtered['Generation_Total'].sum()
media_diaria_ger = df_filtered['Generation_Total'].mean()
media_diaria_irr = df_filtered['Irradiation'].mean()
rendimento = total_gerado / df_filtered['Irradiation'].sum() if df_filtered['Irradiation'].sum() > 0 else 0

col1.metric("Geração Total (kWh)", f"{total_gerado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col2.metric("Média Diária de Geração (kWh)", f"{media_diaria_ger:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("Média Diária de Irradiação (kWh/m²)", f"{media_diaria_irr:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col4.metric("Índice Base de Geração (kWh / kWh/m²)", f"{rendimento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.divider()

# --- GRÁFICOS ---
colA, colB = st.columns(2)

# 1. Geração vs Irradiação ao Longo do Tempo (Eixos Duplos)
with colA:
    st.subheader("Geração x Irradiação (Diária)")
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(
        go.Scatter(x=df_filtered['Date'], y=df_filtered['Generation_Total'], name="Geração (kWh)", marker_color="royalblue"),
        secondary_y=False,
    )
    fig1.add_trace(
        go.Scatter(x=df_filtered['Date'], y=df_filtered['Irradiation'], name="Irradiação (kWh/m²)", marker_color="darkorange", opacity=0.7),
        secondary_y=True,
    )
    fig1.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0), hovermode="x unified")
    fig1.update_yaxes(title_text="Geração (kWh)", secondary_y=False)
    fig1.update_yaxes(title_text="Irradiação (kWh/m²)", secondary_y=True)
    st.plotly_chart(fig1, use_container_width=True)

# 2. Desempenho por Inversor
with colB:
    st.subheader("Desempenho Acumulado por Inversor")
    inv_cols = [f'Inversor_{i}' for i in range(1, 9)]
    inv_sums = df_filtered[inv_cols].sum().sort_values()
    
    fig2 = px.bar(
        x=inv_sums.index, 
        y=inv_sums.values, 
        labels={'x': 'Inversores', 'y': 'Geração Acumulada (kWh)'},
        color_discrete_sequence=['mediumseagreen']
    )
    fig2.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig2, use_container_width=True)

colC, colD = st.columns(2)

# 3. Geração Mensal Acumulada
with colC:
    st.subheader("Geração Mensal")
    monthly_gen = df_filtered.groupby('Month_Year')['Generation_Total'].sum().reset_index()
    
    fig3 = px.bar(
        monthly_gen, 
        x='Month_Year', 
        y='Generation_Total',
        labels={'Month_Year': 'Mês', 'Generation_Total': 'Geração (kWh)'},
        color_discrete_sequence=['purple']
    )
    fig3.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
    fig3.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
    st.plotly_chart(fig3, use_container_width=True)

# 4. Gráfico de Dispersão (Irradiação vs Geração)
with colD:
    st.subheader("Relação: Irradiação vs Geração")
    fig4 = px.scatter(
        df_filtered, 
        x='Irradiation', 
        y='Generation_Total', 
        trendline="ols",
        trendline_color_override="red",
        labels={'Irradiation': 'Irradiação Medida (kWh/m²)', 'Generation_Total': 'Geração Total (kWh)'},
        color_discrete_sequence=['crimson'],
        opacity=0.6
    )
    fig4.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig4, use_container_width=True)

# --- VISUALIZAÇÃO DOS DADOS BRUTOS ---
st.divider()
with st.expander("Visualizar Tabela de Dados"):
    st.dataframe(df_filtered.drop(columns=['Month_Year']).sort_values('Date', ascending=False), use_container_width=True)
