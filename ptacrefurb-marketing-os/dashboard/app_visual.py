import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
from datetime import date
import plotly.graph_objects as go

st.set_page_config(
    page_title="PTAC Refurb Marketing OS",
    page_icon="📊",
    layout="wide"
)

RED = "#9C0100"
DARK = "#343434"
BORDER = "#D9D9D9"

# -----------------------------
# DATA CONNECTION
# -----------------------------

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
        response = requests.get(
            url,
            params={
                "action": "read",
                "sheet": sheet_name,
                "token": token
            },
            timeout=20
        )

        data = response.json()

        if data.get("status") != "success":
            st.error(f"Apps Script error for {sheet_name}: {data.get('message')}")
            return pd.DataFrame()

        return pd.DataFrame(data.get("rows", []))

    except Exception as e:
        st.error(f"Could not read {sheet_name}: {e}")
        return pd.DataFrame()


def to_num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)


def money(value):
    try:
        return f"${float(value):,.0f}"
    except Exception:
        return "$0"


def safe_count(df, column, value):
    if df.empty or column not in df.columns:
        return 0
    return int((df[column].astype(str).str.lower() == value.lower()).sum())


# -----------------------------
# VISUAL STYLING
# -----------------------------

st.markdown(
    f"""
    <style>
    .block-container {{
        padding-top: 0.75rem;
        padding-bottom: 1rem;
        max-width: 1700px;
    }}

    .ptac-page {{
        background: #ffffff;
        border: 1px solid #bfbfbf;
        padding: 10px 14px 12px 14px;
        font-family: Arial, sans-serif;
    }}

    .topbar {{
        display: grid;
        grid-template-columns: 31% 34% 16% 10% 9%;
        align-items: center;
        gap: 8px;
        border-bottom: 7px solid {RED};
        padding-bottom: 12px;
        margin-bottom: 16px;
    }}

    .logo-text {{
        font-size: 50px;
        font-weight: 900;
        color: {DARK};
        letter-spacing: -2px;
        white-space: nowrap;
    }}

    .logo-text span {{
        font-weight: 400;
    }}

    .main-title h1 {{
        margin: 0;
        color: {RED};
        font-size: 27px;
        font-weight: 900;
    }}

    .main-title p {{
        margin: 2px 0 0 0;
        color: #111111;
        font-size: 15px;
        font-weight: 600;
    }}

    .mini-box {{
        border: 1px solid {BORDER};
        text-align: center;
        height: 58px;
        background: #ffffff;
    }}

    .mini-head {{
        background: #f2f2f2;
        font-size: 11px;
        font-weight: 900;
        padding: 4px;
        text-transform: uppercase;
    }}

    .mini-val {{
        font-size: 14px;
        padding-top: 9px;
    }}

    .date-box .mini-head {{
        background: linear-gradient(90deg, {DARK}, {RED});
        color: white;
    }}

    .section {{
        border: 1px solid {BORDER};
        background: white;
        min-height: 165px;
        margin-bottom: 13px;
    }}

    .section-title {{
        background: linear-gradient(90deg, {RED}, #7a0000);
        color: white;
        text-align: center;
        font-size: 14px;
        font-weight: 900;
        padding: 6px;
        text-transform: uppercase;
    }}

    .brand-card {{
        display: grid;
        grid-template-columns: 48% 2% 50%;
        align-items: center;
        padding: 24px 20px;
        min-height: 105px;
    }}

    .brand-logo-text {{
        font-size: 39px;
        font-weight: 900;
        color: {DARK};
        letter-spacing: -1px;
        white-space: nowrap;
    }}

    .brand-logo-text span {{
        font-weight: 400;
    }}

    .brand-divider {{
        height: 76px;
        width: 1px;
        background: #999999;
    }}

    .brand-text {{
        font-size: 15px;
        line-height: 1.5;
        color: #111111;
    }}

    .brand-text b {{
        color: {RED};
    }}

    .table-small {{
        width: 100%;
        border-collapse: collapse;
        font-size: 11px;
    }}

    .table-small th {{
        background: #f1f1f1;
        border: 1px solid #dddddd;
        padding: 5px;
        font-weight: 900;
        text-transform: uppercase;
    }}

    .table-small td {{
        border: 1px solid #e3e3e3;
        padding: 6px;
        height: 28px;
    }}

    .empty-note {{
        color: #555555;
        font-style: italic;
        text-align: center;
        padding: 35px 10px;
        font-size: 14px;
    }}

    .footer {{
        display: grid;
        grid-template-columns: 1fr auto;
        align-items: center;
        color: #555555;
        font-size: 11px;
        padding: 10px 8px 0 8px;
    }}

    div[data-testid="stVerticalBlock"] > div {{
        gap: 0rem;
    }}

    .stPlotlyChart {{
        margin-top: -12px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# HTML HELPERS
# -----------------------------

def kpi_card(label, value, sub="-- vs last week"):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """


def render_kpi_grid(cards_html):
    full_html = f"""
    <style>
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        padding: 12px;
        font-family: Arial, sans-serif;
    }}
    .kpi-card {{
        border: 1px solid #D9D9D9;
        height: 92px;
        padding: 10px;
        background: #ffffff;
        box-sizing: border-box;
    }}
    .kpi-label {{
        font-size: 10px;
        font-weight: 900;
        text-transform: uppercase;
        color: #222222;
        text-align: center;
    }}
    .kpi-value {{
        font-size: 31px;
        font-weight: 900;
        text-align: center;
        margin-top: 8px;
        color: #111111;
    }}
    .kpi-sub {{
        font-size: 11px;
        color: #555555;
        text-align: center;
        margin-top: 2px;
    }}
    </style>
    <div class="kpi-grid">
        {cards_html}
    </div>
    """
    components.html(full_html, height=230, scrolling=False)


def table_html(df, columns, empty_message, max_rows=5):
    if df.empty:
        return f'<div class="empty-note">{empty_message}</div>'

    html = '<table class="table-small"><thead><tr>'

    for col in columns:
        html += f"<th>{col}</th>"

    html += "</tr></thead><tbody>"

    for _, row in df.head(max_rows).iterrows():
        html += "<tr>"
        for col in columns:
            value = row.get(col, "")
            html += f"<td>{value}</td>"
        html += "</tr>"

    html += "</tbody></table>"

    return html


def funnel_chart(impressions, visits, leads, quote_requests, quotes_sent, deals_won):
    fig = go.Figure(
        go.Funnel(
            y=[
                "Impressions",
                "Website Visits",
                "New Leads",
                "Quote Requests",
                "Quotes Sent",
                "Deals Won"
            ],
            x=[
                impressions,
                visits,
                leads,
                quote_requests,
                quotes_sent,
                deals_won
            ],
            marker={
                "color": [
                    RED,
                    "#B73535",
                    "#D46A6A",
                    "#E8A2A2",
                    "#F0CCCC",
                    DARK
                ]
            },
            textinfo="value"
        )
    )

    fig.update_layout(
        height=235,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False
    )

    return fig


def donut_chart(labels, values):
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker_colors=[RED, DARK, "#888888", "#CFCFCF", "#111111"]
        )
    )

    fig.update_layout(
        height=235,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True
    )

    return fig


