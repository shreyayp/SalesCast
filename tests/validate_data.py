
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
checks = []


def check(name, condition):
    passed = bool(condition)
    checks.append((name, passed))
    print(f"{'PASS' if passed else 'FAIL'}: {name}")


def load(filename):
    return pd.read_csv(DATA_DIR / filename)


def main():
    print("\nSALESCAST DATA VALIDATION")
    print("=" * 45)

    reps = load("sales_reps.csv")
    accounts = load("accounts.csv")
    territories = load("territories.csv")
    stages = load("stages.csv")
    opps = load("opportunities.csv")
    history = load("stage_history.csv")
    activities = load("activities.csv")
    quotas = load("quotas.csv")
    bookings = load("historical_bookings.csv")
    snapshots = load("forecast_snapshots.csv")
    truth = load("ground_truth.csv")
    anomalies = load("anomaly_labels.csv")

    # Primary keys
    check("Unique rep IDs", reps.rep_id.is_unique)
    check("Unique account IDs", accounts.account_id.is_unique)
    check("Unique territory IDs", territories.territory_id.is_unique)
    check("Unique stage IDs", stages.stage_id.is_unique)
    check("Unique opportunity IDs", opps.opportunity_id.is_unique)
    check("Unique activity IDs", activities.activity_id.is_unique)
    check("Unique quota IDs", quotas.quota_id.is_unique)
    check("Unique booking IDs", bookings.booking_id.is_unique)
    check("Unique snapshot IDs", snapshots.forecast_snapshot_id.is_unique)

    # Required scale
    check("At least 2,000 reps", len(reps) >= 2000)
    check("At least 20,000 opportunities", len(opps) >= 20000)
    check("Exactly 8 snapshot dates", snapshots.snapshot_date.nunique() == 8)

    # Foreign keys
    check("Rep territories valid",
          reps.territory_id.isin(territories.territory_id).all())
    check("Account territories valid",
          accounts.territory_id.isin(territories.territory_id).all())
    check("Opportunity reps valid",
          opps.rep_id.isin(reps.rep_id).all())
    check("Opportunity accounts valid",
          opps.account_id.isin(accounts.account_id).all())
    check("Opportunity stages valid",
          opps.stage_id.isin(stages.stage_id).all())
    check("Activity opportunities valid",
          activities.opportunity_id.isin(opps.opportunity_id).all())
    check("Activity reps valid",
          activities.rep_id.isin(reps.rep_id).all())
    check("Stage history opportunities valid",
          history.opportunity_id.isin(opps.opportunity_id).all())
    check("Stage history stages valid",
          history.stage_id.isin(stages.stage_id).all())
    check("Quota reps valid",
          quotas.rep_id.isin(reps.rep_id).all())
    check("Booking opportunities valid",
          bookings.opportunity_id.isin(opps.opportunity_id).all())
    check("Booking reps valid",
          bookings.rep_id.isin(reps.rep_id).all())
    check("Snapshot opportunities valid",
          snapshots.opportunity_id.isin(opps.opportunity_id).all())
    check("Snapshot stages valid",
          snapshots.stage_id.isin(stages.stage_id).all())
    check("Ground-truth opportunities valid",
          truth.opportunity_id.isin(opps.opportunity_id).all())
    check("Anomaly opportunities valid",
          anomalies.opportunity_id.isin(opps.opportunity_id).all())

    # Valid values and arithmetic
    check("Opportunity amounts non-negative",
          (opps.amount >= 0).all())
    check("Opportunity probabilities within 0-1",
          opps.stage_probability.between(0, 1).all())
    check("Snapshot probabilities within 0-1",
          snapshots.stage_probability.between(0, 1).all())
    check("Forecast amounts non-negative",
          (snapshots.forecast_amount >= 0).all())
    check("Currencies consistently USD",
          opps.currency.eq("USD").all()
          and snapshots.currency.eq("USD").all()
          and bookings.currency.eq("USD").all())

    # Dates and lifecycle
    created = pd.to_datetime(opps.created_date, errors="coerce")
    close = pd.to_datetime(opps.close_date, errors="coerce")
    check("Opportunity dates parse correctly",
          created.notna().all() and close.notna().all())
    check("Close dates after creation",
          (close > created).all())

    activity_dates = pd.to_datetime(activities.activity_date, errors="coerce")
    check("Activity dates parse correctly", activity_dates.notna().all())
    activity_join = activities.merge(
        opps[["opportunity_id", "created_date"]],
        on="opportunity_id",
        how="left",
    )

    activity_dates = pd.to_datetime(
        activity_join["activity_date"], errors="coerce"
    )
    creation_dates = pd.to_datetime(
        activity_join["created_date"], errors="coerce"
    )

    check(
        "Activities not before opportunity creation",
        activity_dates.notna().all()
        and creation_dates.notna().all()
        and (activity_dates >= creation_dates).all()
        and (activity_dates <= pd.Timestamp("2026-10-26")).all(),
    )

    # No duplicate booking per opportunity
    check(
        "At most one booking per opportunity",
        not bookings.opportunity_id.duplicated().any(),
    )

    # Snapshot uniqueness per opportunity and date
    check(
        "No duplicate opportunity snapshots",
        not snapshots.duplicated(
            ["snapshot_date", "opportunity_id"]
        ).any(),
    )

    # Snapshot dates must not precede opportunity creation
    snapshot_join = snapshots.merge(
        opps[["opportunity_id", "created_date"]],
        on="opportunity_id",
        how="left",
    )
    snapshot_dates = pd.to_datetime(snapshot_join.snapshot_date)
    snapshot_created = pd.to_datetime(snapshot_join.created_date)
    check("Snapshots only include already-created opportunities",
          (snapshot_created <= snapshot_dates).all())

    # Booking amount must match its won opportunity
    booking_join = bookings.merge(
        opps[["opportunity_id", "amount", "stage_name"]],
        on="opportunity_id",
        suffixes=("_booking", "_opp"),
    )
    check("Bookings reference Closed Won opportunities",
          booking_join.stage_name.eq("Closed Won").all())
    check("Booking amounts reconcile",
          (booking_join.booking_amount.round(2)
           == booking_join.amount.round(2)).all())

    # Reproducible expected table sizes / basic completeness
    check("Anomaly labels have expected rows",
          len(anomalies) == min(100, len(opps)))
    check("All required tables contain data",
          all(len(df) > 0 for df in [
              reps, accounts, territories, stages, opps,
              history, activities, quotas, bookings,
              snapshots, truth, anomalies
          ]))

           # Required negative-case test helpers
    def negative_test(name, invalid_data, rule):
        check(name, not rule(invalid_data))

    # 1. Duplicate opportunity counted twice
    duplicate_rows = pd.concat(
        [snapshots.head(1), snapshots.head(1)],
        ignore_index=True,
    )
    negative_test(
        "Detect duplicate opportunity snapshot",
        duplicate_rows,
        lambda df: not df.duplicated(
            ["snapshot_date", "opportunity_id"]
        ).any(),
    )

    # 2. Close date before creation date
    invalid_dates = pd.DataFrame({
        "created_date": ["2026-05-10"],
        "close_date": ["2026-05-01"],
    })
    negative_test(
        "Detect close date before creation",
        invalid_dates,
        lambda df: (
            pd.to_datetime(df["close_date"])
            > pd.to_datetime(df["created_date"])
        ).all(),
    )

    # 3. Mixed currencies without conversion
    mixed_currencies = pd.DataFrame({
        "currency": ["USD", "CAD"],
    })
    negative_test(
        "Detect mixed currencies",
        mixed_currencies,
        lambda df: df["currency"].nunique() == 1,
    )

    # 4. Stage probability inconsistent with stage definition
    invalid_probability = pd.DataFrame({
        "stage_name": ["Qualification"],
        "stage_probability": [0.95],
    })
    negative_test(
        "Detect inconsistent stage probability",
        invalid_probability,
        lambda df: df.iloc[0]["stage_probability"]
        == stages.loc[
            stages["stage_name"] == df.iloc[0]["stage_name"],
            "probability",
        ].iloc[0],
    )

    # 5. Final outcome information leaked into a forecast
    invalid_forecast = pd.DataFrame({
        "snapshot_date": ["2025-03-31"],
        "actual_close_date": ["2025-02-01"],
    })
    negative_test(
        "Detect outcome data unavailable at snapshot time",
        invalid_forecast,
        lambda df: (
            pd.to_datetime(df["actual_close_date"])
            > pd.to_datetime(df["snapshot_date"])
        ).all(),
    )
    print("\n" + "=" * 45)
    passed = sum(ok for _, ok in checks)
    failed = len(checks) - passed
    print(f"Passed: {passed}/{len(checks)} checks")
    print(f"Failed: {failed}")

    if failed:
        print("\nSome checks failed. We'll fix these before continuing.")
        raise SystemExit(1)

    print("All current validation checks passed.")


if __name__ == "__main__":
    main()
