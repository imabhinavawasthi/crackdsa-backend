from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = ""
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        # Avoid error if variables are not provided when app spins up locally for scaffolding
        extra = "ignore" 

settings = Settings()
