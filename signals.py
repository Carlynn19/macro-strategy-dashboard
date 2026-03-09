"""
Signal Classification & Macro Regime Engine.
Scores each indicator, aggregates pillar scores, and classifies the macro regime.
"""

import pandas as pd
import numpy as np
from config import SIGNAL_RULES, REGIME_RULES, INDICATORS


# ── Signal Scoring ───────────────────────────────────────────────────────────

def score_indicator(row: pd.Series) -> int:
    """
    Score a single indicator row as +1 (positive), 0 (neutral), or -1 (negative).
    Uses threshold rules from config.SIGNAL_RULES.
    """
    key = row["key"]
    if key not in SIGNAL_RULES:
        return 0

    rules = SIGNAL_RULES[key]

    # Check positive condition
    pos_field, pos_op, pos_thresh = rules["positive"]
    val_pos = row.get(pos_field if pos_field == "value" else pos_field, np.nan)
    if pos_field == "value":
        val_pos = row.get("current", np.nan)

    # Check negative condition
    neg_field, neg_op, neg_thresh = rules["negative"]
    val_neg = row.get(neg_field if neg_field == "value" else neg_field, np.nan)
    if neg_field == "value":
        val_neg = row.get("current", np.nan)

    # Evaluate positive
    if not np.isnan(val_pos):
        if pos_op == ">" and val_pos > pos_thresh:
            return 1
        if pos_op == "<" and val_pos < pos_thresh:
            return 1

    # Evaluate negative
    if not np.isnan(val_neg):
        if neg_op == ">" and val_neg > neg_thresh:
            return -1
        if neg_op == "<" and val_neg < neg_thresh:
            return -1

    return 0


def add_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'signal' column (+1/0/-1) to the indicator table."""
    df = df.copy()
    df["signal"] = df.apply(score_indicator, axis=1)
    return df


# ── Pillar Scores ────────────────────────────────────────────────────────────

def compute_pillar_scores(df: pd.DataFrame) -> dict[str, float]:
    """
    Average the signal scores within each pillar.
    Returns dict: {"Growth": 0.67, "Inflation": -0.33, ...}
    """
    scores = {}
    for pillar in ["Growth", "Inflation", "Liquidity", "Risk Sentiment"]:
        subset = df[df["pillar"] == pillar]
        if len(subset) > 0:
            scores[pillar] = round(subset["signal"].mean(), 2)
        else:
            scores[pillar] = 0.0
    return scores


def classify_pillar_direction(score: float) -> int:
    """Map a continuous pillar score to -1, 0, or +1."""
    if score > 0.2:
        return 1
    elif score < -0.2:
        return -1
    return 0


# ── Macro Regime Classification ──────────────────────────────────────────────

def classify_regime(pillar_scores: dict[str, float]) -> str:
    """
    Match pillar directions to the closest regime template in REGIME_RULES.
    Uses simple distance metric (sum of absolute differences).
    """
    growth_dir = classify_pillar_direction(pillar_scores.get("Growth", 0))
    inflation_dir = classify_pillar_direction(pillar_scores.get("Inflation", 0))
    liquidity_dir = classify_pillar_direction(pillar_scores.get("Liquidity", 0))

    current = {"growth": growth_dir, "inflation": inflation_dir, "liquidity": liquidity_dir}

    best_regime = "Disinflation"  # default fallback
    best_distance = float("inf")

    for regime, template in REGIME_RULES.items():
        distance = sum(abs(current[k] - template[k]) for k in template)
        if distance < best_distance:
            best_distance = distance
            best_regime = regime

    return best_regime


# ── Convenience ──────────────────────────────────────────────────────────────

def run_signal_engine(df: pd.DataFrame) -> tuple[pd.DataFrame, dict, str]:
    """
    Full signal pipeline:
      1. Score each indicator
      2. Compute pillar scores
      3. Classify macro regime
    Returns (scored_df, pillar_scores, regime_label).
    """
    scored = add_signals(df)
    pillars = compute_pillar_scores(scored)
    regime = classify_regime(pillars)
    return scored, pillars, regime
