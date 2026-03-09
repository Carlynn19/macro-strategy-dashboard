"""
Macro Strategy Dashboard — Streamlit application.
Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from data_pipeline import run_pipeline, resample_monthly
from signals import run_signal_engine
from config import INDICATORS, PORTFOLIO_IMPLICATIONS


# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Macro Strategy Dashboard",
    page_icon="🌐",
    layout="wide",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .regime-box {
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    .signal-positive { color: #16a34a; font-weight: 700; }
    .signal-negative { color: #dc2626; font-weight: 700; }
    .signal-neutral  { color: #a3a3a3; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── Data Loading (cached) ───────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="Pulling macro data...")
def load_data():
    table, raw = run_pipeline()
    scored, pillars, regime = run_signal_engine(table)
    return scored, pillars, regime, raw


# ── Helper Functions ─────────────────────────────────────────────────────────

REGIME_COLORS = {
    "Expansion": "#16a34a",
    "Reflation": "#f59e0b",
    "Disinflation": "#3b82f6",
    "Stagflation": "#dc2626",
    "Recession Risk": "#7f1d1d",
}


def signal_label(val: int) -> str:
    if val == 1:
        return '<span class="signal-positive">Positive (+1)</span>'
    elif val == -1:
        return '<span class="signal-negative">Negative (-1)</span>'
    return '<span class="signal-neutral">Neutral (0)</span>'


def pillar_gauge(label: str, score: float):
    """Create a small gauge chart for a pillar score."""
    color = "#16a34a" if score > 0.2 else "#dc2626" if score < -0.2 else "#a3a3a3"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": label, "font": {"size": 16}},
            number={"font": {"size": 28}},
            gauge={
                "axis": {"range": [-1, 1], "tickvals": [-1, -0.5, 0, 0.5, 1]},
                "bar": {"color": color},
                "bgcolor": "#f5f5f5",
                "steps": [
                    {"range": [-1, -0.2], "color": "#fee2e2"},
                    {"range": [-0.2, 0.2], "color": "#f5f5f5"},
                    {"range": [0.2, 1], "color": "#dcfce7"},
                ],
            },
        )
    )
    fig.update_layout(height=200, margin=dict(t=40, b=10, l=30, r=30))
    return fig


def trend_chart(series: pd.Series, title: str):
    """Line chart showing indicator history."""
    monthly = resample_monthly(series)
    if monthly.empty:
        return go.Figure().update_layout(title=title, height=250)
    fig = px.line(
        x=monthly.index,
        y=monthly.values,
        labels={"x": "", "y": ""},
        title=title,
    )
    fig.update_traces(line_color="#3b82f6")
    fig.update_layout(
        height=280,
        margin=dict(t=40, b=20, l=40, r=20),
        xaxis_title="",
        yaxis_title="",
    )
    return fig


# ── Main Dashboard ───────────────────────────────────────────────────────────

def main():
    st.title("Macro Strategy Dashboard")
    st.caption("Global macro monitoring for tactical asset allocation")

    # Load data
    try:
        scored_df, pillar_scores, regime, raw_series = load_data()
    except Exception as e:
        st.error(f"Data loading failed: {e}")
        st.info("Make sure your FRED API key is set in `config.py`.")
        st.stop()

    # ── Section 1: Macro Regime ──────────────────────────────────────────────
    st.header("Current Macro Regime")
    regime_color = REGIME_COLORS.get(regime, "#6b7280")
    st.markdown(
        f'<div class="regime-box" style="background:{regime_color}22; '
        f'border: 2px solid {regime_color}; color: {regime_color};">'
        f"{regime}</div>",
        unsafe_allow_html=True,
    )

    # ── Section 2: Pillar Scores ─────────────────────────────────────────────
    st.header("Pillar Scores")
    cols = st.columns(4)
    for i, (pillar, score) in enumerate(pillar_scores.items()):
        with cols[i]:
            st.plotly_chart(pillar_gauge(pillar, score), use_container_width=True)

    # ── Section 3: Indicator Table ───────────────────────────────────────────
    st.header("Indicator Summary")

    display_df = scored_df.copy()
    display_df["Signal"] = display_df["signal"].apply(signal_label)
    display_df = display_df.rename(columns={
        "indicator": "Indicator",
        "pillar": "Pillar",
        "current": "Current",
        "change_3m": "3M Change",
        "change_12m": "12M Change",
        "trend_5y": "5Y Trend",
        "source": "Source",
    })
    show_cols = ["Indicator", "Pillar", "Source", "Current", "3M Change", "12M Change", "5Y Trend", "Signal"]
    st.markdown(
        display_df[show_cols].to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )

    # ── Section 4: Trend Charts ──────────────────────────────────────────────
    st.header("Indicator Trends")

    for pillar in ["Growth", "Inflation", "Liquidity", "Risk Sentiment"]:
        st.subheader(pillar)
        pillar_keys = [k for k, v in INDICATORS.items() if v["pillar"] == pillar]
        chart_cols = st.columns(len(pillar_keys))
        for j, key in enumerate(pillar_keys):
            with chart_cols[j]:
                if key in raw_series and not raw_series[key].empty:
                    st.plotly_chart(
                        trend_chart(raw_series[key], INDICATORS[key]["name"]),
                        use_container_width=True,
                    )
                else:
                    st.info(f"No data for {INDICATORS[key]['name']}")

    # ── Section 5: Portfolio Implications ────────────────────────────────────
    st.header("Portfolio Implications")
    st.caption(f"Recommended positioning under **{regime}** regime")

    implications = PORTFOLIO_IMPLICATIONS.get(regime, [])
    impl_df = pd.DataFrame(implications)

    def colour_position(val):
        """Highlight the active position marker."""
        if val == "✦":
            return "font-size: 1.2rem; text-align: center;"
        return "color: #525252; text-align: center;"

    def colour_position_uw(val):
        if val == "✦":
            return "background-color: #fee2e2; color: #991b1b; font-size: 1.2rem; text-align: center;"
        return "color: #525252; text-align: center;"

    def colour_position_n(val):
        if val == "✦":
            return "background-color: #f5f5f5; color: #404040; font-size: 1.2rem; text-align: center;"
        return "color: #525252; text-align: center;"

    def colour_position_ow(val):
        if val == "✦":
            return "background-color: #dcfce7; color: #166534; font-size: 1.2rem; text-align: center;"
        return "color: #525252; text-align: center;"

    styled = (
        impl_df.style
        .hide(axis="index")
        .map(colour_position_uw, subset=["Underweight"])
        .map(colour_position_n, subset=["Neutral"])
        .map(colour_position_ow, subset=["Overweight"])
    )

    st.markdown(
        styled.to_html(escape=False),
        unsafe_allow_html=True,
    )

    # Full regime comparison table
    with st.expander("View all regime implications"):
        for r, rows in PORTFOLIO_IMPLICATIONS.items():
            regime_color = REGIME_COLORS.get(r, "#6b7280")
            st.markdown(
                f'<span style="color:{regime_color}; font-weight:700;">{r}</span>',
                unsafe_allow_html=True,
            )
            r_df = pd.DataFrame(rows)
            styled_r = (
                r_df.style
                .hide(axis="index")
                .map(colour_position_uw, subset=["Underweight"])
                .map(colour_position_n, subset=["Neutral"])
                .map(colour_position_ow, subset=["Overweight"])
            )
            st.markdown(
                styled_r.to_html(escape=False),
                unsafe_allow_html=True,
            )
            st.markdown("")

    # ── Footer ───────────────────────────────────────────────────────────────
    st.divider()
    st.caption(
        "Data sources: FRED (St. Louis Fed), Yahoo Finance. "
        "Dashboard refreshes hourly when running. Signals are rules-based and intended for research only."
    )


if __name__ == "__main__":
    main()
