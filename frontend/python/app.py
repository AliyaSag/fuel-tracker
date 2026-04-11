"""Streamlit frontend for Fuel Tracker."""

from __future__ import annotations

from datetime import date
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

try:
    from frontend.python.client import (
        FuelTrackerApiError,
        FuelTrackerClient,
    )
except ModuleNotFoundError:
    from client import FuelTrackerApiError, FuelTrackerClient


def get_client(base_url: str) -> FuelTrackerClient:
    """Reuse one API client per user session."""
    saved_base_url = st.session_state.get("api_base_url")

    if "api_client" not in st.session_state or saved_base_url != base_url:
        st.session_state["api_client"] = FuelTrackerClient(base_url=base_url)
        st.session_state["api_base_url"] = base_url

    return st.session_state["api_client"]


def format_value(value: float | int | None, suffix: str = "") -> str:
    """Format metric value with fallback for missing data."""
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return f"{value:,}{suffix}"
    return f"{value:,.2f}{suffix}"


def inject_styles() -> None:
    """Apply custom visual language for a modern dashboard look."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap');

        :root {
            color-scheme: light;
        }

        .stApp {
            color: #132b44;
            background:
                radial-gradient(circle at 6% 3%, #dff0f4 0%, transparent 35%),
                radial-gradient(circle at 92% 4%, #fde8d8 0%, transparent 34%),
                linear-gradient(160deg, #f9fcfb 0%, #eef5f2 50%, #f2f8f6 100%);
            font-family: "Manrope", "Segoe UI", sans-serif;
        }

        .block-container {
            max-width: 1060px;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }

        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebar"] {
            display: none !important;
        }

        #MainMenu,
        footer {
            visibility: hidden;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.45rem;
            border-bottom: none !important;
        }
        
        .stTabs [data-baseweb="tab-border"] {
            display: none !important;
        }
        
        .stTabs [data-baseweb="tab-highlight"] {
            display: none !important;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            border: 1px solid #c8d7e2;
            background: #ffffff;
            color: #385368;
            font-size: 0.92rem;
            font-weight: 600;
            padding: 0.42rem 0.92rem;
        }

        .stTabs [aria-selected="true"] {
            background: #dff1ee;
            border-color: #0b8d84;
            color: #173650;
        }

        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #d4e1ea;
            border-radius: 12px;
            padding: 0.5rem 0.75rem;
        }

        div[data-testid="stMetricLabel"] p {
            color: #476176;
            font-weight: 600;
        }

        div[data-testid="stMetricValue"] {
            color: #132b44;
            font-weight: 700;
        }

        div[data-testid="stForm"] {
            border-radius: 14px;
            border: 1px solid #d4e1ea;
            background: rgba(255, 255, 255, 0.85);
            padding: 1rem 1rem 0.5rem;
        }

        div[data-testid="stForm"] form {
            border: 0;
        }

        div[data-baseweb="input"],
        div[data-baseweb="base-input"],
        div[data-baseweb="textarea"],
        div[data-baseweb="select"] > div,
        [data-testid="stDateInput"] > div > div {
            background: #ffffff !important;
            border: 1px solid #9fb6c7 !important;
            border-radius: 10px !important;
            box-shadow: none !important;
        }

        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="base-input"]:focus-within,
        div[data-baseweb="textarea"]:focus-within,
        div[data-baseweb="select"] > div:focus-within,
        [data-testid="stDateInput"] > div > div:focus-within {
            border-color: #0b8d84 !important;
            box-shadow: 0 0 0 2px rgba(11, 141, 132, 0.16) !important;
        }

        [data-testid="stDateInput"] div[data-baseweb="input"] {
            border: 0 !important;
            box-shadow: none !important;
            background: transparent !important;
        }

        div[data-baseweb="input"] input,
        div[data-baseweb="base-input"] input,
        div[data-baseweb="textarea"] textarea,
        [data-testid="stDateInput"] input {
            color: #173650 !important;
            -webkit-text-fill-color: #173650 !important;
            caret-color: #173650 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.title("Fuel Tracker")
    st.caption(
        "Add refueling entries, review totals and trends, and delete "
        "incorrect records."
    )
    st.write(
        "Workflow: Add entry in tab 2, check results in tab 1, "
        "fix mistakes in tab 3."
    )


def render_metric_cards(stats: dict[str, Any], cost_unit: str) -> None:
    cost_suffix = " units" if cost_unit == "No currency" else f" {cost_unit}"
    cost_per_km_suffix = (
        " units/km" if cost_unit == "No currency" else f" {cost_unit}/km"
    )

    cards = [
        ("Entries", format_value(stats.get("total_entries"))),
        ("Total liters", format_value(stats.get("total_liters"), " L")),
        ("Total cost", format_value(stats.get("total_cost"), cost_suffix)),
        (
            "Distance",
            format_value(stats.get("total_distance_km"), " km"),
        ),
        (
            "Avg consumption",
            format_value(stats.get("average_consumption_l_per_100km"), " L/100"),
        ),
        (
            "Avg cost per km",
            format_value(stats.get("average_cost_per_km"), cost_per_km_suffix),
        ),
    ]

    columns = st.columns(2)
    for index, (label, value) in enumerate(cards):
        with columns[index % 2]:
            st.metric(label=label, value=value)


def history_to_dataframe(history: list[dict[str, Any]]) -> pd.DataFrame:
    if not history:
        return pd.DataFrame()

    frame = pd.DataFrame(history)
    frame["refueled_at"] = pd.to_datetime(frame["refueled_at"])
    frame = frame.sort_values("refueled_at").reset_index(drop=True)
    frame["distance_since_previous_km"] = frame[
        "distance_since_previous_km"
    ].fillna(0)
    return frame


def render_charts(history: list[dict[str, Any]]) -> None:
    frame = history_to_dataframe(history)
    if frame.empty:
        st.info("Add at least one refueling entry to see charts.")
        return

    chart_columns = st.columns(2)

    with chart_columns[0]:
        distance_chart = (
            alt.Chart(frame)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("refueled_at:T", title="Date"),
                y=alt.Y("distance_since_previous_km:Q", title="Distance km"),
                color=alt.value("#0f8a83"),
                tooltip=[
                    alt.Tooltip("refueled_at:T", title="Date"),
                    alt.Tooltip("distance_since_previous_km:Q", title="Distance"),
                ],
            )
            .properties(height=260, title="Distance Between Refuelings")
        )
        st.altair_chart(distance_chart, width="stretch")

    with chart_columns[1]:
        consumption_data = frame.dropna(
            subset=["consumption_l_per_100km"]
        )
        if consumption_data.empty:
            st.info("Consumption chart appears after the second entry.")
        else:
            consumption_chart = (
                alt.Chart(consumption_data)
                .mark_line(point=True, strokeWidth=3)
                .encode(
                    x=alt.X("refueled_at:T", title="Date"),
                    y=alt.Y(
                        "consumption_l_per_100km:Q",
                        title="L/100 km",
                    ),
                    color=alt.value("#c75045"),
                    tooltip=[
                        alt.Tooltip("refueled_at:T", title="Date"),
                        alt.Tooltip(
                            "consumption_l_per_100km:Q",
                            title="Consumption",
                        ),
                    ],
                )
                .properties(height=260, title="Consumption Trend")
            )
            st.altair_chart(consumption_chart, width="stretch")


def render_create_form(
    client: FuelTrackerClient,
    device_id: str | None,
) -> None:
    st.subheader("Add New Refueling")
    st.caption(
        "Required fields: date, odometer, liters, and one cost option."
    )

    with st.form("create_refueling_form", clear_on_submit=True):
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            refueled_at = st.date_input("Refueling date", value=date.today())
        with col_b:
            odometer_km = st.number_input(
                "Odometer (km)",
                min_value=0.01,
                value=10000.0,
                step=1.0,
            )
        with col_c:
            liters = st.number_input(
                "Liters",
                min_value=0.01,
                value=40.0,
                step=0.1,
            )

        total_cost = st.number_input(
            "Total cost",
            min_value=0.01,
            value=2000.0,
            step=1.0,
        )

        fuel_type = st.text_input("Fuel type (optional)", value="")
        station_name = st.text_input("Station name (optional)", value="")
        notes = st.text_area(
            "Notes (optional)",
            value="",
            max_chars=500,
        )

        submitted = st.form_submit_button("Save entry")

    if not submitted:
        return

    payload: dict[str, Any] = {
        "refueled_at": refueled_at.isoformat(),
        "odometer_km": odometer_km,
        "liters": liters,
        "total_cost": total_cost,
    }

    if fuel_type.strip():
        payload["fuel_type"] = fuel_type.strip()
    if station_name.strip():
        payload["station_name"] = station_name.strip()
    if notes.strip():
        payload["notes"] = notes.strip()

    try:
        created = client.create_refueling(payload, device_id=device_id)
    except FuelTrackerApiError as exc:
        st.error(f"Could not create refueling: {exc}")
        return

    st.session_state["show_success_toast"] = (
        f"Saved refueling entry with id {created['id']}"
    )
    st.rerun()


def render_history_panel(
    client: FuelTrackerClient,
    history: list[dict[str, Any]],
    device_id: str | None,
) -> None:
    st.subheader("Saved Refuelings")
    st.caption(
        "Use this section to review your refueling entries and delete "
        "incorrect ones."
    )

    if not history:
        st.info("No refueling entries yet for this device.")
        return

    # Header row
    widths = [0.7, 1.5, 1.5, 1.2, 1.3, 2.0, 1.2]
    header = st.columns(widths)
    header[0].markdown("**ID**")
    header[1].markdown("**Date**")
    header[2].markdown("**Odometer**")
    header[3].markdown("**Liters**")
    header[4].markdown("**Cost**")
    header[5].markdown("**Consumption**")
    header[6].markdown("**Action**")

    st.divider()

    # Show latest records first
    records_for_delete = sorted(
        history,
        key=lambda item: (str(item.get("refueled_at", "")), int(item["id"])),
        reverse=True,
    )

    for item in records_for_delete:
        row = st.columns(widths, vertical_alignment="center")
        
        row[0].write(str(item["id"]))
        
        # Display nicely formatted date
        date_str = str(item.get("refueled_at", "")).split("T")[0]
        row[1].write(date_str)
        
        row[2].write(f"{item.get('odometer_km', 0)} km")
        row[3].write(f"{item.get('liters', 0)} L")
        row[4].write(str(item.get("total_cost", 0)))
        
        cons = item.get("consumption_l_per_100km")
        if cons is not None:
            row[5].write(f"{cons:.2f} L/100km")
        else:
            row[5].write("—")

        if row[6].button(
            "Delete",
            key=f"delete_row_{item['id']}",
            type="secondary",
            use_container_width=True,
        ):
            try:
                client.delete_refueling(int(item["id"]), device_id=device_id)
            except FuelTrackerApiError as exc:
                st.error(f"Could not delete entry: {exc}")
                return
            st.session_state["show_success_toast"] = (
                f"Deleted entry id {item['id']}"
            )
            st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="Fuel Tracker Frontend",
        page_icon="FT",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_styles()
    render_hero()
    
    if "show_success_toast" in st.session_state:
        st.toast(st.session_state.pop("show_success_toast"), icon="✅")

    base_url = "http://127.0.0.1:8000"
    active_device_id = "local_user"
    cost_unit = "RUB"

    client = get_client(base_url)

    try:
        client.healthcheck()
        history = client.list_refuelings(device_id=active_device_id)
        stats = client.get_stats(device_id=active_device_id)
    except FuelTrackerApiError as exc:
        st.error(f"Failed to load backend data: {exc}")
        st.stop()

    dashboard_tab, command_tab, history_tab = st.tabs(
        ["1. Overview", "2. Add Entry", "3. History"]
    )

    with dashboard_tab:
        st.caption("Summary numbers and trends.")
        render_metric_cards(stats, cost_unit)
        st.subheader("Trends")
        render_charts(history)

    with command_tab:
        st.caption("Fill the form and press Save entry.")
        render_create_form(client, active_device_id)

    with history_tab:
        st.caption("Review records and delete an incorrect one.")
        render_history_panel(client, history, active_device_id)


if __name__ == "__main__":
    main()
