from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    base_url: str = Field(..., alias="WSP_BASE_URL")
    username: str = Field(..., alias="WSP_USERNAME")
    password: str = Field(..., alias="WSP_PASSWORD")
    desired_time_local: str = Field("10:00:00.000000", alias="WSP_DESIRED_TIME_LOCAL")

    request_delay: float = Field(0.5, alias="WSP_REQUEST_DELAY")

    retry_delay: float = Field(0.5, alias="WSP_RETRY_DELAY")

    max_retries: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
