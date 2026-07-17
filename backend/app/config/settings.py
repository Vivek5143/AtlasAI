from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "InsightForge AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str

    SECRET_KEY: str

    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL_NAME: str = "gemini-2.5-flash"
    CHROMA_DB_PATH: str = "./chroma_db"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    NEWS_API_KEY: str = ""
    RAG_TOP_K: int = 4

    @property
    def EFFECTIVE_GOOGLE_API_KEY(self) -> str:
        """Return the configured Google/Gemini API key."""

        return self.GOOGLE_API_KEY or self.GEMINI_API_KEY

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()