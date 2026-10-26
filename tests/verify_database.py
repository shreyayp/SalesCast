
import sqlite3
from pathlib import Path

DB_PATH = (
    Path(__file__).resolve().parents[1]
    / "exports"
    / "salescast.db"
)

def main():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

        print("DATABASE TABLES:", len(tables))

        for (table_name,) in tables:
            primary_keys = connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()

            pk_columns = [
                row[1] for row in primary_keys if row[5] > 0
            ]

            foreign_keys = connection.execute(
                f'PRAGMA foreign_key_list("{table_name}")'
            ).fetchall()

            print(
                f"{table_name}: "
                f"primary keys={pk_columns}; "
                f"foreign keys={len(foreign_keys)}"
            )

        violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        print("\nFOREIGN KEY VIOLATIONS:", len(violations))
        if violations:
            print(violations[:10])
        else:
            print("All foreign-key relationships are valid.")

if __name__ == "__main__":
    main()
