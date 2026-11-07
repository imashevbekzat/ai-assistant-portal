from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ASSISTANT_", env_file=".env", extra="ignore")

    llm_api_base: str = ""
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_timeout_sec: float = 4.0

    cors_origins: str = "*"
    audit_log_path: str = "logs/audit.jsonl"


settings = Settings()
