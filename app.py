import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Konfigurasi halaman
st.set_page_config(
    page_title="Maintenance Dashboard",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=600)  # Refresh setiap 10 menit
def load_data():
    # Ganti dengan SHEET_ID Anda
    SHEET_URL = "https://docs.google.com/spreadsheets/d/14cfkZrFmVZKyOH5qbAmNphYyMDa974GcQBMoZgx2Yhc/edit?usp=sharing"
    SHEET_ID = "14cfkZrFmVZKyOH5qbAmNphYyMDa974GcQBMoZgx2Yhc"
    
    # Load langsung dari Google Sheets (public link)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"
    df = pd.read_csv(url)
    
    # Data cleaning
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Biaya'] = pd.to_numeric(df['Biaya'].str.replace('Rp ', '').str.replace('.', '').str.replace(',', ''), errors='coerce')
    df['Bulan'] = df['Timestamp'].dt.to_period('M').astype(str)
    df['Hari'] = df['Timestamp'].dt.day_name()
    
    return df

# Load data
df = load_data()
st.sidebar.success(f"✅ Data loaded: {len(df):,} records")

# Header
st.title("🔧 Dashboard Maintenance Real-time")
st.markdown("---")

# Sidebar Filters
st.sidebar.header("🔍 Filter Data")
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.sidebar.date_input("Dari Tanggal", df['Timestamp'].min().date())
with col2:
    end_date = st.sidebar.date_input("Sampai Tanggal", df['Timestamp'].max().date())

asset_filter = st.sidebar.multiselect("Asset", options=df['Asset'].unique(), default=df['Asset'].unique())
jenis_filter = st.sidebar.multiselect("Jenis Maintenance", options=df['Jenis_Maintenance'].unique(), default=df['Jenis_Maintenance'].unique())
status_filter = st.sidebar.multiselect("Status", options=df['Status'].unique(), default=df['Status'].unique())

# Filter dataframe
df_filtered = df[
    (df['Timestamp'].dt.date >= start_date) & 
    (df['Timestamp'].dt.date <= end_date) &
    (df['Asset'].isin(asset_filter)) &
    (df['Jenis_Maintenance'].isin(jenis_filter)) &
    (df['Status'].isin(status_filter))
]

# KPI Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_wo = len(df_filtered)
    st.metric("Total Work Order", f"{total_wo:,}", 
              delta=f"+{total_wo - len(df[(df['Timestamp'].dt.month == df_filtered['Timestamp'].dt.month.max()) & (df['Timestamp'].dt.year == df_filtered['Timestamp'].dt.year.max())]):+d}")

with col2:
    selesai_pct = len(df_filtered[df_filtered['Status'] == 'Selesai']) / len(df_filtered) * 100 if len(df_filtered) > 0 else 0
    st.metric("Completion Rate", f"{selesai_pct:.1f}%", delta="+2.3%")

with col3:
    total_biaya = df_filtered['Biaya'].sum()
    st.metric("Total Biaya", f"Rp {total_biaya:,.0f}", delta="+Rp 2.5M")

with col4:
    avg_biaya = df_filtered['Biaya'].mean()
    st.metric("Rata-rata Biaya", f"Rp {avg_biaya:,.0f}", delta="+Rp 45K")

st.markdown("---")

# Charts Row 1
col1, col2 = st.columns([2.5, 2])
with col1:
    st.subheader("📈 Trend Maintenance")
    trend_data = df_filtered.groupby(df_filtered['Timestamp'].dt.to_period('D')).size().reset_index(name='Jumlah')
    trend_data['Tanggal'] = trend_data['Timestamp'].astype(str)
    fig_trend = px.line(trend_data, x='Tanggal', y='Jumlah', 
                       title="Daily Work Order Trend",
                       markers=True)
    fig_trend.update_layout(xaxis_title="Tanggal", yaxis_title="Jumlah WO")
    st.plotly_chart(fig_trend, use_container_width=True)

with col2:
    st.subheader("🥧 Jenis Maintenance")
    pie_data = df_filtered['Jenis_Maintenance'].value_counts()
    fig_pie = px.pie(values=pie_data.values, names=pie_data.index,
                    title="Distribusi Jenis Maintenance",
                    color_discrete_sequence=px.colors.qualitative.Set3)
    st.plotly_chart(fig_pie, use_container_width=True)

# Charts Row 2
col1, col2 = st.columns([2, 2.5])
with col1:
    st.subheader("📊 Status Distribution")
    status_data = df_filtered['Status'].value_counts()
    fig_status = go.Figure(data=[
        go.Pie(labels=status_data.index, values=status_data.values, hole=0.4)
    ])
    fig_status.update_layout(title="Status Work Order", 
                           uniformtext_minsize=12, uniformtext_mode='hide')
    st.plotly_chart(fig_status, use_container_width=True)

with col2:
    st.subheader("🏆 Top 10 Asset")
    top_asset = df_filtered['Asset'].value_counts().head(10)
    fig_asset = px.bar(x=top_asset.values, y=top_asset.index, 
                      orientation='h',
                      title="Asset Paling Sering Maintenance",
                      color=top_asset.values,
                      color_continuous_scale='Viridis')
    fig_asset.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_asset, use_container_width=True)

# Detail Table
st.markdown("---")
st.subheader("📋 Detail Work Order")
st.dataframe(
    df_filtered[['Timestamp', 'Asset', 'Jenis_Maintenance', 'Status', 'Biaya']].sort_values('Timestamp', ascending=False),
    column_config={
        "Biaya": st.column_config.NumberColumn(
            "Biaya",
            format="Rp ₦.0f",
            width="medium"
        ),
        "Timestamp": st.column_config.DateColumn(
            "Tanggal",
            format="DD/MM/YYYY HH:mm",
            width="medium"
        )
    },
    use_container_width=True,
    height=400
)

# Footer
st.markdown("---")
st.markdown("👨‍💼 **Last Updated:** " + datetime.now().strftime("%d %B %Y %H:%M"))
st.markdown("🔗 **Data Source:** [Google Sheets](https://docs.google.com/spreadsheets/d/14cfkZrFmVZKyOH5qbAmNphYyMDa974GcQBMoZgx2Yhc)")
