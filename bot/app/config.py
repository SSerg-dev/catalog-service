from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    telegram_admin_ids: str = ""
    telegram_webhook_url: str = ""
    telegram_webhook_secret: str = "change-me-too"
    web_app_url: str = "http://localhost:3000"
    api_base_url: str = "http://api:8000"
    admin_api_token: str = "change-me"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def admin_ids(self) -> set[int]:
        return {
            int(value.strip())
            for value in self.telegram_admin_ids.split(",")
            if value.strip().isdigit()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

