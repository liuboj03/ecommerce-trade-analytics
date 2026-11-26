"""Load the Olist CSV files into a DuckDB database and build the SQL layers."""
from pathlib import Path

import duckdb
import pandas as pd

from . import config


def load_raw(con: duckdb.DuckDBPyConnection, data_dir: Path) -> None:
    missing = [f for f in config.TABLES.values() if not (data_dir / f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing files in {data_dir}: {missing}. See data/README.md for the download steps."
        )
    for table, filename in config.TABLES.items():
        path = (data_dir / filename).as_posix()
        try:
            con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_csv_auto('{path}', header=true)")
        except duckdb.Error:
            # fallback for files with messy quoting (e.g. free-text review comments)
            df = pd.read_csv(path)
            con.register("tmp_df", df)
            con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM tmp_df")
            con.unregister("tmp_df")
        # some versions of the translation file start with a UTF-8 BOM in the header
        for (col,) in con.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'").fetchall():
            clean = col.replace("﻿", "").strip()
            if clean != col:
                con.execute(f'ALTER TABLE {table} RENAME COLUMN "{col}" TO {clean}')


def build_layers(con: duckdb.DuckDBPyConnection) -> None:
    params = {"analysis_start": config.ANALYSIS_START, "analysis_end": config.ANALYSIS_END}
    for sql_file in sorted(config.SQL_DIR.glob("*.sql")):
        con.execute(sql_file.read_text(encoding="utf-8").format(**params))


def row_counts(con: duckdb.DuckDBPyConnection) -> dict:
    tables = list(config.TABLES) + ["dwd_order", "dwd_order_item", "ads_daily_metrics",
                                    "ads_category_month", "ads_review_repurchase", "ads_delivery_review"]
    return {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}
