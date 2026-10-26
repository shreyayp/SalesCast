# AI Prompt History — SalesCast

This file summarizes the AI assistance used during development of SalesCast. It documents the main tasks, implementation changes, and review responsibilities. These are prompt summaries, not verbatim transcripts of every interaction.

## 1. Project Structure and Synthetic Data Generation

**Purpose:** Design a reproducible synthetic sales forecasting dataset with related entities.

**Prompt summary:** Help me plan and implement a Python project for a sales forecasting challenge. Generate sales representatives, territories, accounts, opportunities, stages, stage history, activities, quotas, historical bookings, forecast snapshots, separate ground-truth outcomes, and anomaly labels. Use a fixed random seed, valid relationships, realistic dates, and configurable dataset sizes.

**Implementation:** Created and iteratively updated `src/data_generator.py`. Generated CSV datasets under `data/` using seed `20261022`.

## 2. Data Integrity and Negative-Case Validation

**Purpose:** Check that generated datasets satisfy structural and business rules.

**Prompt summary:** Help me validate primary keys, foreign keys, stage probabilities, enumerated values, non-negative amounts, date ordering, snapshot uniqueness, booking reconciliation, and required dataset sizes. Add negative-case checks for duplicate opportunity snapshots, invalid close dates, mixed currencies, inconsistent stage probabilities, and outcome information unavailable at forecast time.

**Implementation:** Updated `tests/validate_data.py` with data-integrity checks and negative-case test helpers. The validation script previously reported 49/49 checks passing.

**Review note:** Negative-case tests should be reviewed to confirm that each test genuinely exercises the corresponding failure condition, rather than only checking a simplified example.

## 3. Explainable Forecasting Engine

**Purpose:** Estimate expected bookings using transparent assumptions.

**Prompt summary:** Help me implement an opportunity-level sales forecast using stage probability, opportunity age, sales activity recency, close-date slippage, and conservative, base, and optimistic scenarios. Avoid treating future outcomes as already known at the forecast date.

**Implementation:** Created and updated `src/forecaster.py`. The current approach uses heuristic probability adjustments and scenario multipliers; it is not a trained machine-learning model.

## 4. Scenario Comparison

**Purpose:** Compare expected bookings under different assumptions.

**Prompt summary:** Help me run the conservative, base, and optimistic forecasting scenarios and save their expected booking totals to a CSV file.

**Implementation:** Updated `src/forecaster.py` to run all three scenarios and save the comparison to `data/scenario_comparison.csv`.

## 5. Forecast Backtesting and Evaluation

**Purpose:** Measure forecast errors against synthetic eventual outcomes.

**Prompt summary:** Help me evaluate forecast snapshots against separate ground-truth records. Calculate forecast totals, actual bookings, mean absolute error (MAE), and root mean squared error (RMSE), with breakdowns by snapshot date, stage, forecast horizon, and available business segments.

**Implementation:** Updated `tests/evaluate_forecast.py`. The evaluation previously completed with 122,363 matched forecast rows and zero unmatched rows. The metrics are backtest results on synthetic data, not evidence of real-world predictive performance.

## 6. Database and Data Exports

**Purpose:** Provide portable, structured project outputs.

**Prompt summary:** Help me export generated datasets into SQL seed data, JSON, and SQLite, while defining primary and foreign keys and checking database integrity.

**Implementation:** Created and updated `src/export_data.py`. Generated `exports/salescast_seed.sql`, `exports/salescast_data.json`, and `exports/salescast.db`. The database verification script previously reported 12 tables and zero foreign-key violations.

## 7. Interactive Dashboard

**Purpose:** Present forecasting results through a user interface.

**Prompt summary:** Help me build a Streamlit dashboard displaying pipeline and forecast information, scenario results, stage breakdowns, opportunity search, and CSV export.

**Implementation:** Created `src/app.py` and configured the application dependencies in `requirements.txt`. Dashboard behaviour should be verified against the final generated data and current forecast logic.

## 8. Documentation and Source Manifest

**Purpose:** Explain how to install, run, reproduce, and assess the project.

**Prompt summary:** Help me document the project structure, installation, generator and forecast commands, validation and evaluation scripts, data provenance, reproducibility settings, modelling assumptions, and limitations.

**Implementation:** Updated `README.md` and created `docs/source_manifest.md`. The manifest documents the synthetic data source, random seed, as-of date, generated datasets, data separation, currency considerations, and limitations.

## 9. Reproducibility and Final Review

**Purpose:** Prepare the project for independent review and submission.

**Prompt summary:** Help me run the project checks, regenerate exports, verify reproducibility using checksums, confirm that documentation matches implementation, and prepare the repository for publication.

**Implementation:** Reproducibility checks and the final end-to-end review remain subject to confirmation after the latest changes. Public GitHub publication must also be confirmed separately.

## Review and Accountability

AI assistance was used to draft and revise code, tests, and documentation. The author is responsible for reviewing the implementation, verifying the final outputs, understanding the forecasting assumptions, and ensuring the documentation accurately describes the delivered project.

This document contains summarized descriptions of the assistance used; it is not a verbatim record of all prompts or tool calls. Where complete prompt history is required by the challenge, the original prompts and tools should be recorded accurately rather than reconstructed from summaries.
