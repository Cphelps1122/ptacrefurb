import streamlit as st
import pandas as pd
import requests
from datetime import date
import html

st.set_page_config(page_title="PTAC Refurb Marketing OS", page_icon="📊", layout="wide")

RED = "#9C0100"
DARK = "#343434"
BORDER = "#D9D9D9"

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
    try:
        r = requests.get(url, params={"action":"read","sheet":sheet_name,"token":token}, timeout=20)
        data = r.json()
        if data.get("status") != "success":
            st.warning(f"{sheet_name}: {data.get('message')}")
            return pd.DataFrame()
        return pd.DataFrame(data.get("rows", []))
    except Exception as e:
        st.warning(f"Could not read {sheet_name}: {e}")
        return pd.DataFrame()

def to_num(x):
    return pd.to_numeric(x, errors="coerce").fillna(0)

def money(x):
    try:
        return f"${float(x):,.0f}"
    except Exception:
        return "$0"

def esc(x):
    return html.escape(str("" if x is None else x))

def count_status(df, status):
    if df.empty or "Status" not in df.columns:
        return 0
    return int((df["Status"].astype(str).str.strip().str.lower() == status.lower()).sum())

def latest(df, col):
    if df.empty or col not in df.columns:
        return 0
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    return int(s.iloc[-1]) if len(s) else 0

def kpi(label, value):
    return f"""
    <div class='kpi'>
      <div class='kpi-label'>{esc(label)}</div>
      <div class='kpi-value'>{esc(value)}</div>
      <div class='kpi-sub'>-- vs last week</div>
    </div>
    """

def table_html(df, cols, max_rows=5):
    if df.empty:
        return f"<table><tr><td class='empty' colspan='{len(cols)}'>No data yet</td></tr></table>"
    header = "".join(f"<th>{esc(c)}</th>" for c in cols)
    rows = ""
    for _, r in df.head(max_rows).iterrows():
        rows += "<tr>" + "".join(f"<td>{esc(r.get(c, ''))}</td>" for c in cols) + "</tr>"
    return f"<table><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table>"

def funnel_row(label, value, max_value):
    pct = 0 if max_value == 0 else max(8, min(100, (float(value) / max_value) * 100))
    return f"""
    <div class='funnel-row'>
      <div class='funnel-label'>{esc(label)}</div>
      <div class='funnel-track'><div class='funnel-fill' style='width:{pct:.1f}%'>{int(value)}</div></div>
    </div>
    """

def legend(source_counts):
    if source_counts.empty:
        items = [("LinkedIn",0),("Facebook",0),("Website",0),("Referral",0)]
    else:
        items = [(str(k), int(v)) for k, v in source_counts.items()]
    return "".join(f"<div class='legend'><span></span>{esc(k)}: {v}</div>" for k, v in items[:5])

weekly = read_sheet("3 Weekly KPI Tracker")
leads = read_sheet("4 Lead CRM")
pipeline = read_sheet("5 Opportunity Pipeline")
calendar = read_sheet("6 Content Calendar")
content = read_sheet("7 Content Performance")
outreach = read_sheet("8 Outreach Tracker")
website = read_sheet("9 Website Roadmap")
revenue = read_sheet("10 Revenue Attribution")

li = latest(weekly, "LinkedIn Followers")
fb = latest(weekly, "Facebook Followers")
visitors = latest(weekly, "Website Visitors")
lead_count = len(leads)
quote_requests = count_status(leads, "Quote Requested")
quotes_sent = count_status(leads, "Quote Sent")
won = count_status(leads, "Won")
pipeline_value = to_num(pipeline["Pipeline Value"]).sum() if not pipeline.empty and "Pipeline Value" in pipeline.columns else 0
closed_revenue = to_num(revenue["Closed Revenue"]).sum() if not revenue.empty and "Closed Revenue" in revenue.columns else 0
impressions = to_num(content["Impressions"]).sum() if not content.empty and "Impressions" in content.columns else 0
clicks = to_num(content["Clicks"]).sum() if not content.empty and "Clicks" in content.columns else 0
max_funnel = max(impressions, visitors, lead_count, quote_requests, quotes_sent, won, 1)

if not leads.empty and "Source" in leads.columns:
    src = leads["Source"].fillna("Unknown").astype(str).replace("", "Unknown").value_counts()
else:
    src = pd.Series(dtype=int)

if not pipeline.empty and "Stage" in pipeline.columns:
    p = pipeline.copy()
    p["Pipeline Value"] = to_num(p["Pipeline Value"]) if "Pipeline Value" in p.columns else 0
    pipe_group = p.groupby("Stage", dropna=False).agg(Opportunities=("Company","count"), Value=("Pipeline Value","sum")).reset_index()
    pipe_group["Value"] = pipe_group["Value"].apply(money)
