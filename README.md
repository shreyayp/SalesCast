# SalesCast — Synthetic Sales Forecasting Engine

SalesCast is a reproducible, metadata-driven sales forecasting project that estimates expected bookings from opportunity stages, opportunity age, sales activity, and scenario assumptions. It generates synthetic CRM data, historical forecast snapshots, ground-truth outcomes, validation reports, and SQL/JSON/SQLite exports.

## Features

- Synthetic sales data with deterministic random seed `20261022`
- Master and dependent entities with primary and foreign key relationships
- Historical snapshots across eight quarters
- Opportunity-level weighted forecasts
- Conservative, base, and optimistic scenarios
- Staleness, opportunity-age, and close-date slippage adjustments
- Forecast evaluation using MAE and RMSE
- CSV, JSON, SQL seed, and SQLite exports
- Data validation and database integrity checks

## Project Structure

```text
SalesCast/
├── data/                 # Generated datasets and evaluation results
├── docs/                 # Project documentation and source manifest
├── exports/              # SQL, JSON, and SQLite exports
├── src/
│   ├── data_generator.py
│   ├── forecaster.py
│   ├── export_data.py
│   └── app.py
├── tests/
│   ├── validate_data.py
│   ├── evaluate_forecast.py
│   └── verify_database.py
├── main.py
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10 or later
- pip

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Project

Run commands from the project root.

Generate synthetic data:

```bash
python src/data_generator.py
```

Generate forecasts for conservative, base, and optimistic scenarios:

```bash
python src/forecaster.py
```

Run data validation:

```bash
python tests/validate_data.py
```

Evaluate historical forecasts:

```bash
python tests/evaluate_forecast.py
```

Export SQL, JSON, and SQLite data:

```bash
python src/export_data.py
```

Verify database integrity:

```bash
python tests/verify_database.py
```

Launch the dashboard:

```bash
streamlit run src/app.py
```

## Forecasting Approach

The forecast engine estimates opportunity-level booking probabilities using stage probability assumptions, opportunity age, recent sales activity, staleness adjustments, and close-date slippage. Weighted forecast value is calculated from opportunity amount and adjusted probability.

Three scenarios are supported:

- **Conservative:** reduces the probability and activity assumptions.
- **Base:** uses the default assumptions.
- **Optimistic:** increases the probability and activity assumptions.

Scenario factors are illustrative assumptions, not statistically calibrated probabilities.

## Evaluation

The backtest compares forecast amounts against eventual synthetic booking outcomes. Results include forecast totals, actual bookings, mean absolute error (MAE), and root mean squared error (RMSE), grouped by snapshot date and other supported dimensions.

Evaluation outputs are written to `data/evaluation/`.

## Reproducibility

The generator uses seed `20261022`. Regenerate the datasets with the same seed and compare file checksums to check reproducibility. The forecast as-of date is configured in `src/forecaster.py`.

See [`docs/source_manifest.md`](docs/source_manifest.md) for dataset descriptions, provenance, and limitations.

## Limitations

All data is synthetic. The results demonstrate a forecasting workflow and do not establish real-world predictive accuracy. Ground-truth outcomes must remain separate from features available at the time of each forecast. Currency totals should only be combined when their currencies are consistent or an explicit conversion method is applied.
