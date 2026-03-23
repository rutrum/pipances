"""Importer for Metro Credit Union CSV exports.

Format: split debit/credit columns with MM/DD/YYYY dates.

    Transaction Date,Debit,Credit,Memo
    02/15/2026,,2800.00,EMPLOYER DIRECT DEP
    02/16/2026,87.43,,KROGER #1234
"""

import io

import polars as pl

IMPORTER_NAME = "Metro Credit Union"


def parse(blob: bytes) -> pl.DataFrame:
    df = pl.read_csv(io.BytesIO(blob))
    return df.select(
        pl.col("Transaction Date").str.strptime(pl.Date, "%m/%d/%Y").alias("date"),
        (
            pl.when(pl.col("Credit").is_not_null())
            .then(pl.col("Credit").cast(pl.Decimal(38, 2)))
            .otherwise(-pl.col("Debit").cast(pl.Decimal(38, 2)))
        ).alias("amount"),
        pl.col("Memo").cast(pl.String).alias("description"),
    )
