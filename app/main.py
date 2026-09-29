import logging
from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.postcodes import router as postcodes_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.services.postcode_lookup import PostcodeService

configure_logging()
logger = logging.getLogger(__name__)

# Global postcode service instance
postcode_service: PostcodeService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler for startup and shutdown events."""
    global postcode_service

    logger.info('Starting UK Postcode API...')

    # Initialize postcode service with in-memory data
    postcode_service = PostcodeService(settings.postcode_file_1, settings.postcode_file_2)
    logger.info('Postcode service initialized')

    # Store in app state for dependency injection
    app.state.postcode_service = postcode_service

    # Initialize monitoring
    if settings.sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=1.0)
        logger.info('Sentry initialized')

    yield

    # Shutdown
    logger.info('Shutting down UK Postcode API...')


app = FastAPI(
    title='UK Postcode API',
    description="""
    Very simple API for geocoding UK postcodes.
    
    This API takes a list of UK postcodes and returns their coordinates (latitude and longitude).
    
    ## Features
    
    * **Fast Lookups**: All postcode data loaded into memory for instant lookups
    * **Batch Processing**: Look up multiple postcodes in a single request
    * **Comprehensive Coverage**: Covers all UK postcodes
    * **Simple Authentication**: Token-based authentication via Authorization header
    
    ## Authentication
    
    All requests require an authentication token in the Authorization header:
    ```
    Authorization: Token <your_token_here>
    ```
    
    ## Example Usage
    
    ```bash
    curl -X POST http://localhost:8000/api/ \\
      -H "Authorization: Token your-token-here" \\
      -H "Content-Type: application/json" \\
      -d '["SW8 5EL", "W1J 7BU", "N7 7AJ"]'
    ```
    
    ## Data Source
    
    The postcode list is combined from CSV files at:
    - [freemaptools.com](http://www.freemaptools.com/download-uk-postcode-lat-lng.htm)
    - [doogal.co.uk](http://www.doogal.co.uk/UKPostcodes.php)
    """,
    version='1.0.0',
    lifespan=lifespan,
    contact={'name': 'UK Postcode API Support'},
    license_info={'name': 'MIT'},
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Include routers
app.include_router(postcodes_router)


@app.get('/', name='root')
async def root():
    """Root endpoint with API information."""
    return {'message': 'UK Postcode API', 'version': '1.0.0', 'docs': '/docs', 'postcode_endpoint': '/api/'}


@app.get('/health', name='health-check')
async def health_check():
    """Health check endpoint for monitoring."""
    postcode_count = len(postcode_service.postcodes) if postcode_service else 0
    return {'status': 'healthy', 'postcodes_loaded': postcode_count}


# Configure Logfire if token is provided
if settings.logfire_token:
    logfire.configure(
        token=settings.logfire_token, environment=settings.logfire_environment, service_name='uk-postcode-api'
    )
    logfire.instrument_fastapi(app)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('app.main:app', host=settings.host, port=settings.port, reload=True)