# -----------------------------
# LOAD DATA
# -----------------------------

leads = read_sheet("4 Lead CRM")
pipeline = read_sheet("5 Opportunity Pipeline")
content = read_sheet("7 Content Performance")
website = read_sheet("9 Website Roadmap")
outreach = read_sheet("8 Outreach Tracker")
calendar = read_sheet("6 Content Calendar")
weekly = read_sheet("3 Weekly KPI Tracker")
revenue = read_sheet("10 Revenue Attribution")

# -----------------------------
# CALCULATIONS
# -----------------------------

total_leads = len(leads)

quote_requests = safe_count(leads, "Status", "Quote Requested")
quotes_sent = safe_count(leads, "Status", "Quote Sent")
deals_won = safe_count(leads, "Status", "Won")

pipeline_value = (
    to_num(pipeline["Pipeline Value"]).sum()
    if not pipeline.empty and "Pipeline Value" in pipeline.columns
    else 0
)

closed_revenue = (
    to_num(revenue["Closed Revenue"]).sum()
    if not revenue.empty and "Closed Revenue" in revenue.columns
    else 0
)

content_impressions = (
    to_num(content["Impressions"]).sum()
    if not content.empty and "Impressions" in content.columns
    else 0
)

content_clicks = (
    to_num(content["Clicks"]).sum()
    if not content.empty and "Clicks" in content.columns
    else 0
)

