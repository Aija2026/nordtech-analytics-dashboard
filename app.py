import streamlit as st
import pandas as pd
import plotly.express as px

# 1. KONFIGURĀCIJA
st.set_page_config(page_title="NordTech Analītikas Panelis", layout="wide")

# AGRESĪVS CSS LABOJUMS:
# 1. Palielinām multiselect rāmja augstumu.
# 2. Atļaujam sarakstam (dropdown) būt garākam.
# 3. Noņemam liekās atstarpes sānjoslā.
st.markdown("""
    <style> 
    .main .block-container {padding-top: 1rem;}
    
    /* Palielinām pašu multiselect rāmi, kurā dzīvo izvēlētie produkti */
    div[data-baseweb="select"] > div:first-child {
        min-height: 450px !important; 
        align-items: flex-start !important;
    }
    
    /* Padarām saraksta izvēlni garāku, kad tā tiek atvērta */
    div[data-baseweb="popover"] > div {
        max-height: 600px !important;
    }

    /* Sānjoslas platuma un atstarpju optimizācija */
    [data-testid="stSidebar"] {
        min-width: 350px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 NordTech Darbības Pārskata Panelis")
st.markdown("Analītiķe: **Aija**")

# 2. DATU IELĀDE
@st.cache_data
def load_data():
    df = pd.read_csv("enriched_data.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    df['Ticket_Count'] = df['Ticket_Count'].fillna(0)
    
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

# Datuma filtrs
min_date = df['Date'].min().date()
max_date = df['Date'].max().date()

date_range = st.sidebar.date_input(
    "1. Izvēlieties laika periodu:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

st.sidebar.markdown("---")

# Produktu izvēle - tagad ar piespiedu augstumu
st.sidebar.markdown("**2. Izvēlieties produktus:**")
product_filter = st.sidebar.multiselect(
    "Saraksts:", 
    options=sorted(df['Product_Name'].unique()), 
    default=df['Product_Name'].unique(),
    label_visibility="collapsed"
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

# 4. KPI RINDA (Prasība: vismaz 3 rādītāji)
total_rev = filtered_df['Total_Value'].sum()
total_refunds = filtered_df['Refund_Amount'].sum()
total_tickets = int(filtered_df['Ticket_Count'].sum())
return_rate = (filtered_df['Refund_Amount'] > 0).mean() * 100 if len(filtered_df) > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Kopējie ieņēmumi", f"{total_rev:,.2f} €")
col2.metric("Atgrieztā summa", f"{total_refunds:,.2f} €")
col3.metric("Atgriešanas likme", f"{return_rate:.1f}%")
col4.metric("Sūdzības", total_tickets)

st.divider()

# 5. VIZUĀĻI (Prasība: vismaz 2 interaktīvi grafiki)
c1, c2 = st.columns(2)

with c1:
    product_risk = filtered_df.groupby('Product_Name')['Refund_Amount'].sum().reset_index()
    fig1 = px.bar(product_risk.sort_values('Refund_Amount', ascending=False), 
                 x='Refund_Amount', y='Product_Name', orientation='h', 
                 title="Preču atgriešanas apjoms pa produktiem (€)",
                 labels={'Refund_Amount': 'Summa (€)', 'Product_Name': 'Produkts'},
                 color='Refund_Amount', color_continuous_scale='Reds')
    fig1.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
    st.plotly_chart(fig1, width='stretch')

with c2:
    issue_data = filtered_df[filtered_df['Issue_Category_LV'] != 'Nav sūdzību']
    if not issue_data.empty:
        fig2 = px.pie(issue_data, names='Issue_Category_LV', 
                     title="Klientu sūdzību iemesli",
                     hole=0.4)
        fig2.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
        st.plotly_chart(fig2, width='stretch')
    else:
        st.info("Sūdzību nav.")

# 6. TABULA (Prasība: Top problemātiskie gadījumi)
st.subheader("⚠️ Problemātisko pasūtījumu detalizēta analīze")
tabulas_df = filtered_df[(filtered_df['Refund_Amount'] > 0) | (filtered_df['Ticket_Count'] > 0)].copy()
tabulas_df = tabulas_df[['Date', 'Transaction_ID', 'Product_Name', 'Total_Value', 'Refund_Amount', 'Issue_Category_LV']].rename(columns={
    'Date': 'Datums', 'Transaction_ID': 'ID', 'Product_Name': 'Produkts',
    'Total_Value': 'Vērtība (€)', 'Refund_Amount': 'Atgriezts (€)', 'Issue_Category_LV': 'Iemesls'
})
st.dataframe(tabulas_df.sort_values(by='Atgriezts (€)', ascending=False).head(10), width='stretch')