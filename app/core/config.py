import os
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file='.env', case_sensitive=False)

    # API Settings
    host: str = '0.0.0.0'
    port: int = 8000
    base_url: str = 'http://localhost:8000'

    # Authentication
    auth_token: Optional[str] = None

    # Sentry
    sentry_dsn: Optional[str] = None

    # Logfire
    logfire_token: Optional[str] = None
    logfire_environment: str = 'development'

    # Data files
    postcode_file_1: str = 'app/data/postcodes_1.mp'
    postcode_file_2: str = 'app/data/postcodes_2.mp'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Require auth token except during tests
        if not os.getenv('AUTH_TOKEN') and not kwargs.get('auth_token'):
            raise ValueError('AUTH_TOKEN environment variable must be set')


settings = Settings()