latest_week = weekly.tail(1) if not weekly.empty else pd.DataFrame()

linkedin_followers = (
    int(to_num(latest_week["LinkedIn Followers"]).iloc[0])
    if not latest_week.empty and "LinkedIn Followers" in latest_week.columns
    else 0
)

facebook_followers = (
    int(to_num(latest_week["Facebook Followers"]).iloc[0])
    if not latest_week.empty and "Facebook Followers" in latest_week.columns
    else 0
)

website_visitors = (
    int(to_num(latest_week["Website Visitors"]).iloc[0])
    if not latest_week.empty and "Website Visitors" in latest_week.columns
    else 0
)

# -----------------------------
# DASHBOARD PAGE
# -----------------------------

st.markdown('<div class="ptac-page">', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="topbar">
        <div class="logo-text">PTAC<span>refurb</span></div>
        <div class="main-title">
            <h1>PTAC REFURB MARKETING OS v2</h1>
            <p>Marketing. Leads. Pipeline. Revenue.<br>All in One Place.</p>
        </div>
        <div class="mini-box">
            <div class="mini-head">Owner</div>
            <div class="mini-val">CP</div>
        </div>
        <div class="mini-box">
            <div class="mini-head">Role</div>
            <div class="mini-val">Marketing Director</div>
        </div>
        <div class="mini-box date-box">
            <div class="mini-head">Today's Date</div>
            <div class="mini-val">{date.today().strftime("%m/%d/%Y")}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

row1_col1, row1_col2, row1_col3 = st.columns([1.45, 0.9, 0.9])

with row1_col1:
    st.markdown(
        '<div class="section"><div class="section-title">Executive Dashboard (Week to Date)</div>',
        unsafe_allow_html=True
    )

    cards = (
        kpi_card("LinkedIn Followers", linkedin_followers)
        + kpi_card("Facebook Followers", facebook_followers)
        + kpi_card("Website Visitors", website_visitors)
        + kpi_card("New Leads", total_leads)
        + kpi_card("Quote Requests", quote_requests)
        + kpi_card("Quotes Sent", quotes_sent)
        + kpi_card("Pipeline Value", money(pipeline_value))
        + kpi_card("Closed Revenue", money(closed_revenue))
    )

    render_kpi_grid(cards)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="section">
            <div class="brand-card">
                <div class="brand-logo-text">PTAC<span>refurb</span></div>
                <div class="brand-divider"></div>
                <div class="brand-text">
                    We help properties <b>save</b><br>
                    money and extend the life<br>
                    of their PTAC units.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with row1_col2:
    st.markdown(
        '<div class="section"><div class="section-title">Marketing Funnel (This Month)</div>',
        unsafe_allow_html=True
    )

    st.plotly_chart(
        funnel_chart(
            content_impressions,
            website_visitors,
            total_leads,
            quote_requests,
            quotes_sent,
            deals_won
        ),
        use_container_width=True,
        config={"displayModeBar": False}
    )

    st.markdown('</div>', unsafe_allow_html=True)

with row1_col3:
    st.markdown(
        '<div class="section"><div class="section-title">Lead Sources (This Month)</div>',
        unsafe_allow_html=True
    )

    if not leads.empty and "Source" in leads.columns:
        source_counts = leads.groupby("Source").size()

        if not source_counts.empty:
            st.plotly_chart(
                donut_chart(source_counts.index.tolist(), source_counts.values.tolist()),
                use_container_width=True,
                config={"displayModeBar": False}
            )
        else:
            st.plotly_chart(
                donut_chart(["LinkedIn", "Facebook", "Website", "Referral", "Other"], [0, 0, 0, 0, 0]),
                use_container_width=True,
                config={"displayModeBar": False}
            )
    else:
        st.plotly_chart(
            donut_chart(["LinkedIn", "Facebook", "Website", "Referral", "Other"], [0, 0, 0, 0, 0]),
            use_container_width=True,
            config={"displayModeBar": False}
        )

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="section"><div class="section-title">Top Content (This Month)</div>',
    unsafe_allow_html=True
)

