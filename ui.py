import streamlit as st
import os, json, pandas as pd
from math import ceil

BASE = os.path.dirname(__file__)
st.set_page_config(layout="wide", page_title="B2B Fire Detection Lead Estimator (Streamlit-only)")

st.title("B2B Fire Detection Lead Estimator — (Streamlit-only deployment)")
st.markdown("This version runs entirely in Streamlit Cloud using the precomputed `averages.json` and `clean_orders.csv`. No backend required.")

# Load averages and clean data
with open(os.path.join(BASE, "averages.json")) as f:
    A = json.load(f)

try:
    df = pd.read_csv(os.path.join(BASE, "clean_orders.csv"))
except Exception:
    df = pd.DataFrame()

# Sidebar inputs
st.sidebar.header("Lead input")
lead_type = st.sidebar.selectbox("Lead type", options=["end user","distributor","installer","consultant"])
country = st.sidebar.text_input("Country (EMEA)")
industry = st.sidebar.text_input("Industry (if end user)")
technology = st.sidebar.selectbox("Technology interested in", options=sorted(list(A.get("by_technology", {}).keys())))
job_title = st.sidebar.text_input("Job title (optional)")

st.sidebar.header("Tunable multipliers (live)")
lead_mult_end_user = st.sidebar.slider("End user multiplier", 0.5, 1.5, 1.0, 0.05)
lead_mult_distributor = st.sidebar.slider("Distributor multiplier", 0.1, 1.5, 0.6, 0.05)
lead_mult_installer = st.sidebar.slider("Installer multiplier", 0.1, 1.5, 0.5, 0.05)
lead_mult_consultant = st.sidebar.slider("Consultant multiplier", 0.1, 1.5, 0.4, 0.05)

st.sidebar.markdown("**Job title multipliers (keyword match)**")
jt_ceo = st.sidebar.slider("C-Level / Owner multiplier", 1.0, 2.0, 1.3, 0.05)
jt_director = st.sidebar.slider("Director / Head multiplier", 0.8, 1.5, 1.15, 0.05)
jt_manager = st.sidebar.slider("Manager multiplier", 0.8, 1.4, 1.1, 0.05)
jt_engineer = st.sidebar.slider("Engineer multiplier", 0.5, 1.2, 0.95, 0.05)

lead_multiplier_map = {
    "end user": lead_mult_end_user,
    "distributor": lead_mult_distributor,
    "installer": lead_mult_installer,
    "consultant": lead_mult_consultant
}

def job_multiplier(title: str):
    if not title or not isinstance(title, str):
        return 1.0, "none"
    t = title.lower()
    if any(k in t for k in ["ceo","cfo","owner","founder"]):
        return jt_ceo, "c-level/owner"
    if any(k in t for k in ["director","head"]):
        return jt_director, "director/head"
    if "manager" in t:
        return jt_manager, "manager"
    if "engineer" in t or "technician" in t:
        return jt_engineer, "engineer/technician"
    return 1.0, "default"

# Estimate when button pressed
if st.button("Estimate deal value"):
    tech_avg = A.get("by_technology", {}).get(technology, A.get("overall_average", 0))
    country_avg = A.get("by_country", {}).get(country.strip(), A.get("overall_average", 0))
    region_avg = A.get("by_region", {}).get(country.strip(), A.get("overall_average", 0))
    industry_avg = A.get("by_industry", {}).get(industry.strip(), A.get("overall_average", 0))
    lead_avg = A.get("by_lead_type", {}).get(lead_type.strip(), A.get("overall_average", 0))

    parts = [p for p in [tech_avg, country_avg, region_avg, industry_avg, lead_avg] if p is not None]
    base = sum(parts) / max(1, len(parts))

    lm = lead_multiplier_map.get(lead_type, 1.0)
    jm, jm_label = job_multiplier(job_title)

    expected = base * lm * jm
    low = expected * 0.8
    high = expected * 1.2

    # Show metrics
    c1, c2, c3 = st.columns([2,1,1])
    c1.metric("Expected deal value", f"{expected:,.2f}")
    c2.metric("Low (−20%)", f"{low:,.2f}")
    c3.metric("High (+20%)", f"{high:,.2f}")

    st.subheader("Estimation components (explainable)")
    st.write({
        "technology_avg": tech_avg,
        "country_avg": country_avg,
        "region_avg": region_avg,
        "industry_avg": industry_avg,
        "lead_avg": lead_avg,
        "base_mean": round(base,2),
        "lead_multiplier": lm,
        "job_multiplier": jm,
        "job_multiplier_label": jm_label
    })

    st.subheader("KPIs & quick insights")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Top technologies by average deal value")
        tech_df = pd.DataFrame.from_dict(A.get("by_technology", {}), orient='index', columns=['avg']).sort_values('avg', ascending=False)
        st.dataframe(tech_df.head(20))
    with col2:
        st.write("Top countries by average deal value")
        country_df = pd.DataFrame.from_dict(A.get("by_country", {}), orient='index', columns=['avg']).sort_values('avg', ascending=False)
        st.dataframe(country_df.head(20))

    st.write("Region averages")
    region_df = pd.DataFrame.from_dict(A.get("by_region", {}), orient='index', columns=['avg']).sort_values('avg', ascending=False)
    st.dataframe(region_df)

    if not df.empty:
        st.write("Sample of cleaned orders used (first 100 rows)")
        st.dataframe(df.head(100))

    st.info("This app runs fully in Streamlit (no external backend). Tweak multipliers in the sidebar to tune estimates live.")

else:
    st.info("Fill the inputs in the sidebar and press **Estimate deal value**.")