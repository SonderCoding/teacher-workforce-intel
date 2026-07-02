from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    reddit_client_id: str
    reddit_client_secret: SecretStr
    reddit_user_agent: str
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )