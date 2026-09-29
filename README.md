# UK Postcode API

[![CI](https://github.com/tutorcruncher/uk-postcode-api/actions/workflows/ci.yml/badge.svg)](https://github.com/tutorcruncher/uk-postcode-api/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/tutorcruncher/uk-postcode-api/branch/master/graph/badge.svg)](https://codecov.io/gh/tutorcruncher/uk-postcode-api/)

A fast, modern API for geocoding UK postcodes built with FastAPI.

## Features

- **⚡ Fast**: All postcode data loaded into memory for instant O(1) lookups
- **🚀 Modern**: Built with FastAPI, includes automatic OpenAPI documentation
- **📊 Observable**: Integrated with Logfire for monitoring and debugging
- **🔄 Auto-updating**: GitHub Actions automatically updates postcode data weekly
- **✅ Well-tested**: Comprehensive test suite with pytest
- **🛠️ Developer-friendly**: Uses uv for fast dependency management

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/tutorcruncher/uk-postcode-api.git
cd uk-postcode-api

# Install dependencies
make install-dev

# Set your authentication token
export AUTH_TOKEN="your-secret-token-here"

# Generate postcode data files (downloads ~2GB, processes to ~33MB)
make update-postcodes
```

### Running the API

```bash
# Development server with auto-reload
make run-dev

# Or use uvicorn directly
uv run uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000

- **API Documentation**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

### Usage Example

```bash
curl -X POST http://localhost:8000/api/ \
  -H "Authorization: Token your-secret-token-here" \
  -H "Content-Type: application/json" \
  -d '["SW8 5EL", "W1J 7BU", "N7 7AJ"]'
```

Response:
```json
{
  "results": {
    "SW8 5EL": [51.475, -0.121],
    "W1J 7BU": [51.509, -0.143],
    "N7 7AJ": [51.556, -0.118]
  },
  "errors": {}
}
```

## Development

### Available Commands

```bash
make install        # Install production dependencies
make install-dev    # Install with dev dependencies
make test           # Run tests
make test-cov       # Run tests with coverage
make lint           # Check code style
make format         # Format code with ruff
make run-dev        # Run development server
make update-postcodes  # Download and process latest postcode data
make clean          # Clean cache files
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
uv run pytest tests/test_postcodes.py -v
```

### Code Quality

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
make lint

# Auto-fix issues
make format
```

## Deployment

### Heroku

The app is ready to deploy on Heroku:

```bash
# Create Heroku app
heroku create your-app-name

# Set config
heroku config:set AUTH_TOKEN="your-secret-token"

# Deploy
git push heroku master
```

### Environment Variables

- `AUTH_TOKEN` (required): Authentication token for API access
- `SENTRY_DSN` (optional): Sentry DSN for error tracking
- `LOGFIRE_TOKEN` (optional): Logfire token for observability
- `LOGFIRE_ENVIRONMENT` (optional): Environment name (default: development)
- `PORT` (optional): Port to run on (default: 8000)

## Data Sources

The postcode data is sourced from:
- [doogal.co.uk](http://www.doogal.co.uk/UKPostcodes.php) - Primary source

The raw CSV is ~2.0GB uncompressed, but is compressed to just ~33MB using msgpack format (60x compression).

### Data Updates

Postcode data is automatically updated weekly via GitHub Actions. The workflow:
1. Downloads the latest postcode CSV (~2GB)
2. Processes and compresses it to msgpack format (~33MB)
3. Creates a pull request with the updates
4. You review and merge

You can also trigger updates manually:
```bash
make update-postcodes
```

## Architecture

```
uk-postcode-api/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Configuration and logging
│   ├── services/         # Business logic
│   └── data/             # Postcode msgpack files
├── tests/                # Test suite
├── scripts/              # Utility scripts
└── .github/workflows/    # CI/CD automation
```

### Performance

- **Startup**: Loads 1.7M postcodes into memory in ~2 seconds
- **Memory**: ~200MB RAM when all data is loaded (perfect for Heroku 1X with 512MB)
- **Lookup speed**: O(1) dict lookup, typically <1ms per postcode
- **Throughput**: Handles thousands of requests per second

## Migration from Old Version

The API maintains backward compatibility with the original Flask-based API:

- Same endpoint (`/api/`)
- Same request/response format
- Same authentication mechanism
- Just much faster! 🚀

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run `make lint` and `make test`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- [Logfire](https://pydantic.dev/logfire) - Observability platform
- [Ruff](https://github.com/astral-sh/ruff) - Fast Python linter

Original version by TutorCruncher. Modernized in 2024.
