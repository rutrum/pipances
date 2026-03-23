from datetime import date

import patito as pt
import polars as pl


class ImportedTransaction(pt.Model):
    date: date
    amount: float = pt.Field(dtype=pl.Decimal(38, 2))
    description: str
