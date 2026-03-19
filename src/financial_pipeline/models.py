from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self) -> str:
        return f"Account(id={self.id}, name={self.name!r}, kind={self.kind!r})"


class Import(Base):
    __tablename__ = "imports"

    id: Mapped[int] = mapped_column(primary_key=True)
    institution: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str | None] = mapped_column(String)
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="import_record")

    def __repr__(self) -> str:
        return f"Import(id={self.id}, institution={self.institution!r}, imported_at={self.imported_at})"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("imports.id"), nullable=False)
    internal_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    external_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    raw_description: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")

    import_record: Mapped[Import] = relationship(back_populates="transactions")
    internal: Mapped[Account] = relationship(foreign_keys=[internal_id])
    external: Mapped[Account] = relationship(foreign_keys=[external_id])

    def __repr__(self) -> str:
        return f"Transaction(id={self.id}, date={self.date}, amount_cents={self.amount_cents}, status={self.status!r})"
