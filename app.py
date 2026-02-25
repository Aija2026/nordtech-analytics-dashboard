import streamlit as st
import pandas as pd
import plotly.express as px

# 1. KONFIGURĀCIJA
st.set_page_config(page_title="NordTech Analītikas Panelis", layout="wide")

st.title("📊 NordTech Darbības Pārskata Panelis")
st.markdown("Analītiķe: **[Tavs Vārds]**")

# 2. DATU IELĀDE
@st.cache_data
def load_data():
    df = pd.read_csv("enriched_data.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    df['Ticket_Count'] = df['Ticket_Count'].fillna(0)
    
    # Terminoloģijas tulkošana
    translations = {
        'Product Defect': 'Produkta defekts',
        'Shipping Issue': 'Piegādes problēma',
        'Refund Request': 'Atgriešanas pieprasījums',
        'No complaint': 'Nav sūdzību'
    }
    df['Issue_Category_LV'] = df['Issue_Category'].replace(translations)
    return df

df = load_data()

# 3. SIDEBAR FILTRI
st.sidebar.header("Datu atlase")

# 1. filtrs: Produkts
product_filter = st.sidebar.multiselect(
    "Izvēlieties produktus:", 
    options=sorted(df['Product_Name'].unique()), 
    default=df['Product_Name'].unique()
)

# 2. filtrs: Laika periods
min_date = df['Date'].min().date()
max_date = df['Date'].max().date()

date_range = st.sidebar.date_input(
    "Izvēlieties laika periodu:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Datu filtrēšana
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    mask = (
        df['Product_Name'].isin(product_filter) & 
        (df['Date'].dt.date >= start_date) & 
        (df['Date'].dt.date <= end_date)
    )
    filtered_df = df.loc[mask]
else:
    filtered_df = df[df['Product_Name'].isin(product_filter)]

# 4. KPI RINDA
total_rev = filtered_df['Total_Value'].sum()
total_refunds = filtered_df['Refund_Amount'].sum()
total_tickets = int(filtered_df['Ticket_Count'].sum())
return_rate = (filtered_df['Refund_Amount'] > 0).mean() * 100 if len(filtered_df) > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Kopējie ieņēmumi (Bruto)", f"{total_rev:,.2f} €")
col2.metric("Atgrieztā summa", f"{total_refunds:,.2f} €")
col3.metric("Preču atgriešanas likme", f"{return_rate:.1f}%")
col4.metric("Klientu sūdzības", total_tickets)

st.divider()

# 5. VIZUĀĻI
c1, c2 = st.columns(2)

with c1:
    # 1. Grafiks: Atgrieztās summas pa produktiem
    product_risk = filtered_df.groupby('Product_Name')['Refund_Amount'].sum().reset_index()
    fig1 = px.bar(product_risk.sort_values('Refund_Amount', ascending=False), 
                 x='Refund_Amount', y='Product_Name', orientation='h', 
                 title="Preču atgriešanas apjoms pa produktiem (€)",
                 labels={'Refund_Amount': 'Atmaksu summa (€)', 'Product_Name': 'Produkts'},
                 color='Refund_Amount', color_continuous_scale='Reds')
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    # 2. Grafiks: Sūdzību iemesli
    issue_data = filtered_df[filtered_df['Issue_Category_LV'] != 'Nav sūdzību']
    if not issue_data.empty:
        fig2 = px.pie(issue_data, names='Issue_Category_LV', 
                     title="Klientu sūdzību iemeslu sadalījums",
                     labels={'Issue_Category_LV': 'Iemesls'},
                     hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Atlasītajā periodā sūdzību nav.")

# 6. DATU TABULA
st.subheader("⚠️ Problemātisko pasūtījumu detalizēta analīze")

tabulas_df = filtered_df[
    (filtered_df['Refund_Amount'] > 0) | (filtered_df['Ticket_Count'] > 0)
].copy()

tabulas_df = tabulas_df[['Date', 'Transaction_ID', 'Product_Name', 'Total_Value', 'Refund_Amount', 'Issue_Category_LV']].rename(columns={
    'Date': 'Datums',
    'Transaction_ID': 'Darījuma ID',
    'Product_Name': 'Produkts',
    'Total_Value': 'Darījuma vērtība (€)',
    'Refund_Amount': 'Atgrieztā summa (€)',
    'Issue_Category_LV': 'Sūdzības iemesls'
})

st.dataframe(tabulas_df.sort_values(by='Atgrieztā summa (€)', ascending=False).head(20), use_container_width=True)

st.caption("Dati tiek apstrādāti reāllaikā no NordTech uzskaites sistēmas.")