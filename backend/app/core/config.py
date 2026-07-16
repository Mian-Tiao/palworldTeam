from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """應用程式設定,一律由環境變數讀取(AGENTS.md 機密資訊管理)。

    本地開發預設 SQLite;正式環境由 Render 後台注入 DATABASE_URL 指向 PostgreSQL。
    """

    database_url: str = "sqlite:///./palworld.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