else:
    pipe_group = pd.DataFrame(columns=["Stage","Opportunities","Value"])

if not content.empty and "Impressions" in content.columns:
    content = content.copy()
    content["_imp"] = to_num(content["Impressions"])
    content = content.sort_values("_imp", ascending=False)

css = f"""
<style>
.stApp {{ background:#f3f3f3; }}
.block-container {{ max-width:1800px; padding:10px 18px 30px; }}
header {{ visibility:hidden; height:0; }}
.sheet {{ background:white; border:1px solid #a9a9a9; padding:14px; font-family:Arial,sans-serif; color:#111; box-shadow:0 2px 12px rgba(0,0,0,.08); }}
.top {{ display:grid; grid-template-columns:310px 1fr 145px 130px 150px; gap:8px; border-bottom:8px solid {RED}; padding-bottom:12px; margin-bottom:14px; align-items:stretch; }}
.logo {{ font-size:49px; font-weight:900; color:{DARK}; letter-spacing:-3px; display:flex; align-items:center; }}
.logo span {{ font-weight:400; }}
.title {{ display:flex; flex-direction:column; justify-content:center; }}
.title h1 {{ margin:0; color:{RED}; font-size:30px; font-weight:900; }}
.title p {{ margin:3px 0 0; font-size:15px; font-weight:700; line-height:1.25; }}
.info-box {{ border:1px solid {BORDER}; text-align:center; background:white; }}
.info-head {{ background:#eee; padding:5px; font-size:11px; font-weight:900; text-transform:uppercase; }}
.info-val {{ padding:12px 4px; font-size:13px; }}
.date .info-head {{ background:linear-gradient(90deg,{DARK},{RED}); color:white; }}
.grid-top {{ display:grid; grid-template-columns:1.55fr .95fr .95fr; gap:12px; }}
.grid-3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; }}
.section {{ border:1px solid {BORDER}; background:white; margin-bottom:12px; }}
.section-title {{ background:linear-gradient(90deg,{RED},#710000); color:white; text-align:center; font-weight:900; font-size:14px; padding:7px; text-transform:uppercase; }}
.kpi-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:9px; padding:12px; }}
.kpi {{ border:1px solid {BORDER}; height:96px; background:white; padding:10px 8px; box-sizing:border-box; }}
.kpi-label {{ text-align:center; font-weight:900; font-size:10px; text-transform:uppercase; line-height:1.1; }}
.kpi-value {{ text-align:center; font-weight:900; font-size:30px; margin-top:9px; }}
.kpi-sub {{ text-align:center; color:#666; font-size:11px; margin-top:2px; }}
.brand-strip {{ display:grid; grid-template-columns:46% 1px 1fr; gap:20px; align-items:center; padding:28px 25px; }}
.brand-logo {{ font-size:42px; font-weight:900; color:{DARK}; letter-spacing:-2px; }}
.brand-logo span {{ font-weight:400; }}
.divider {{ width:1px; height:78px; background:#888; }}
.brand-copy {{ font-size:17px; line-height:1.35; }}
.brand-copy b {{ color:{RED}; }}
.funnel {{ padding:14px 15px 20px; min-height:255px; }}
.funnel-row {{ margin-bottom:12px; }}
.funnel-label {{ font-size:11px; font-weight:900; text-transform:uppercase; margin-bottom:4px; }}
.funnel-track {{ width:100%; background:#eee; height:24px; border:1px solid #ddd; }}
.funnel-fill {{ height:24px; background:linear-gradient(90deg,{RED},#d56a6a); color:white; font-size:12px; font-weight:900; text-align:right; padding-right:8px; line-height:24px; box-sizing:border-box; }}
.donut-area {{ padding:15px; min-height:255px; display:grid; grid-template-columns:155px 1fr; gap:15px; align-items:center; }}
.donut {{ width:145px; height:145px; border-radius:50%; background:radial-gradient(circle at center, white 0 48%, transparent 49%), conic-gradient({RED} 0 40%, {DARK} 40% 64%, #888 64% 82%, #d0d0d0 82% 100%); border:1px solid #ddd; }}
.legend {{ font-size:12px; margin:7px 0; font-weight:700; }}
.legend span {{ display:inline-block; width:10px; height:10px; background:{RED}; margin-right:7px; }}
table {{ width:100%; border-collapse:collapse; font-size:11px; }}
th {{ background:#efefef; border:1px solid #dcdcdc; padding:6px; text-transform:uppercase; font-weight:900; }}
td {{ border:1px solid #e6e6e6; padding:7px; height:27px; }}
.empty {{ text-align:center; color:#666; font-style:italic; padding:32px; }}
.footer {{ display:grid; grid-template-columns:1fr auto; font-size:11px; color:#555; padding-top:8px; }}
</style>
"""

