
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = DATA_DIR / "evaluation"


def evaluate(data, group_columns):
    rows = []

    for keys, group in data.groupby(group_columns, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)

        error = group["forecast_amount"] - group["actual_booking_amount"]

        row = dict(zip(group_columns, keys))
        row.update({
            "opportunities": group["opportunity_id"].nunique(),
            "forecast_total": group["forecast_amount"].sum(),
            "actual_bookings": group["actual_booking_amount"].sum(),
            "mae": error.abs().mean(),
            "rmse": (error.pow(2).mean()) ** 0.5,
        })
        rows.append(row)

    return pd.DataFrame(rows)


def main():
    snapshots = pd.read_csv(DATA_DIR / "forecast_snapshots.csv")
    truth = pd.read_csv(DATA_DIR / "ground_truth.csv")

    snapshots["snapshot_date"] = pd.to_datetime(snapshots["snapshot_date"])
    truth["snapshot_date"] = pd.to_datetime(truth["snapshot_date"])

    truth = truth[
        ["snapshot_date", "opportunity_id", "actual_booking_amount"]
    ]

    data = snapshots.merge(
        truth,
        on=["snapshot_date", "opportunity_id"],
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    unmatched = int((data["_merge"] != "both").sum())
    if unmatched:
        raise ValueError(f"{unmatched} forecast rows lack ground truth.")

    data.drop(columns="_merge", inplace=True)

    for column in ["forecast_amount", "actual_booking_amount"]:
        data[column] = pd.to_numeric(data[column], errors="coerce").fillna(0)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Metrics by snapshot date
    by_snapshot = evaluate(data, ["snapshot_date"])
    by_snapshot["snapshot_date"] = by_snapshot["snapshot_date"].astype(str)
    by_snapshot.to_csv(OUTPUT_DIR / "evaluation_by_snapshot.csv", index=False)

    # Metrics by stage
    if "stage_id" in data.columns:
        evaluate(data, ["stage_id"]).to_csv(
            OUTPUT_DIR / "evaluation_by_stage.csv", index=False
        )

    # Metrics by expected forecast horizon
    close_column = next(
        (c for c in ["expected_close_date", "close_date"] if c in data.columns),
        None,
    )

    if close_column:
        data[close_column] = pd.to_datetime(data[close_column], errors="coerce")
        days = (data[close_column] - data["snapshot_date"]).dt.days

        data["forecast_horizon"] = pd.cut(
            days,
            bins=[-float("inf"), 0, 30, 90, 180, float("inf")],
            labels=["Overdue", "0-30 days", "31-90 days", "91-180 days", "181+ days"],
        )

        evaluate(
            data.dropna(subset=["forecast_horizon"]),
            ["forecast_horizon"],
        ).to_csv(OUTPUT_DIR / "evaluation_by_horizon.csv", index=False)

    # Metrics by available business segments
    segment_columns = [
        c for c in ["territory_id", "region", "market_segment", "product_group", "rep_id"]
        if c in data.columns
    ]

    segment_results = []
    for column in segment_columns:
        result = evaluate(data, [column])
        result.insert(0, "segment_dimension", column)
        result.rename(columns={column: "segment"}, inplace=True)
        segment_results.append(result)

    if segment_results:
        pd.concat(segment_results, ignore_index=True).to_csv(
            OUTPUT_DIR / "evaluation_by_segment.csv", index=False
        )

    print("FORECAST BACKTEST SUMMARY")
    print("=========================")
    print(by_snapshot.to_string(index=False))
    print(f"\nMatched forecast rows: {len(data):,}")
    print(f"Unmatched forecast rows: {unmatched:,}")
    print(f"Evaluation files saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