st.markdown(
    table_html(
        content,
        ["Post Topic", "Platform", "Impressions", "Clicks", "Engagement Rate"],
        "No data yet. Start posting and tracking!",
        max_rows=4
    ),
    unsafe_allow_html=True
)

st.markdown('</div>', unsafe_allow_html=True)

row3_col1, row3_col2, row3_col3 = st.columns([1, 0.9, 1])

with row3_col1:
    st.markdown(
        '<div class="section"><div class="section-title">Recent Leads</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        table_html(
            leads,
            ["Date", "Company", "Contact Name", "Source", "Status", "Estimated Value"],
            "No leads yet. Add your first lead in Streamlit.",
            max_rows=5
        ),
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

with row3_col2:
    st.markdown(
        '<div class="section"><div class="section-title">Pipeline at a Glance</div>',
        unsafe_allow_html=True
    )

    if not pipeline.empty and "Stage" in pipeline.columns:
        pipeline_copy = pipeline.copy()

        if "Pipeline Value" in pipeline_copy.columns:
            pipeline_copy["Pipeline Value"] = to_num(pipeline_copy["Pipeline Value"])

        grouped_pipeline = (
            pipeline_copy
            .groupby("Stage")
            .agg({
                "Company": "count",
                "Pipeline Value": "sum"
            })
            .reset_index()
            .rename(columns={"Company": "# Opportunities"})
        )

        grouped_pipeline["Pipeline Value"] = grouped_pipeline["Pipeline Value"].apply(money)

        st.markdown(
            table_html(
                grouped_pipeline,
                ["Stage", "# Opportunities", "Pipeline Value"],
                "No pipeline yet.",
                max_rows=8
            ),
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div class="empty-note">No pipeline yet.</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

with row3_col3:
    st.markdown(
        '<div class="section"><div class="section-title">Website Health</div>',
        unsafe_allow_html=True
    )

    website_health = pd.DataFrame(
        [
            {
                "Metric": "Total Visitors",
                "This Month": website_visitors,
                "Last Month": 0,
                "Change": "--"
            },
            {
                "Metric": "New Visitors",
                "This Month": "--",
                "Last Month": "--",
                "Change": "--"
            },
            {
                "Metric": "Page Views",
                "This Month": "--",
                "Last Month": "--",
                "Change": "--"
            },
            {
                "Metric": "Top Landing Page",
                "This Month": "--",
                "Last Month": "--",
                "Change": "--"
            },
            {
                "Metric": "Avg. Session Duration",
                "This Month": "--",
                "Last Month": "--",
                "Change": "--"
            }
        ]
    )

    st.markdown(
        table_html(
            website_health,
            ["Metric", "This Month", "Last Month", "Change"],
            "",
            max_rows=5
        ),
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

row4_col1, row4_col2, row4_col3 = st.columns(3)

with row4_col1:
    st.markdown(
        '<div class="section"><div class="section-title">Upcoming Content (Next 7 Days)</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        table_html(
            calendar,
            ["Date", "Platform", "Post Topic", "Status"],
            "No upcoming content.",
            max_rows=4
        ),
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

with row4_col2:
    st.markdown(
        '<div class="section"><div class="section-title">Upcoming Outreach (Next 7 Days)</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        table_html(
            outreach,
            ["Date", "Contact Name", "Company", "Outreach Type", "Status"],
            "No upcoming outreach.",
            max_rows=4
        ),
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

with row4_col3:
    st.markdown(
        '<div class="section"><div class="section-title">Priority Website Tasks</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        table_html(
            website,
            ["Task", "Priority", "Status", "Target Date"],
            "No website tasks.",
            max_rows=4
        ),
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="footer">
        <div>
            Built with purpose. Driven by results. &nbsp; | &nbsp;
            PTAC Refurb Marketing OS &nbsp; | &nbsp; Owner: <b>CP</b>
        </div>
        <div><b>PTACrefurb</b></div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('</div>', unsafe_allow_html=True)
