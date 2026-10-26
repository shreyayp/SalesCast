
from pathlib import Path
import json
import sqlite3
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
EXPORT_DIR = ROOT_DIR / "exports"

TABLES = [
    "territories",
    "sales_reps",
    "accounts",
    "stages",
    "opportunities",
    "stage_history",
    "activities",
    "quotas",
    "historical_bookings",
    "forecast_snapshots",
    "ground_truth",
    "anomaly_labels",
]

PRIMARY_KEYS = {
    "territories": ["territory_id"],
    "sales_reps": ["rep_id"],
    "accounts": ["account_id"],
    "stages": ["stage_id"],
    "opportunities": ["opportunity_id"],
    "stage_history": ["stage_history_id"],
    "activities": ["activity_id"],
    "quotas": ["quota_id"],
    "historical_bookings": ["booking_id"],
    "forecast_snapshots": ["forecast_snapshot_id"],
    "ground_truth": ["snapshot_date", "opportunity_id"],
    "anomaly_labels": ["anomaly_id"],
}

FOREIGN_KEYS = {
    "sales_reps": [("territory_id", "territories", "territory_id")],
    "accounts": [("territory_id", "territories", "territory_id")],
    "opportunities": [
        ("account_id", "accounts", "account_id"),
        ("rep_id", "sales_reps", "rep_id"),
        ("stage_id", "stages", "stage_id"),
    ],
    "stage_history": [
        ("opportunity_id", "opportunities", "opportunity_id"),
        ("stage_id", "stages", "stage_id"),
    ],
    "activities": [
        ("opportunity_id", "opportunities", "opportunity_id"),
        ("rep_id", "sales_reps", "rep_id"),
    ],
    "quotas": [("rep_id", "sales_reps", "rep_id")],
    "historical_bookings": [
        ("opportunity_id", "opportunities", "opportunity_id"),
        ("rep_id", "sales_reps", "rep_id"),
    ],
    "forecast_snapshots": [
        ("opportunity_id", "opportunities", "opportunity_id"),
        ("stage_id", "stages", "stage_id"),
    ],
    "ground_truth": [
        ("opportunity_id", "opportunities", "opportunity_id")
    ],
    "anomaly_labels": [
        ("opportunity_id", "opportunities", "opportunity_id")
    ],
}


def load_table(table_name):
    path = DATA_DIR / f"{table_name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return pd.read_csv(path)


def create_schema(connection, table_name, df):
    definitions = [f'"{col}" TEXT' for col in df.columns]

    pk = ", ".join(
        f'"{col}"' for col in PRIMARY_KEYS[table_name]
    )
    definitions.append(f"PRIMARY KEY ({pk})")

    for child_col, parent_table, parent_col in FOREIGN_KEYS.get(
        table_name, []
    ):
        definitions.append(
            f'FOREIGN KEY ("{child_col}") '
            f'REFERENCES "{parent_table}" ("{parent_col}")'
        )

    connection.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    connection.execute(
        f'CREATE TABLE "{table_name}" ({", ".join(definitions)})'
    )


def insert_table(connection, table_name, df):
    columns = list(df.columns)
    column_sql = ", ".join(f'"{col}"' for col in columns)
    placeholders = ", ".join("?" for _ in columns)

    sql = (
        f'INSERT INTO "{table_name}" ({column_sql}) '
        f'VALUES ({placeholders})'
    )

    rows = [
        tuple(None if pd.isna(value) else str(value) for value in row)
        for row in df.itertuples(index=False, name=None)
    ]
    connection.executemany(sql, rows)


def export_sql_seed():
    sql_path = EXPORT_DIR / "salescast_seed.sql"

    # Parent tables must be created before dependent tables.
    with open(sql_path, "w", encoding="utf-8") as sql_file:
        sql_file.write(
            "-- SalesCast synthetic seed data\n"
            "PRAGMA foreign_keys = ON;\n\n"
        )

        for table_name in TABLES:
            df = load_table(table_name)
            definitions = [f'"{col}" TEXT' for col in df.columns]

            pk = ", ".join(
                f'"{col}"' for col in PRIMARY_KEYS[table_name]
            )
            definitions.append(f"PRIMARY KEY ({pk})")

            for child_col, parent_table, parent_col in FOREIGN_KEYS.get(
                table_name, []
            ):
                definitions.append(
                    f'FOREIGN KEY ("{child_col}") '
                    f'REFERENCES "{parent_table}" ("{parent_col}")'
                )

            sql_file.write(f'DROP TABLE IF EXISTS "{table_name}";\n')
            sql_file.write(
                f'CREATE TABLE "{table_name}" '
                f'({", ".join(definitions)});\n'
            )

            columns = list(df.columns)
            column_sql = ", ".join(f'"{col}"' for col in columns)

            for row in df.itertuples(index=False, name=None):
                values = []
                for value in row:
                    if pd.isna(value):
                        values.append("NULL")
                    else:
                        escaped = str(value).replace("'", "''")
                        values.append(f"'{escaped}'")

                sql_file.write(
                    f'INSERT INTO "{table_name}" ({column_sql}) '
                    f'VALUES ({", ".join(values)});\n'
                )

            sql_file.write("\n")

    return sql_path


def main():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Export JSON data.
    all_tables = {}
    for table_name in TABLES:
        df = load_table(table_name)
        all_tables[table_name] = json.loads(
            df.to_json(orient="records", date_format="iso")
        )

    json_path = EXPORT_DIR / "salescast_data.json"
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(all_tables, json_file, indent=2)

    # Export standalone SQL with explicit keys.
    sql_path = export_sql_seed()

    # Export SQLite with explicit keys.
    db_path = EXPORT_DIR / "salescast.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")

        for table_name in TABLES:
            df = load_table(table_name)
            create_schema(connection, table_name, df)
            insert_table(connection, table_name, df)

        connection.commit()

        violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()
        if violations:
            raise ValueError(
                f"SQLite foreign-key violations: {violations[:10]}"
            )

    print("Export completed.")
    print(f"SQL seed: {sql_path}")
    print(f"JSON data: {json_path}")
    print(f"SQLite database: {db_path}")
    print("SQLite foreign-key check passed.")


if __name__ == "__main__":
    main()
