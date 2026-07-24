from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AtlasAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str

    SECRET_KEY: str

    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL_NAME: str = "gemini-3.5-flash"
    CHROMA_DB_PATH: str = "./chroma_db"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    NEWS_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    INITIAL_ADMIN_EMAIL: str = ""
    INITIAL_ADMIN_PASSWORD: str = ""
    INITIAL_ADMIN_USERNAME: str = "admin"
    NEWS_SYNC_LOOKBACK_DAYS: int = 7
    NEWS_SYNC_MAX_COMPANIES_PER_REFRESH: int = 25
    NEWS_SYNC_PAGE_SIZE: int = 10
    NEWS_SYNC_ROTATION_WINDOW_MINUTES: int = 60
    NEWS_SYNC_MARKET_KEYWORDS: str = (
        "AI,artificial intelligence,machine learning,automation,investment,"
        "funding,acquisition,partnership,launch,technology,expansion,contract,deployment"
    )
    NEWS_SYNC_BLOCKED_DOMAINS: str = "pypi.org,npmjs.com,registry.npmjs.org"
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