from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    PROJECT_NAME: str = "SwipeX API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    # A development value keeps local onboarding simple. Production must supply a
    # high-entropy value through its deployment secret store.
    SECRET_KEY: str = "change-me-before-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    GOOGLE_OAUTH_ENABLED: bool = False
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    # The Vite frontend is deployed separately. Keep the historical static UI
    # opt-in only to avoid serving a stale application from the API process.
    SERVE_LEGACY_UI: bool = False
    # Kept solely to migrate development records created before bcrypt adoption.
    LEGACY_PASSWORD_SALT: str = "swipex_super_secret_jwt_key_2026_antigravity_master"
    
    # Database
    DATABASE_URL: str = "sqlite:///./swipex.db"
    
    # Uploads
    UPLOAD_DIR: str = "./uploads"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def get_database_url(self) -> str:
        """Translate legacy ``postgres://`` to ``postgresql://`` for SQLAlchemy 1.4+."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

settings = Settings()
