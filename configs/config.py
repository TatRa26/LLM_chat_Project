import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    model_name: str
    api_url: str
    api_key: str
    postgres_url: str


def load_config() -> Config:
    load_dotenv()

    model_name = os.getenv("MODEL_NAME")
    api_url = os.getenv("API_URL")
    api_key = os.getenv("API_KEY")
    postgres_url = os.getenv("POSTGRES_URL")

    return Config(
        model_name=model_name,
        api_url=api_url,
        api_key=api_key,
        postgres_url=postgres_url
    )
