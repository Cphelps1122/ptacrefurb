import streamlit as st
import pandas as pd
import requests
from datetime import date
import plotly.express as px

st.set_page_config(page_title="PTAC Refurb Marketing OS", page_icon="📈", layout="wide")
BRAND_RED = "#9C0100"
CHARCOAL = "#343434"
SHEETS = ["2 Day 0 Baseline","3 Weekly KPI Tracker","4 Lead CRM","5 Opportunity Pipeline","6 Content Calendar","7 Content Performance","8 Outreach Tracker","9 Website Roadmap","10 Revenue Attribution","11 Monthly Report"]

def css():
    st.markdown(f"""
    <style>
    .hero {{border:1px solid #ddd;border-radius:14px;padding:22px 26px;margin-bottom:18px;background:linear-gradient(135deg,#fff 0%,#fff 72%,{CHARCOAL} 72%,{BRAND_RED} 100%);}}
    .hero h1 {{margin:0;color:{CHARCOAL};font-size:42px;font-weight:800;}}
    .hero p {{margin:6px 0 0;color:{BRAND_RED};font-weight:800;letter-spacing:1.5px;}}
    .block-title {{background:linear-gradient(90deg,{BRAND_RED},{CHARCOAL});color:white;border-radius:8px;padding:8px 12px;font-weight:800;margin:12px 0;}}
    div[data-testid="stMetric"] {{background:white;border:1px solid #e3e3e3;border-radius:12px;padding:15px;box-shadow:0 2px 8px rgba(0,0,0,.04);}}
    </style>
    """, unsafe_allow_html=True)

def header():
    st.markdown("""<div class="hero"><h1>PTAC Refurb Marketing OS</h1><p>MARKETING. LEADS. PIPELINE. REVENUE. | Managed by CP</p></div>""", unsafe_allow_html=True)

def get_config():
    url = st.secrets.get("APPS_SCRIPT_URL", "")
    token = st.secrets.get("APPS_SCRIPT_TOKEN", "")
    if not url or not token:
        st.error("Missing Streamlit secrets: APPS_SCRIPT_URL and/or APPS_SCRIPT_TOKEN.")
        st.stop()
    return url, token

@st.cache_data(ttl=30, show_spinner=False)
def read_sheet(sheet_name):
    url, token = get_config()
    r = requests.get(url, params={"action": "read", "sheet": sheet_name, "token": token}, timeout=20)
    data = r.json()
    if data.get("status") != "success":
        st.error(f"Apps Script read error: {data.get('message')}")
        return pd.DataFrame()
    return pd.DataFrame(data.get("rows", []))

def append_row(sheet_name, row):
    url, token = get_config()
    r = requests.post(url, json={"sheet": sheet_name, "row": row, "token": token}, timeout=20)
    data = r.json()
    if data.get("status") == "success":
        st.cache_data.clear()
        return True, "Saved."
    return False, data.get("message", "Unknown error.")

def to_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)

def money(v):
    try: return f"${float(v):,.0f}"
    except: return "$0"

