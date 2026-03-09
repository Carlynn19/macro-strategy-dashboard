"""
CLI runner — prints macro indicators, signals, and regime to the terminal.
Use this for quick checks without launching the Streamlit dashboard.

Usage: python run_cli.py
"""

from data_pipeline import run_pipeline
from signals import run_signal_engine
from config import PORTFOLIO_IMPLICATIONS, REGIONS


def main():
    # 1. Fetch data and compute trends
    table, raw, regional_table, regional_raw = run_pipeline()

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
    implications = PORTFOLIO_IMPLICATIONS.get(regime, [])
    if implications:
        print(f"\nPortfolio implications under {regime}:")
        for row in implications:
            position = "Overweight" if row["Overweight"] == "✦" else "Underweight" if row["Underweight"] == "✦" else "Neutral"
            print(f"  {row['Asset Class']:15s} → {position:12s}  {row['Commentary']}")
    else:
        print(f"\nNo portfolio implications defined for {regime}")

    # 7. Print regional macro indicators
    print("\n" + "=" * 90)
    print("REGIONAL MACRO MONITOR")
    print("=" * 90)
    for region in REGIONS:
        region_df = regional_table[regional_table["region"] == region]
        if not region_df.empty:
            print(f"\n  ── {region} {'─' * (70 - len(region))}")
            rcols = ["indicator", "current", "change_3m", "change_12m", "trend_5y"]
            print(region_df[rcols].to_string(index=False))

    print()


if __name__ == "__main__":
    main()
