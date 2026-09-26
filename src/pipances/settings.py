import tempfile
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PIPANCES_",
        env_file=".env",
        extra="ignore",
    )

    # Application paths. Defaults suit a source checkout; the Nix wrapper,
    # NixOS module, and container image override them for packaged deployments.
    db_path: Path = Path("pipances.db")
    static_dir: Path = Path("static")
    temp_dir: Path = Path(tempfile.gettempdir())

    # Internal structural path (not user-configurable)
    templates_dir: Path = Path(__file__).resolve().parent / "templates"

    # --- Derived properties ---
    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_path}"

    # --- Inbox (Tabulator) ---
    inbox_default_page_size: int = 25
    inbox_page_size_options: list[int] = [25, 50, 100]

    # --- ML hyperparameters ---
    ml_similarity_floor: float = 0.4
    ml_agreement_threshold: float = 0.6

    # --- DuckDB SQL importers ---
    duckdb_threads: int = 2
    duckdb_memory_limit: str = "512MB"
    duckdb_query_timeout_seconds: float = 10.0
    importer_sql_max_length: int = 100_000
    importer_upload_max_bytes: int = 20 * 1024 * 1024
    importer_max_rows: int = 200_000
    importer_preview_display_rows: int = 100
    importer_raw_preview_rows: int = 20


settings = Settings()
