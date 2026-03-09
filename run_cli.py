"""
CLI runner — prints macro indicators, signals, and regime to the terminal.
Use this for quick checks without launching the Streamlit dashboard.

Usage: python run_cli.py
"""

from data_pipeline import run_pipeline
from signals import run_signal_engine
from config import PORTFOLIO_IMPLICATIONS


def main():
    # 1. Fetch data and compute trends
    table, raw = run_pipeline()

    # 2. Score signals and classify regime
    scored, pillars, regime = run_signal_engine(table)

    # 3. Print indicator table
    print("=" * 90)
    print("MACRO INDICATOR TABLE")
    print("=" * 90)
    cols = ["indicator", "pillar", "current", "change_3m", "change_12m", "trend_5y", "signal"]
    print(scored[cols].to_string(index=False))

    # 4. Print pillar scores
    print("\n" + "=" * 90)
    print("PILLAR SCORES")
    print("=" * 90)
    for pillar, score in pillars.items():
        direction = "Positive" if score > 0.2 else "Negative" if score < -0.2 else "Neutral"
        print(f"  {pillar:20s}  Score: {score:+.2f}  ({direction})")

    # 5. Print regime
    print("\n" + "=" * 90)
    print(f"MACRO REGIME:  {regime}")
    print("=" * 90)

    # 6. Print portfolio implications
    implications = PORTFOLIO_IMPLICATIONS.get(regime, {})
    print(f"\nPortfolio implications under {regime}:")
    for asset, behaviour in implications.items():
        print(f"  {asset:15s} → {behaviour}")

    print()


if __name__ == "__main__":
    main()
