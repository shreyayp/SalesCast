
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
AS_OF_DATE = pd.Timestamp("2026-10-26")

SCENARIOS = {
    "conservative": {
        "probability_factor": 0.85,
        "activity_factor": 0.90,
    },
    "base": {
        "probability_factor": 1.00,
        "activity_factor": 1.00,
    },
    "optimistic": {
        "probability_factor": 1.10,
        "activity_factor": 1.05,
    },
}


def generate_forecast(scenario="base"):
    """Generate an explainable opportunity-level sales forecast."""

    if scenario not in SCENARIOS:
        raise ValueError(
            "Scenario must be conservative, base, or optimistic."
        )

    required_files = [
        "opportunities.csv",
        "activities.csv",
        "historical_bookings.csv",
    ]

    for filename in required_files:
        if not (DATA_DIR / filename).exists():
            raise FileNotFoundError(
                f"Required data file not found: {DATA_DIR / filename}"
            )

    opportunities = pd.read_csv(DATA_DIR / "opportunities.csv")
    activities = pd.read_csv(DATA_DIR / "activities.csv")
    bookings = pd.read_csv(DATA_DIR / "historical_bookings.csv")

    # Parse dates
    opportunities["created_date"] = pd.to_datetime(
        opportunities["created_date"], errors="coerce"
    )
    opportunities["close_date"] = pd.to_datetime(
        opportunities["close_date"], errors="coerce"
    )
    activities["activity_date"] = pd.to_datetime(
        activities["activity_date"], errors="coerce"
    )

    # Calculate opportunity age
    opportunities["age_days"] = (
        AS_OF_DATE - opportunities["created_date"]
    ).dt.days.clip(lower=0)

    # Summarize rep activity for each opportunity using activity records
    activity_summary = (
        activities.groupby("opportunity_id")
        .agg(
            activity_count=("activity_id", "count"),
            last_activity_date=("activity_date", "max"),
        )
        .reset_index()
    )

    opportunities = opportunities.merge(
        activity_summary,
        on="opportunity_id",
        how="left",
        validate="one_to_one",
    )

    opportunities["activity_count"] = (
        opportunities["activity_count"].fillna(0).astype(int)
    )

    opportunities["days_since_activity"] = (
        AS_OF_DATE - opportunities["last_activity_date"]
    ).dt.days

    # Conservative fallback: no recorded activity means stale.
    opportunities["days_since_activity"] = (
        opportunities["days_since_activity"].fillna(9999).clip(lower=0)
    )

        # Only treat an outcome as closed if its close date has passed.
    # This prevents future outcomes from being treated as known today.
    has_closed = opportunities["close_date"] <= AS_OF_DATE

    closed_won = (
        opportunities["stage_name"].eq("Closed Won") & has_closed
    )
    closed_lost = (
        opportunities["stage_name"].eq("Closed Lost") & has_closed
    )
    is_open = ~(closed_won | closed_lost)

    # For open opportunities, estimate stage from age rather than
    # using a potentially future final-stage label.
    base_probability = opportunities["stage_probability"].copy()

    base_probability.loc[is_open & (opportunities["age_days"] < 60)] = 0.20
    base_probability.loc[
        is_open
        & (opportunities["age_days"] >= 60)
        & (opportunities["age_days"] < 120)
    ] = 0.50
    base_probability.loc[
        is_open & (opportunities["age_days"] >= 120)
    ] = 0.75

    base_probability = base_probability.clip(0, 1)

    # Staleness adjustment: older opportunities with no recent activity
    stale = opportunities["days_since_activity"] > 30
    staleness_factor = pd.Series(
        1.0, index=opportunities.index, dtype=float
    )
    staleness_factor.loc[stale] = 0.75

    # Age adjustment: reduce probability for very old open opportunities.
    old_open = is_open & (opportunities["age_days"] > 180)
    staleness_factor.loc[old_open] *= 0.85

    # Slippage adjustment: overdue open opportunities are less likely
    # to close on their currently expected date.
    overdue = is_open & (
        opportunities["close_date"] < AS_OF_DATE
    )
    slippage_factor = pd.Series(
        1.0, index=opportunities.index, dtype=float
    )
    slippage_factor.loc[overdue] = 0.80

    # Scenario-specific assumptions
    assumptions = SCENARIOS[scenario]

    adjusted_probability = (
        base_probability
        * staleness_factor
        * slippage_factor
        * assumptions["probability_factor"]
    )

    # Recorded activity contributes a modest confidence adjustment.
    has_recent_activity = opportunities["days_since_activity"] <= 14
    activity_adjustment = pd.Series(
        1.0, index=opportunities.index, dtype=float
    )
    activity_adjustment.loc[has_recent_activity & is_open] = (
        assumptions["activity_factor"]
    )

    adjusted_probability *= activity_adjustment

    # Closed outcomes are not uncertain pipeline.
    adjusted_probability.loc[closed_won] = 1.0
    adjusted_probability.loc[closed_lost] = 0.0

    # Never allow probabilities outside 0..1.
    opportunities["forecast_probability"] = adjusted_probability.clip(0, 1)

    # Expected bookings per opportunity
    opportunities["weighted_forecast"] = (
        opportunities["amount"] * opportunities["forecast_probability"]
    )

    opportunities["scenario_forecast"] = opportunities["weighted_forecast"]

    # Already-won bookings are shown separately from open pipeline.
    opportunities["open_pipeline_amount"] = (
        opportunities["amount"] * is_open.astype(int)
    )

    opportunities["forecast_category"] = "Open Opportunity"
    opportunities.loc[closed_won, "forecast_category"] = "Closed Won"
    opportunities.loc[closed_lost, "forecast_category"] = "Closed Lost"

    total_pipeline = opportunities.loc[is_open, "amount"].sum()
    weighted_forecast = opportunities.loc[is_open, "weighted_forecast"].sum()
    booked_wins = opportunities.loc[closed_won, "amount"].sum()
    expected_open_bookings = weighted_forecast
    total_expected = booked_wins + expected_open_bookings

    print(f"\nSALESCAST — {scenario.upper()} SCENARIO")
    print("=" * 45)
    print(f"As-of date: {AS_OF_DATE.date()}")
    print(f"Total opportunities: {len(opportunities):,}")
    print(f"Open opportunities: {int(is_open.sum()):,}")
    print(f"Open pipeline: ${total_pipeline:,.2f}")
    print(f"Already closed-won amount: ${booked_wins:,.2f}")
    print(f"Expected bookings from open pipeline: ${expected_open_bookings:,.2f}")
    print(f"Total expected including closed wins: ${total_expected:,.2f}")

    return opportunities



if __name__ == "__main__":
    results = []

    for scenario in ["conservative", "base", "optimistic"]:
        forecast = generate_forecast(scenario)

        results.append({
            "scenario": scenario,
            "expected_bookings": forecast["scenario_forecast"].sum(),
        })

    comparison = pd.DataFrame(results)
    print("\nSCENARIO COMPARISON")
    print("=" * 45)
    print(comparison.to_string(index=False))

    comparison.to_csv(
        DATA_DIR / "scenario_comparison.csv",
        index=False,
    )
    print(f"Saved: {DATA_DIR / 'scenario_comparison.csv'}")
