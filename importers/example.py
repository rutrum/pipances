"""Example importer for a simple CSV with columns: date, amount, description.

This serves as a reference for writing institution-specific importers.
"""

import io

import polars as pl

IMPORTER_NAME = "Example Bank"


def parse(blob: bytes) -> pl.DataFrame:
    df = pl.read_csv(io.BytesIO(blob))
    return df.select(
        pl.col("date").str.strptime(pl.Date, "%Y-%m-%d"),
        pl.col("amount").cast(pl.Decimal(38, 2)),
        pl.col("description").cast(pl.String),
    )
