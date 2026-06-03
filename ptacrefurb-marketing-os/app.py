from __future__ import annotations

from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="PTAC Refurb Marketing OS", page_icon="📈", layout="wide")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKBOOK = ROOT / "data" / "PTAC_Refurb_Marketing_OS.xlsx"

SHEET_CONFIG = {
    "dashboard": {"sheet": "Dashboard", "header": 5},
    "leads": {"sheet": "Leads CRM", "header": 3},
    "calendar": {"sheet": "Content Calendar", "header": 3},
    "content": {"sheet": "Content Performance", "header": 3},
    "outreach": {"sheet": "Outreach Tracker", "header": 3},
    "website": {"sheet": "Website Roadmap", "header": 3},
}

STATUS_ORDER = ["New", "Contacted", "Discovery", "Quote Requested", "Quote Sent", "Won", "Lost"]


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", case=False, na=False)]
    df = df.dropna(how="all")
    return df


def money(value: Any) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        value = value.replace("$", "").replace(",", "").strip()
    return pd.to_numeric(value, errors="coerce") if pd.notna(pd.to_numeric(value, errors="coerce")) else 0.0


def numeric_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(0)


@st.cache_data(show_spinner=False)
def load_from_excel(file_or_path: Any) -> dict[str, pd.DataFrame]:
    data: dict[str, pd.DataFrame] = {}
    for key, cfg in SHEET_CONFIG.items():
        try:
            data[key] = clean_df(pd.read_excel(file_or_path, sheet_name=cfg["sheet"], header=cfg["header"]))
        except Exception:
            data[key] = pd.DataFrame()
    return data


@st.cache_data(show_spinner=False)
def load_csv(url: str) -> pd.DataFrame:
    return clean_df(pd.read_csv(url))


def load_data() -> dict[str, pd.DataFrame]:
    st.sidebar.header("Data Source")
    source = st.sidebar.radio(
        "Choose how to load your Marketing OS data",
        ["Use repo workbook", "Upload workbook", "Use Google Sheet CSV links"],
        index=0,
    )

    if source == "Upload workbook":
        uploaded = st.sidebar.file_uploader("Upload PTAC_Refurb_Marketing_OS.xlsx", type=["xlsx"])
        if uploaded is None:
            st.info("Upload the Marketing OS spreadsheet to view the dashboard.")
            st.stop()
        return load_from_excel(uploaded)

    if source == "Use Google Sheet CSV links":
        links = st.secrets.get("google_sheets", {}) if hasattr(st, "secrets") else {}
        mapping = {
            "dashboard": "dashboard_csv",
            "leads": "leads_csv",
            "content": "content_performance_csv",
            "calendar": "content_calendar_csv",
            "outreach": "outreach_csv",
            "website": "website_roadmap_csv",
        }
        if not any(links.get(v, "") for v in mapping.values()):
            st.warning("No Google Sheet CSV links are set in Streamlit secrets yet. Use the repo workbook or upload the workbook for now.")
            st.stop()
        return {key: load_csv(links.get(secret_key, "")) if links.get(secret_key, "") else pd.DataFrame() for key, secret_key in mapping.items()}

    if not DEFAULT_WORKBOOK.exists():
        st.error("The default workbook is missing from data/PTAC_Refurb_Marketing_OS.xlsx")
        st.stop()
    return load_from_excel(DEFAULT_WORKBOOK)


def metric_card(label: str, value: str | int | float, help_text: str | None = None) -> None:
    st.metric(label, value, help=help_text)