dashboard = f"""
{css}
<div class="sheet">
  <div class="top">
    <div class="logo">PTAC<span>refurb</span></div>
    <div class="title"><h1>PTAC REFURB MARKETING OS v2</h1><p>Marketing. Leads. Pipeline. Revenue.<br>All in One Place.</p></div>
    <div class="info-box"><div class="info-head">Owner</div><div class="info-val">CP</div></div>
    <div class="info-box"><div class="info-head">Role</div><div class="info-val">Marketing Director</div></div>
    <div class="info-box date"><div class="info-head">Today's Date</div><div class="info-val">{date.today().strftime("%m/%d/%Y")}</div></div>
  </div>

  <div class="grid-top">
    <div>
      <div class="section">
        <div class="section-title">Executive Dashboard (Week to Date)</div>
        <div class="kpi-grid">
          {kpi("LinkedIn Followers", li)}
          {kpi("Facebook Followers", fb)}
          {kpi("Website Visitors", visitors)}
          {kpi("New Leads", lead_count)}
          {kpi("Quote Requests", quote_requests)}
          {kpi("Quotes Sent", quotes_sent)}
          {kpi("Pipeline Value", money(pipeline_value))}
          {kpi("Closed Revenue", money(closed_revenue))}
        </div>
      </div>
      <div class="section">
        <div class="brand-strip"><div class="brand-logo">PTAC<span>refurb</span></div><div class="divider"></div><div class="brand-copy">We help properties <b>save</b><br>money and extend the life<br>of their PTAC units.</div></div>
      </div>
    </div>
    <div class="section"><div class="section-title">Marketing Funnel (This Month)</div><div class="funnel">
      {funnel_row("Impressions", impressions, max_funnel)}
      {funnel_row("Website Visits", visitors, max_funnel)}
      {funnel_row("New Leads", lead_count, max_funnel)}
      {funnel_row("Quote Requests", quote_requests, max_funnel)}
      {funnel_row("Quotes Sent", quotes_sent, max_funnel)}
      {funnel_row("Deals Won", won, max_funnel)}
    </div></div>
    <div class="section"><div class="section-title">Lead Sources (This Month)</div><div class="donut-area"><div class="donut"></div><div>{legend(src)}</div></div></div>
  </div>

  <div class="section"><div class="section-title">Top Content (This Month)</div>{table_html(content, ["Post Topic","Platform","Impressions","Clicks","Engagement Rate"], 4)}</div>

  <div class="grid-3">
    <div class="section"><div class="section-title">Recent Leads</div>{table_html(leads, ["Date","Company","Contact Name","Source","Status","Estimated Value"], 5)}</div>
    <div class="section"><div class="section-title">Pipeline at a Glance</div>{table_html(pipe_group, ["Stage","Opportunities","Value"], 6)}</div>
    <div class="section"><div class="section-title">Website Health</div>{table_html(pd.DataFrame([
        {"Metric":"Total Visitors","This Month":visitors,"Last Month":"--","Change":"--"},
        {"Metric":"New Visitors","This Month":"--","Last Month":"--","Change":"--"},
        {"Metric":"Page Views","This Month":"--","Last Month":"--","Change":"--"},
        {"Metric":"Top Landing Page","This Month":"--","Last Month":"--","Change":"--"},
        {"Metric":"Avg. Session Duration","This Month":"--","Last Month":"--","Change":"--"}
    ]), ["Metric","This Month","Last Month","Change"], 5)}</div>
  </div>

  <div class="grid-3">
    <div class="section"><div class="section-title">Upcoming Content (Next 7 Days)</div>{table_html(calendar, ["Date","Platform","Post Topic","Status"], 4)}</div>
    <div class="section"><div class="section-title">Upcoming Outreach (Next 7 Days)</div>{table_html(outreach, ["Date","Contact Name","Company","Outreach Type","Status"], 4)}</div>
    <div class="section"><div class="section-title">Priority Website Tasks</div>{table_html(website, ["Task","Priority","Status","Target Date"], 4)}</div>
  </div>

  <div class="footer"><div>Built with purpose. Driven by results. | PTAC Refurb Marketing OS | Owner: <b>CP</b></div><div><b>PTACrefurb</b></div></div>
</div>
"""

st.markdown(dashboard, unsafe_allow_html=True)
