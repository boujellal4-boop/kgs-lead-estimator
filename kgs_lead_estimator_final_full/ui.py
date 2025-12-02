import streamlit as st
import pandas as pd, json, os
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="KGS Lead Estimator", layout="wide")

BASE = os.path.dirname(__file__)
st.markdown("<style>body{font-family: Inter, system-ui, Arial;}</style>", unsafe_allow_html=True)
st.title("KGS Lead Estimator")

# Load data
df = pd.read_csv(os.path.join(BASE, "clean_orders.csv"))
with open(os.path.join(BASE, "totals.json")) as f:
    totals = json.load(f)

# Dropdowns: fixed technology list
technologies = [
    "Addressable system","Conventional system","Aspirating smoke detection",
    "Wireless detection system","Software & tools","Linear heat detection",
    "Flame detection","Other specialty detection","Security solutions"
]

countries = sorted([c for c in df['country'].dropna().unique()]) if 'country' in df.columns else []
industries = sorted([c for c in df['product_category'].dropna().unique()]) if 'product_category' in df.columns else []

col1, col2 = st.columns([1,1])
with col1:
    lead_type = st.selectbox("Lead type", ["End User","Distributor","Installer","Consultant"])
with col2:
    country = st.selectbox("Country (EMEA)", countries if countries else ["All"])

if lead_type == "End User" and industries:
    industry = st.selectbox("Industry", industries)
else:
    industry = None

technology = st.selectbox("Technology interested in", technologies)
job_title = st.selectbox("Job title (optional)", ["","CEO","Owner","Director","Manager","Engineer","Technician","Other"])

st.write("---")
st.markdown("### Estimation (totals-based)")

def safe_total(dct, key):
    try:
        return float(dct.get(key, {}).get('total',0))
    except:
        return 0.0

# Get historical totals (eOrders only) for selection
tech_total = safe_total(totals.get("by_technology", {}), technology)
country_total = safe_total(totals.get("by_country", {}), country) if country and country!="All" else 0.0
industry_total = safe_total(totals.get("by_industry", {}), industry) if industry else 0.0

# Combine signals (use tech_total primarily)
selected_total = tech_total
# scale: first-500 * 4 and then adjust for offline (eOrders = 30% of business)
scaled_500_estimate = selected_total * 4
adjusted_for_offline = (scaled_500_estimate / 0.30) if selected_total>0 else 0.0

expected = adjusted_for_offline
low = expected * 0.8
high = expected * 1.2

c1,c2,c3 = st.columns(3)
c1.metric("Low (−20%)", f"${low:,.0f}")
c2.metric("Expected", f"${expected:,.0f}")
c3.metric("High (+20%)", f"${high:,.0f}")

st.markdown("#### Notes")
st.markdown("- Estimates are totals-based (sum of historical eOrders) and scaled to estimate full business (offline + online).")
st.markdown("- SKU→Technology mapping is performed by the SKU lookup worker and logged in `sku_lookup_log.csv`.")

st.write("---")
st.subheader("Visual insights")

# Pie chart: technology distribution
tech_df = pd.DataFrame([{'Technology':k,'Total':v['total']} for k,v in totals.get('by_technology', {}).items()])
if not tech_df.empty:
    fig = px.pie(tech_df, names='Technology', values='Total', title='Value distribution by Technology')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Technology totals are not available yet. Run the SKU lookup worker to populate mappings.")

# Bar chart: top countries
country_df = pd.DataFrame([{'Country':k,'Total':v['total']} for k,v in totals.get('by_country', {}).items()])
if not country_df.empty:
    fig2 = px.bar(country_df.sort_values('Total', ascending=False).head(20), x='Country', y='Total', title='Top Countries by Total Value')
    st.plotly_chart(fig2, use_container_width=True)

# Treemap: technology -> country
if 'country' in df.columns and not df.empty:
    per = df.groupby(['technology','country'])['value'].sum().reset_index().rename(columns={'technology':'tech','country':'country','value':'value'})
    if not per.empty:
        fig3 = px.treemap(per, path=['tech','country'], values='value', title='Treemap: Technology → Country → Value')
        st.plotly_chart(fig3, use_container_width=True)

st.sidebar.header("Actions & Data")
st.sidebar.write("Last updated: " + datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
st.sidebar.download_button("Download sku_lookup_log.csv", os.path.join(BASE, "sku_lookup_log.csv"))
st.sidebar.download_button("Download clean_orders.csv", os.path.join(BASE, "clean_orders.csv"))
st.sidebar.download_button("Download totals.json", os.path.join(BASE, "totals.json"))
st.sidebar.info("To populate mappings, run the SKU lookup worker (GitHub Actions workflow or locally).")