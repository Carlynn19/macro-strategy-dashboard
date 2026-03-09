"""
Configuration for Macro Strategy Dashboard.
Contains indicator definitions, data sources, and classification rules.
"""

import os

# ── FRED API Key ─────────────────────────────────────────────────────────────
# Reads from Streamlit secrets (cloud) or environment variable (local).
# For local dev, set: export FRED_API_KEY="your_key_here"
# For Streamlit Cloud, add to Settings → Secrets.
try:
    import streamlit as st
    FRED_API_KEY = st.secrets.get("FRED_API_KEY", os.environ.get("FRED_API_KEY", ""))
except Exception:
    FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# ── Indicator Definitions ────────────────────────────────────────────────────
# Each indicator: (name, pillar, source_type, ticker/series_id, description, frequency)

INDICATORS = {
    # ── Growth ───────────────────────────────────────────────────────────────
    "global_pmi": {
        "name": "US Industrial Production",
        "pillar": "Growth",
        "source": "fred",
        "ticker": "INDPRO",
        "description": "Industrial Production Index — proxy for global growth momentum",
        "frequency": "Monthly",
    },
    "ism_manufacturing": {
        "name": "Manufacturing Capacity Utilization",
        "pillar": "Growth",
        "source": "fred",
        "ticker": "MCUMFN",
        "description": "Manufacturing Capacity Utilization Rate — higher = stronger manufacturing",
        "frequency": "Monthly",
    },
    "unemployment_rate": {
        "name": "US Unemployment Rate",
        "pillar": "Growth",
        "source": "fred",
        "ticker": "UNRATE",
        "description": "US civilian unemployment rate (seasonally adjusted)",
        "frequency": "Monthly",
    },
    # ── Inflation ────────────────────────────────────────────────────────────
    "cpi": {
        "name": "CPI Year-over-Year",
        "pillar": "Inflation",
        "source": "fred",
        "ticker": "CPIAUCSL",
        "description": "Consumer Price Index for All Urban Consumers (SA)",
        "frequency": "Monthly",
    },
    "breakeven_10y": {
        "name": "10Y Breakeven Inflation",
        "pillar": "Inflation",
        "source": "fred",
        "ticker": "T10YIE",
        "description": "10-Year Breakeven Inflation Rate — market inflation expectation",
        "frequency": "Daily",
    },
    "commodity_index": {
        "name": "Bloomberg Commodity Index (proxy)",
        "pillar": "Inflation",
        "source": "yahoo",
        "ticker": "^GSPC",  # Using DJP as commodity proxy; fallback to GSCI
        "description": "Broad commodity index proxy via iPath Bloomberg Commodity ETN",
        "frequency": "Daily",
    },
    # ── Liquidity ────────────────────────────────────────────────────────────
    "real_interest_rate": {
        "name": "Real Interest Rate (10Y - CPI)",
        "pillar": "Liquidity",
        "source": "fred",
        "ticker": "REAINTRATREARAT10Y",
        "description": "10-Year Treasury Constant Maturity minus CPI inflation",
        "frequency": "Monthly",
    },
    "fed_balance_sheet": {
        "name": "Federal Reserve Balance Sheet",
        "pillar": "Liquidity",
        "source": "fred",
        "ticker": "WALCL",
        "description": "Total Assets of the Federal Reserve (Weds, SA)",
        "frequency": "Weekly",
    },
    "financial_conditions": {
        "name": "Chicago Fed Financial Conditions Index",
        "pillar": "Liquidity",
        "source": "fred",
        "ticker": "NFCI",
        "description": "NFCI — negative = loose conditions, positive = tight",
        "frequency": "Weekly",
    },
    # ── Risk Sentiment ───────────────────────────────────────────────────────
    "credit_spreads": {
        "name": "ICE BofA US HY Option-Adjusted Spread",
        "pillar": "Risk Sentiment",
        "source": "fred",
        "ticker": "BAMLH0A0HYM2",
        "description": "High Yield credit spread — widening = risk-off",
        "frequency": "Daily",
    },
    "yield_curve": {
        "name": "Yield Curve (10Y - 2Y)",
        "pillar": "Risk Sentiment",
        "source": "fred",
        "ticker": "T10Y2Y",
        "description": "Treasury 10Y minus 2Y spread — inversion = recession signal",
        "frequency": "Daily",
    },
    "vix": {
        "name": "VIX (CBOE Volatility Index)",
        "pillar": "Risk Sentiment",
        "source": "yahoo",
        "ticker": "^VIX",
        "description": "Market fear gauge — high = elevated uncertainty",
        "frequency": "Daily",
    },
}

