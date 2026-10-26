
from pathlib import Path

import pandas as pd
import streamlit as st

from forecaster import generate_forecast

st.set_page_config(
    page_title="SalesCast | Sales Forecasting",
    page_icon="📊",
    layout="wide",
)

st.title("SalesCast")
st.subheader("Scenario-Based Sales Forecasting")
st.caption("Explore pipeline value and weighted forecasts under different scenarios.")

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

if not (DATA_DIR / "opportunities.csv").exists():
    st.error("Opportunity data not found. Generate the data first.")
    st.stop()

scenario = st.selectbox(
    "Choose a forecasting scenario",
    ["conservative", "base", "optimistic"],
    index=1,
)

opportunities = generate_forecast(scenario)

open_opportunities = opportunities[
    opportunities["forecast_category"] == "Open Opportunity"
]

total_pipeline = open_opportunities["amount"].sum()
weighted_forecast = open_opportunities["weighted_forecast"].sum()
scenario_forecast = open_opportunities["scenario_forecast"].sum()
booked_wins = opportunities.loc[
    opportunities["forecast_category"] == "Closed Won", "amount"
].sum()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Open Pipeline", f"${total_pipeline:,.0f}")
col2.metric("Open Weighted Forecast", f"${weighted_forecast:,.0f}")
col3.metric("Scenario Forecast", f"${scenario_forecast:,.0f}")
col4.metric("Closed-Won Amount", f"${booked_wins:,.0f}")

st.divider()


st.subheader("Open Pipeline Forecast by Sales Stage")

stage_summary = (
    open_opportunities.groupby("stage_name", as_index=False)
    .agg(
        opportunity_count=("opportunity_id", "count"),
        pipeline_value=("amount", "sum"),
        weighted_forecast=("weighted_forecast", "sum"),
        scenario_forecast=("scenario_forecast", "sum"),
    )
    .sort_values("pipeline_value", ascending=False)
)

if stage_summary.empty:
    st.info("No open opportunities are available for this scenario.")
else:
    st.bar_chart(
        stage_summary,
        x="stage_name",
        y="scenario_forecast",
    )

    display_summary = stage_summary.copy()
    for column in [
        "pipeline_value",
        "weighted_forecast",
        "scenario_forecast",
    ]:
        display_summary[column] = display_summary[column].map(
            lambda value: f"${value:,.2f}"
        )

    st.dataframe(
        display_summary,
        use_container_width=True,
        hide_index=True,
    )


st.subheader("Opportunity Details")

search = st.text_input("Search by opportunity ID or stage")

if search:
    filtered = opportunities[
        opportunities["opportunity_id"].astype(str).str.contains(
            search, case=False, na=False
        )
        | opportunities["stage_name"].astype(str).str.contains(
            search, case=False, na=False
        )
    ]
else:
    filtered = opportunities

filtered = filtered[
    filtered["forecast_category"] == "Open Opportunity"
]

st.dataframe(
    filtered[
        [
    "opportunity_id",
    "stage_name",
    "amount",
    "forecast_probability",
    "weighted_forecast",
    "scenario_forecast",
]
    ],
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "Download Forecast CSV",
    data=opportunities.to_csv(index=False).encode("utf-8"),
    file_name=f"salescast_{scenario}_forecast.csv",
    mime="text/csv",
)
