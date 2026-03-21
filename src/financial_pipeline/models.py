from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"Category(id={self.id}, name={self.name!r})"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    starting_balance_cents: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    balance_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", nullable=False
    )

    def __repr__(self) -> str:
        return f"Account(id={self.id}, name={self.name!r}, kind={self.kind!r}, active={self.active})"


class Import(Base):
    __tablename__ = "imports"

    id: Mapped[int] = mapped_column(primary_key=True)
    institution: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str | None] = mapped_column(String)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    row_count: Mapped[int | None] = mapped_column(Integer)

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="import_record"
    )

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
    marked_for_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    ml_confidence_description: Mapped[float | None] = mapped_column(
        Float, nullable=True, default=None
    )
    ml_confidence_category: Mapped[float | None] = mapped_column(
        Float, nullable=True, default=None
    )
    ml_confidence_external: Mapped[float | None] = mapped_column(
        Float, nullable=True, default=None
    )

    import_record: Mapped[Import] = relationship(back_populates="transactions")
    internal: Mapped[Account] = relationship(foreign_keys=[internal_id])
    external: Mapped[Account] = relationship(foreign_keys=[external_id])
    category: Mapped[Category | None] = relationship()

    def __repr__(self) -> str:
        return f"Transaction(id={self.id}, date={self.date}, amount_cents={self.amount_cents}, status={self.status!r})"