# ── Signal Classification Thresholds ─────────────────────────────────────────
# Each rule: (indicator_key, field, condition, threshold, signal_value)
# field: "value" = current level, "change_3m" = 3-month change, etc.

SIGNAL_RULES = {
    "global_pmi": {"positive": ("change_3m", ">", 0), "negative": ("change_3m", "<", -1)},
    "ism_manufacturing": {"positive": ("value", ">", 77), "negative": ("value", "<", 72)},
    "unemployment_rate": {"positive": ("change_3m", "<", 0), "negative": ("change_3m", ">", 0.3)},
    "cpi": {"positive": ("change_12m", "<", 0), "negative": ("change_12m", ">", 0.5)},
    "breakeven_10y": {"positive": ("value", "<", 2.5), "negative": ("value", ">", 3.0)},
    "commodity_index": {"positive": ("change_3m", "<", 0), "negative": ("change_3m", ">", 5)},
    "real_interest_rate": {"positive": ("value", "<", 1.0), "negative": ("value", ">", 2.5)},
    "fed_balance_sheet": {"positive": ("change_3m", ">", 0), "negative": ("change_3m", "<", -50000)},
    "financial_conditions": {"positive": ("value", "<", 0), "negative": ("value", ">", 0.5)},
    "credit_spreads": {"positive": ("value", "<", 400), "negative": ("value", ">", 600)},
    "yield_curve": {"positive": ("value", ">", 0.5), "negative": ("value", "<", 0)},
    "vix": {"positive": ("value", "<", 18), "negative": ("value", ">", 28)},
}

# ── Macro Regime Definitions ─────────────────────────────────────────────────
REGIME_RULES = {
    "Expansion": {"growth": 1, "inflation": -1, "liquidity": 1},
    "Reflation": {"growth": 1, "inflation": 1, "liquidity": 1},
    "Stagflation": {"growth": -1, "inflation": 1, "liquidity": -1},
    "Disinflation": {"growth": 0, "inflation": -1, "liquidity": 0},
    "Recession Risk": {"growth": -1, "inflation": 0, "liquidity": -1},
}

# ── Portfolio Implications by Regime ─────────────────────────────────────────
# Each asset class maps to: (underweight, neutral, overweight, commentary)
# Exactly one of underweight/neutral/overweight should be "✦" to mark the active position.

