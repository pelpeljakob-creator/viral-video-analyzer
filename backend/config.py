from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DOUBAO_API_KEY: str = ""
    DOUBAO_VISION_ENDPOINT: str = "doubao-1.5-vision-pro-250328"
    DOUBAO_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    DATA_DIR: str = "data"
    DOUYIN_COOKIE_FILE: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
