
from pathlib import Path
from datetime import date, timedelta
import random
import pandas as pd

SEED = 20261022
TODAY = date(2026, 10, 26)
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data"


def generate_data(
    num_reps=2000,
    num_accounts=2000,
    num_opportunities=20000,
    seed=SEED,
):
    rng = random.Random(seed)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def random_date(start, end):
        if start > end:
            start = end
        days = (end - start).days
        return start + timedelta(days=rng.randint(0, days))

    # 1. Territories
    territories = pd.DataFrame([
        {
            "territory_id": f"TER-{i:03d}",
            "territory_name": f"Territory {i:03d}",
        }
        for i in range(1, 21)
    ])

    # 2. Sales representatives
    reps = pd.DataFrame([
        {
            "rep_id": f"REP-{i:06d}",
            "rep_name": f"Sales Rep {i:06d}",
            "territory_id": f"TER-{((i - 1) % 20) + 1:03d}",
            "hire_date": random_date(
                date(2021, 1, 1), date(2025, 12, 31)
            ).isoformat(),
            "status": rng.choice(["Active", "Active", "Active", "Inactive"]),
        }
        for i in range(1, num_reps + 1)
    ])

    # 3. Accounts
    accounts = pd.DataFrame([
        {
            "account_id": f"ACC-{i:06d}",
            "account_name": f"Account {i:06d}",
            "territory_id": f"TER-{((i - 1) % 20) + 1:03d}",
            "created_date": random_date(
                date(2022, 1, 1), date(2026, 9, 30)
            ).isoformat(),
        }
        for i in range(1, num_accounts + 1)
    ])

    # 4. Sales stages
    stages = pd.DataFrame([
        {"stage_id": "STG-001", "stage_name": "Qualification",
         "probability": 0.20, "stage_order": 1},
        {"stage_id": "STG-002", "stage_name": "Proposal",
         "probability": 0.50, "stage_order": 2},
        {"stage_id": "STG-003", "stage_name": "Negotiation",
         "probability": 0.75, "stage_order": 3},
        {"stage_id": "STG-004", "stage_name": "Closed Won",
         "probability": 1.00, "stage_order": 4},
        {"stage_id": "STG-005", "stage_name": "Closed Lost",
         "probability": 0.00, "stage_order": 5},
    ])

    stage_by_name = stages.set_index("stage_name").to_dict("index")
    stage_choices = ["Qualification", "Proposal", "Negotiation"]

    # 5. Opportunities and latent outcomes
    opportunities = []
    latent_outcomes = {}

    for i in range(1, num_opportunities + 1):
        opportunity_id = f"OPP-2026-{i:06d}"
        account_num = rng.randint(1, num_accounts)
        rep_num = rng.randint(1, num_reps)

        account_id = f"ACC-{account_num:06d}"
        rep_id = f"REP-{rep_num:06d}"

        created = random_date(date(2023, 1, 1), date(2026, 9, 30))
        close_date = random_date(
            created + timedelta(days=1),
            min(created + timedelta(days=240), date(2027, 12, 31)),
        )

               # Generate realistic outcomes for both past and future opportunities.
        if close_date <= TODAY:
            final_stage = rng.choices(
                ["Closed Won", "Closed Lost"],
                weights=[0.55, 0.45],
                k=1,
            )[0]
            actual_close_date = close_date
        else:
            final_stage = rng.choices(
                ["Closed Won", "Closed Lost", *stage_choices],
                weights=[0.30, 0.25, 0.20, 0.15, 0.10],
                k=1,
            )[0]

            if final_stage in ["Closed Won", "Closed Lost"]:
                actual_close_date = close_date
            else:
                actual_close_date = None

        amount = round(rng.uniform(5000, 500000), 2)

        opportunities.append({
            "opportunity_id": opportunity_id,
            "account_id": account_id,
            "rep_id": rep_id,
            "stage_id": stage_by_name[final_stage]["stage_id"],
            "stage_name": final_stage,
            "stage_probability": stage_by_name[final_stage]["probability"],
            "amount": amount,
            "currency": "USD",
            "created_date": created.isoformat(),
            "close_date": close_date.isoformat(),
            "product": rng.choice([
                "Analytics", "Cloud Services", "AI Solutions"
            ]),
        })

        latent_outcomes[opportunity_id] = {
            "final_stage": final_stage,
            "actual_close_date": actual_close_date,
        }

    opportunities = pd.DataFrame(opportunities)

    # 6. Stage history
    stage_history = []
    for opp in opportunities.to_dict("records"):
        created = date.fromisoformat(opp["created_date"])
        final_stage = opp["stage_name"]
        final_close = latent_outcomes[opp["opportunity_id"]]["actual_close_date"]

        stage_history.append({
            "stage_history_id": f"SH-{opp['opportunity_id']}-001",
            "opportunity_id": opp["opportunity_id"],
            "stage_id": "STG-001",
            "changed_at": created.isoformat(),
        })

        if final_stage in ["Proposal", "Negotiation"]:
            stage_history.append({
                "stage_history_id": f"SH-{opp['opportunity_id']}-002",
                "opportunity_id": opp["opportunity_id"],
                "stage_id": stage_by_name[final_stage]["stage_id"],
                "changed_at": random_date(
                    created, date.fromisoformat(opp["close_date"])
                ).isoformat(),
            })
        elif final_stage in ["Closed Won", "Closed Lost"]:
            stage_history.append({
                "stage_history_id": f"SH-{opp['opportunity_id']}-002",
                "opportunity_id": opp["opportunity_id"],
                "stage_id": "STG-002",
                "changed_at": random_date(
                    created, final_close
                ).isoformat(),
            })
            stage_history.append({
                "stage_history_id": f"SH-{opp['opportunity_id']}-003",
                "opportunity_id": opp["opportunity_id"],
                "stage_id": opp["stage_id"],
                "changed_at": final_close.isoformat(),
            })

    stage_history = pd.DataFrame(stage_history)

    # 7. Activities, linked to the opportunity's assigned rep
    activities = []
    activity_types = ["Call", "Email", "Meeting", "Demo"]

    for i, opp in enumerate(opportunities.to_dict("records"), start=1):
        created = date.fromisoformat(opp["created_date"])
        activity_date = random_date(created, TODAY)
        activities.append({
            "activity_id": f"ACT-{i:07d}",
            "opportunity_id": opp["opportunity_id"],
            "rep_id": opp["rep_id"],
            "activity_type": rng.choice(activity_types),
            "activity_date": activity_date.isoformat(),
        })

    activities = pd.DataFrame(activities)

    # 8. Quarterly quotas
    quotas = pd.DataFrame([
        {
            "quota_id": f"QUOTA-{rep_num:06d}-2025Q{quarter}",
            "rep_id": f"REP-{rep_num:06d}",
            "quarter": f"2025Q{quarter}",
            "quota_amount": 250000,
            "currency": "USD",
        }
        for rep_num in range(1, num_reps + 1)
        for quarter in range(1, 5)
    ] + [
        {
            "quota_id": f"QUOTA-{rep_num:06d}-2026Q{quarter}",
            "rep_id": f"REP-{rep_num:06d}",
            "quarter": f"2026Q{quarter}",
            "quota_amount": 250000,
            "currency": "USD",
        }
        for rep_num in range(1, num_reps + 1)
        for quarter in range(1, 5)
    ])

    # 9. Historical bookings only for won opportunities
    won = opportunities[opportunities["stage_name"] == "Closed Won"]
    historical_bookings = pd.DataFrame([
        {
            "booking_id": f"BOOK-{i:07d}",
            "opportunity_id": row["opportunity_id"],
            "rep_id": row["rep_id"],
            "booking_amount": row["amount"],
            "booking_date": latent_outcomes[row["opportunity_id"]][
                "actual_close_date"
            ].isoformat(),
            "currency": row["currency"],
        }
        for i, (_, row) in enumerate(won.iterrows(), start=1)
    ], columns=[
        "booking_id", "opportunity_id", "rep_id",
        "booking_amount", "booking_date", "currency"
    ])

    # 10. Eight quarter-end forecast snapshots.
    # Snapshot records use only opportunities already created by that date.
    snapshot_dates = [
        date(2024, 12, 31),
        date(2025, 3, 31),
        date(2025, 6, 30),
        date(2025, 9, 30),
        date(2025, 12, 31),
        date(2026, 3, 31),
        date(2026, 6, 30),
        date(2026, 9, 30),
    ]

    snapshots = []
    ground_truth = []

    for snapshot_date in snapshot_dates:
        for opp in opportunities.to_dict("records"):
            created = date.fromisoformat(opp["created_date"])
            if created > snapshot_date:
                continue

            outcome = latent_outcomes[opp["opportunity_id"]]
            final_stage = outcome["final_stage"]
            actual_close = outcome["actual_close_date"]

            # Reconstruct a stage that could have been known at this date.
            age_days = (snapshot_date - created).days
            if actual_close is not None and actual_close <= snapshot_date:
                asof_stage = final_stage
            elif age_days >= 120:
                asof_stage = "Negotiation"
            elif age_days >= 60:
                asof_stage = "Proposal"
            else:
                asof_stage = "Qualification"

            probability = stage_by_name[asof_stage]["probability"]
            expected_close = date.fromisoformat(opp["close_date"])
            days_to_close = (expected_close - snapshot_date).days

            # Simple documented scenario adjustments.
            season_factor = 1.10 if snapshot_date.month in (6, 12) else 1.0
            slippage_factor = 0.80 if days_to_close < 0 else 1.0
            forecast_amount = round(
                opp["amount"] * probability * season_factor * slippage_factor,
                2,
            )

            snapshots.append({
                "forecast_snapshot_id": (
                    f"FCST-{snapshot_date.isoformat()}-"
                    f"{opp['opportunity_id']}"
                ),
                "snapshot_date": snapshot_date.isoformat(),
                "opportunity_id": opp["opportunity_id"],
                "stage_id": stage_by_name[asof_stage]["stage_id"],
                "stage_probability": probability,
                "forecast_amount": forecast_amount,
                "currency": opp["currency"],
            })

            
            ground_truth.append({
                "snapshot_date": snapshot_date.isoformat(),
                "opportunity_id": opp["opportunity_id"],
                "actual_stage": final_stage,
                "actual_close_date": (
                    actual_close.isoformat()
                    if actual_close is not None
                    else ""
                ),
                "actual_booking_amount": (
                    opp["amount"] if final_stage == "Closed Won" else 0
                ),
                "currency": opp["currency"],
            })


    forecast_snapshots = pd.DataFrame(snapshots)
    ground_truth = pd.DataFrame(ground_truth)

    # 11. Anomaly labels, separate from normal business tables
    anomalies = []
    for i, opp in enumerate(
        opportunities.sample(
            n=min(100, len(opportunities)),
            random_state=seed,
        ).to_dict("records"),
        start=1,
    ):
        anomalies.append({
            "anomaly_id": f"ANOM-{i:04d}",
            "opportunity_id": opp["opportunity_id"],
            "anomaly_type": rng.choice([
                "stale_opportunity",
                "unusually_high_amount",
                "potential_slippage",
            ]),
            "description": "Synthetic anomaly label for validation and analysis.",
        })

    anomaly_labels = pd.DataFrame(anomalies)

    # 12. Save all generated files
    tables = {
        "territories.csv": territories,
        "sales_reps.csv": reps,
        "accounts.csv": accounts,
        "stages.csv": stages,
        "opportunities.csv": opportunities,
        "stage_history.csv": stage_history,
        "activities.csv": activities,
        "quotas.csv": quotas,
        "historical_bookings.csv": historical_bookings,
        "forecast_snapshots.csv": forecast_snapshots,
        "ground_truth.csv": ground_truth,
        "anomaly_labels.csv": anomaly_labels,
    }

    for filename, table in tables.items():
        table.to_csv(OUTPUT_DIR / filename, index=False)
        print(f"{filename}: {len(table):,} rows")

    print(f"\nSeed: {seed}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("Data generation completed.")


if __name__ == "__main__":
    generate_data()
