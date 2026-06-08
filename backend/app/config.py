from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite+aiosqlite:///./tempo.db"
    openai_api_key: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"
    frontend_url: str = "http://localhost:3000"
    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_redirect_uri: str = "http://localhost:8001/api/v1/strava/callback"
    strava_auto_sync: bool = True
    strava_sync_interval_minutes: int = 60
    garmin_email: str = ""
    garmin_password: str = ""
    garmin_auto_sync: bool = True
    garmin_sync_interval_minutes: int = 60
    garmin_sync_limit: int = 50

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def uses_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def strava_configured(self) -> bool:
        return bool(self.strava_client_id and self.strava_client_secret)

    @property
    def garmin_configured(self) -> bool:
        return bool(self.garmin_email and self.garmin_password)


settings = Settings()