def dashboard():
    header()
    leads = read_sheet("4 Lead CRM")
    pipe = read_sheet("5 Opportunity Pipeline")
    content = read_sheet("7 Content Performance")
    revenue = read_sheet("10 Revenue Attribution")
    website = read_sheet("9 Website Roadmap")
    total_leads = len(leads)
    quote_requests = int((leads.get("Status", pd.Series(dtype=str)).astype(str).str.lower() == "quote requested").sum()) if not leads.empty else 0
    quotes_sent = int((leads.get("Status", pd.Series(dtype=str)).astype(str).str.lower() == "quote sent").sum()) if not leads.empty else 0
    deals_won = int((leads.get("Status", pd.Series(dtype=str)).astype(str).str.lower() == "won").sum()) if not leads.empty else 0
    pipe_value = to_num(pipe.get("Pipeline Value", pd.Series(dtype=float))).sum() if not pipe.empty else 0
    closed_rev = to_num(revenue.get("Closed Revenue", pd.Series(dtype=float))).sum() if not revenue.empty else 0
    impressions = to_num(content.get("Impressions", pd.Series(dtype=float))).sum() if not content.empty else 0
    clicks = to_num(content.get("Clicks", pd.Series(dtype=float))).sum() if not content.empty else 0

    st.markdown('<div class="block-title">Executive Dashboard</div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Leads", total_leads)
    c2.metric("Quote Requests", quote_requests)
    c3.metric("Quotes Sent", quotes_sent)
    c4.metric("Pipeline Value", money(pipe_value))
    c5,c6,c7,c8 = st.columns(4)
    c5.metric("Closed Revenue", money(closed_rev))
    c6.metric("Deals Won", deals_won)
    c7.metric("Content Impressions", f"{impressions:,.0f}")
    c8.metric("Content Clicks", f"{clicks:,.0f}")

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="block-title">Marketing Funnel</div>', unsafe_allow_html=True)
        funnel = pd.DataFrame({"Stage":["Impressions","Clicks","New Leads","Quote Requests","Quotes Sent","Deals Won"],"Value":[impressions,clicks,total_leads,quote_requests,quotes_sent,deals_won]})
        st.dataframe(funnel, use_container_width=True, hide_index=True)
    with right:
        st.markdown('<div class="block-title">Lead Sources</div>', unsafe_allow_html=True)
        if not leads.empty and "Source" in leads:
            src = leads.groupby("Source").size().reset_index(name="Leads")
            if not src.empty: st.plotly_chart(px.pie(src, names="Source", values="Leads", hole=.45), use_container_width=True)
            else: st.info("No lead source data yet.")
        else: st.info("No leads yet.")

    st.markdown('<div class="block-title">Top Content</div>', unsafe_allow_html=True)
    st.dataframe(content.head(8) if not content.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
    st.markdown('<div class="block-title">Priority Website Tasks</div>', unsafe_allow_html=True)
    st.dataframe(website.head(8) if not website.empty else pd.DataFrame(), use_container_width=True, hide_index=True)

def add_lead():
    header()
    st.subheader("Add Lead")
    with st.form("lead", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            d = st.date_input("Date", date.today())
            company = st.text_input("Company")
            contact = st.text_input("Contact Name")
            title = st.text_input("Title")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
        with c2:
            prop = st.selectbox("Property Type", ["Hotel","Multifamily","Senior Living","Student Housing","Commercial","Other"])
            source = st.selectbox("Source", ["LinkedIn","Facebook","Website","Referral","Google","Email","Phone","Other"])
            status = st.selectbox("Status", ["New Lead","Contacted","Discovery","Quote Requested","Quote Sent","Won","Lost"])
            units = st.number_input("Estimated Units", min_value=0, step=1)
            avg = st.number_input("Average Unit Price", min_value=0.0, value=425.0, step=25.0)
        next_step = st.text_input("Next Step")
        notes = st.text_area("Notes")
        if st.form_submit_button("Save Lead"):
            est = units * avg
            ok, msg = append_row("4 Lead CRM", {"Date":str(d),"Company":company,"Contact Name":contact,"Title":title,"Email":email,"Phone":phone,"Property Type":prop,"Source":source,"Status":status,"Estimated Units":units,"Estimated Value":est,"Next Step":next_step,"Notes":notes})
            st.success(f"Saved. Estimated value: {money(est)}") if ok else st.error(msg)

def add_opportunity():
    header()
    st.subheader("Add Opportunity")
    with st.form("opp", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            d = st.date_input("Date", date.today())
            company = st.text_input("Company")
            contact = st.text_input("Contact Name")
            stage = st.selectbox("Stage", ["New","Contacted","Discovery","Quote Requested","Quote Sent","Negotiation","Won","Lost"])
        with c2:
            units = st.number_input("Estimated Units", min_value=0, step=1)
            avg = st.number_input("Average Unit Price", min_value=0.0, value=425.0, step=25.0)
            prob = st.selectbox("Probability", ["10%","25%","50%","75%","90%","100%"])
            close = st.date_input("Expected Close Date", date.today())
            source = st.selectbox("Source", ["LinkedIn","Facebook","Website","Referral","Google","Email","Phone","Other"])
        notes = st.text_area("Notes")
        if st.form_submit_button("Save Opportunity"):
            val = units * avg
            ok, msg = append_row("5 Opportunity Pipeline", {"Date":str(d),"Company":company,"Contact Name":contact,"Stage":stage,"Estimated Units":units,"Average Unit Price":avg,"Pipeline Value":val,"Probability":prob,"Expected Close Date":str(close),"Source":source,"Notes":notes})
            st.success(f"Saved. Pipeline value: {money(val)}") if ok else st.error(msg)

def raw():
    header()
    sheet = st.selectbox("Sheet", SHEETS)
    st.dataframe(read_sheet(sheet), use_container_width=True, hide_index=True)

css()
with st.sidebar:
    st.title("PTAC Refurb OS")
    page = st.radio("Menu", ["Dashboard","Add Lead","Add Opportunity","Raw Data"])
    st.caption("Live via Apps Script + Google Sheets")

if page == "Dashboard": dashboard()
elif page == "Add Lead": add_lead()
elif page == "Add Opportunity": add_opportunity()
else: raw()
