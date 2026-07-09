from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "gemma2-9b-it"
    database_url: str = "postgresql+psycopg2://hcp_user:hcp_password@localhost:5432/hcp_crm"
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