def main() -> None:
    st.title("PTAC Refurb Marketing OS")
    st.caption("Executive dashboard for marketing activity, leads, quote pipeline, and content performance.")

    data = load_data()
    dashboard = data["dashboard"]
    leads = data["leads"]
    content = data["content"]
    calendar = data["calendar"]
    outreach = data["outreach"]
    website = data["website"]

    # Lead calculations
    lead_count = len(leads)
    statuses = leads.get("Status", pd.Series(dtype=str)).fillna("").astype(str).str.strip() if not leads.empty else pd.Series(dtype=str)
    quote_requests = int((statuses == "Quote Requested").sum())
    quotes_sent = int((statuses == "Quote Sent").sum())
    deals_won = int((statuses == "Won").sum())

    if "Estimated Opportunity Value" in leads.columns:
        pipeline_value = numeric_series(leads, "Estimated Opportunity Value").sum()
    elif {"Estimated Units", "Estimated Unit Price"}.issubset(leads.columns):
        pipeline_value = (numeric_series(leads, "Estimated Units") * numeric_series(leads, "Estimated Unit Price")).sum()
    else:
        pipeline_value = 0

    if "Closed Revenue" in leads.columns:
        closed_revenue = numeric_series(leads, "Closed Revenue").sum()
    elif "Estimated Opportunity Value" in leads.columns and not leads.empty:
        closed_revenue = numeric_series(leads[statuses == "Won"], "Estimated Opportunity Value").sum()
    else:
        closed_revenue = 0

    # Content calculations
    impressions = numeric_series(content, "Impressions/Reach").sum() if not content.empty else 0
    clicks = numeric_series(content, "Clicks").sum() if not content.empty else 0
    leads_influenced = numeric_series(content, "Leads Influenced").sum() if not content.empty else 0

    st.subheader("Executive Snapshot")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Leads", lead_count)
    with c2:
        metric_card("Quotes Sent", quotes_sent)
    with c3:
        metric_card("Pipeline Value", f"${pipeline_value:,.0f}")
    with c4:
        metric_card("Closed Revenue", f"${closed_revenue:,.0f}")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        metric_card("Content Impressions", f"{int(impressions):,}")
    with c6:
        metric_card("Content Clicks", f"{int(clicks):,}")
    with c7:
        metric_card("Quote Requests", quote_requests)
    with c8:
        metric_card("Deals Won", deals_won)

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Pipeline", "Content", "Calendar", "Website", "Raw Data"])

    with tab1:
        st.subheader("Lead Pipeline")
        if leads.empty:
            st.info("No leads entered yet.")
        else:
            left, right = st.columns([1, 2])
            with left:
                if "Status" in leads.columns:
                    status_counts = statuses.value_counts().reindex(STATUS_ORDER).dropna().reset_index()
                    status_counts.columns = ["Status", "Count"]
                    chart = alt.Chart(status_counts).mark_bar().encode(
                        x=alt.X("Count:Q"),
                        y=alt.Y("Status:N", sort=STATUS_ORDER),
                        tooltip=["Status", "Count"],
                    )
                    st.altair_chart(chart, use_container_width=True)
            with right:
                show_cols = [c for c in ["Date Added", "Company", "Contact Name", "Title/Role", "Property Type", "Source", "Status", "Estimated Units", "Estimated Opportunity Value", "Next Follow-Up"] if c in leads.columns]
                st.dataframe(leads[show_cols], use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Content Performance")
        if content.empty:
            st.info("No content performance data entered yet.")
        else:
            if "Date" in content.columns and "Impressions/Reach" in content.columns:
                content_plot = content.copy()
                content_plot["Date"] = pd.to_datetime(content_plot["Date"], errors="coerce")
                content_plot["Impressions/Reach"] = numeric_series(content_plot, "Impressions/Reach")
                chart = alt.Chart(content_plot.dropna(subset=["Date"])).mark_line(point=True).encode(
                    x="Date:T", y="Impressions/Reach:Q", color="Platform:N", tooltip=["Date", "Platform", "Topic", "Impressions/Reach"]
                )
                st.altair_chart(chart, use_container_width=True)
            show_cols = [c for c in ["Date", "Platform", "Topic", "Post Link", "Impressions/Reach", "Reactions", "Comments", "Shares", "Clicks", "Leads Influenced"] if c in content.columns]
            st.dataframe(content[show_cols], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Upcoming Content Calendar")
        if calendar.empty:
            st.info("No content calendar loaded.")
        else:
            upcoming = calendar.copy()
            if "Status" in upcoming.columns:
                upcoming = upcoming[upcoming["Status"].fillna("").astype(str).str.lower() != "posted"]
            show_cols = [c for c in ["Week", "Date", "Day", "Time", "Platform", "Topic", "Audience", "Status"] if c in upcoming.columns]
            st.dataframe(upcoming[show_cols].head(20), use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("Website Roadmap")
        if website.empty:
            st.info("No website roadmap loaded.")
        else:
            show_cols = [c for c in ["Priority", "Page/Area", "Change Needed", "Reason", "Status", "Date Completed", "Impact/Result", "Owner"] if c in website.columns]
            st.dataframe(website[show_cols], use_container_width=True, hide_index=True)

    with tab5:
        st.subheader("Loaded Tables")
        st.write("Dashboard")
        st.dataframe(dashboard, use_container_width=True, hide_index=True)
        st.write("Leads CRM")
        st.dataframe(leads, use_container_width=True, hide_index=True)
        st.write("Outreach")
        st.dataframe(outreach, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
