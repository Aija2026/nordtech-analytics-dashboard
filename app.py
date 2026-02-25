import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="NordTech Dashboard", layout="wide")

st.title("📊 NordTech Biznesa Veselības Panelis")
st.markdown("Analītiķe: **Aija**")

# Datu ielāde
@st.cache_data
def load_data():
    df = pd.read_csv("enriched_data.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    return df

df = load_data()

# Sidebar filtri
st.sidebar.header("Filtri")
product_filter = st.sidebar.multiselect(
    "Izvēlies produktu:", 
    options=df['Product_Name'].unique(), 
    default=df['Product_Name'].unique()
)

# KPI aprēķini
filtered_df = df[df['Product_Name'].isin(product_filter)]
total_rev = filtered_df['Total_Value'].sum()
net_rev = filtered_df['Net_Revenue'].sum()
return_rate = (filtered_df['Refund_Amount'] > 0).mean() * 100 if len(filtered_df) > 0 else 0

# KPI Rinda
col1, col2, col3 = st.columns(3)
col1.metric("Bruto ieņēmumi", f"{total_rev:,.2f} €")
col2.metric("Neto ieņēmumi", f"{net_rev:,.2f} €")
col3.metric("Atgriešanas likme", f"{return_rate:.1f}%")

st.divider()

# Grafiks - Atgriezumi pa produktiem
product_risk = filtered_df.groupby('Product_Name')['Refund_Amount'].sum().reset_index()
fig = px.bar(product_risk.sort_values('Refund_Amount', ascending=False), 
             x='Refund_Amount', y='Product_Name', orientation='h', 
             title="Atgriezumu summa pa produktiem", color='Refund_Amount',
             color_continuous_scale='Reds')
st.plotly_chart(fig, use_container_width=True)

st.subheader("Problemātiskie darījumi (Atgriezumi)")
st.dataframe(filtered_df[filtered_df['Refund_Amount'] > 0].sort_values('Refund_Amount', ascending=False))