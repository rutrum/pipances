from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PIPANCES_",
        env_file=".env",
        extra="ignore",
    )

    # Application paths
    db_path: Path
    static_dir: Path
    importers_dir: Path
    temp_dir: Path

    # Internal structural path (not user-configurable)
    templates_dir: Path = (
        Path(__file__).resolve().parent.parent.parent / "src" / "pipances" / "templates"
    )

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


settings = Settings()