PORTFOLIO_IMPLICATIONS = {
    "Expansion": [
        {"Asset Class": "Equities",    "Underweight": "",  "Neutral": "",  "Overweight": "✦", "Commentary": "Strong earnings growth; favour cyclicals and growth sectors"},
        {"Asset Class": "Bonds",       "Underweight": "",  "Neutral": "✦", "Overweight": "",  "Commentary": "Stable yields; duration neutral, favour IG credit"},
        {"Asset Class": "Commodities", "Underweight": "",  "Neutral": "✦", "Overweight": "",  "Commentary": "Demand supportive but no inflation tailwind"},
        {"Asset Class": "Cash",        "Underweight": "✦", "Neutral": "",  "Overweight": "",  "Commentary": "Opportunity cost high in risk-on environment"},
        {"Asset Class": "Gold",        "Underweight": "",  "Neutral": "✦", "Overweight": "",  "Commentary": "No strong catalyst; hold as portfolio hedge"},
    ],
    "Reflation": [
        {"Asset Class": "Equities",    "Underweight": "",  "Neutral": "",  "Overweight": "✦", "Commentary": "Rising growth + inflation supports value and commodity equities"},
        {"Asset Class": "Bonds",       "Underweight": "✦", "Neutral": "",  "Overweight": "",  "Commentary": "Rising rates erode bond prices; shorten duration"},
        {"Asset Class": "Commodities", "Underweight": "",  "Neutral": "",  "Overweight": "✦", "Commentary": "Inflation and demand tailwinds; energy and industrials benefit"},
        {"Asset Class": "Cash",        "Underweight": "✦", "Neutral": "",  "Overweight": "",  "Commentary": "Real cash returns negative with rising inflation"},
        {"Asset Class": "Gold",        "Underweight": "",  "Neutral": "",  "Overweight": "✦", "Commentary": "Inflation hedge; benefits from negative real rates"},
    ],
    "Stagflation": [
        {"Asset Class": "Equities",    "Underweight": "✦", "Neutral": "",  "Overweight": "",  "Commentary": "Margin compression from rising costs and weak demand"},
        {"Asset Class": "Bonds",       "Underweight": "✦", "Neutral": "",  "Overweight": "",  "Commentary": "Inflation keeps yields elevated; duration risk remains"},
        {"Asset Class": "Commodities", "Underweight": "",  "Neutral": "",  "Overweight": "✦", "Commentary": "Supply-driven inflation supports commodity prices"},
        {"Asset Class": "Cash",        "Underweight": "",  "Neutral": "",  "Overweight": "✦", "Commentary": "Preserve capital; wait for better entry points"},
        {"Asset Class": "Gold",        "Underweight": "",  "Neutral": "",  "Overweight": "✦", "Commentary": "Classic stagflation hedge; safe haven demand rises"},
    ],
    "Disinflation": [
        {"Asset Class": "Equities",    "Underweight": "",  "Neutral": "✦", "Overweight": "",  "Commentary": "Mixed outlook; favour quality and defensive sectors"},
        {"Asset Class": "Bonds",       "Underweight": "",  "Neutral": "",  "Overweight": "✦", "Commentary": "Falling inflation boosts bond prices; extend duration"},
        {"Asset Class": "Commodities", "Underweight": "✦", "Neutral": "",  "Overweight": "",  "Commentary": "Weakening price pressures reduce commodity demand"},
        {"Asset Class": "Cash",        "Underweight": "",  "Neutral": "✦", "Overweight": "",  "Commentary": "Reasonable real yield; maintain tactical flexibility"},
        {"Asset Class": "Gold",        "Underweight": "",  "Neutral": "✦", "Overweight": "",  "Commentary": "Low inflation reduces urgency; hold as diversifier"},
    ],
    "Recession Risk": [
        {"Asset Class": "Equities",    "Underweight": "✦", "Neutral": "",  "Overweight": "",  "Commentary": "Earnings downgrades ahead; reduce risk exposure"},
        {"Asset Class": "Bonds",       "Underweight": "",  "Neutral": "",  "Overweight": "✦", "Commentary": "Flight to safety; long duration Treasuries outperform"},
        {"Asset Class": "Commodities", "Underweight": "✦", "Neutral": "",  "Overweight": "",  "Commentary": "Demand destruction weighs on industrial commodities"},
        {"Asset Class": "Cash",        "Underweight": "",  "Neutral": "",  "Overweight": "✦", "Commentary": "Capital preservation paramount; dry powder for recovery"},
        {"Asset Class": "Gold",        "Underweight": "",  "Neutral": "",  "Overweight": "✦", "Commentary": "Safe haven bid strengthens during risk-off episodes"},
    ],
}
