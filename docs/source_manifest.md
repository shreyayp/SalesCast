# SalesCast — Source Manifest

## Data Source
All datasets are synthetically generated for the SalesCast sales forecasting challenge. No real customer, employee, or company records are used.

## Reproducibility
- Random seed: `20261022`
- As-of forecast date: `2026-10-26`
- Generator: `src/data_generator.py`
- Forecast engine: `src/forecaster.py`

## Generated Datasets
- `territories.csv` — sales territories
- `sales_reps.csv` — sales representatives
- `accounts.csv` — customer account records
- `stages.csv` — opportunity stages and probabilities
- `opportunities.csv` — sales opportunities
- `stage_history.csv` — opportunity stage-change history
- `activities.csv` — sales activities
- `quotas.csv` — representative quotas by period
- `historical_bookings.csv` — historical booking records
- `forecast_snapshots.csv` — forecasts captured at historical snapshot dates
- `ground_truth.csv` — eventual outcomes used for backtesting
- `anomaly_labels.csv` — records marked for anomaly analysis
- `scenario_comparison.csv` — conservative, base, and optimistic scenario totals

## Data Separation
`ground_truth.csv` is the evaluation target. Eventual outcomes must not be used as features when generating forecasts for an earlier snapshot.

## Currency
Amounts are synthetic and should be interpreted in the currency specified by each record. Totals across currencies must not be combined without an explicit conversion rule.

## Limitations
This is a synthetic demonstration dataset. Forecast accuracy and scenario assumptions do not establish performance on real-world sales data.
