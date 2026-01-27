import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

from app.core.config import settings
from app.services.postcode_lookup import PostcodeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api', tags=['postcodes'])


class PostcodeResponse(BaseModel):
    results: Dict[str, List[float]]
    errors: Dict[str, str]


def verify_auth_token(authorization: str = Header(None)):
    """Verify the Authorization header contains the correct token."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    token = authorization.replace('Token ', '').replace('Bearer ', '')
    if token != settings.auth_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


def get_postcode_service(request: Request) -> PostcodeService:
    """Dependency to get the postcode service from app state."""
    # Primary method: get from app state (works in all modes once initialized)
    service = getattr(request.app.state, 'postcode_service', None)

    if service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Postcode service not initialized')

    return service


@router.get('/', name='api-index', response_model=Dict[str, str])
async def index():
    """
    GET request returns 405 Method Not Allowed.

    This endpoint only accepts POST requests.
    """
    return {
        'message': 'Please make a post request with postcodes in a JSON list and Authorization header set',
        'status': 'method_not_allowed',
    }


@router.post('/', name='lookup-postcodes', response_model=PostcodeResponse)
async def lookup_postcodes(
    postcodes: List[str], service: PostcodeService = Depends(get_postcode_service), _: None = Depends(verify_auth_token)
) -> Dict[str, Any]:
    """
    Look up coordinates for a list of UK postcodes.

    ## Request Body

    Send a JSON array of postcode strings:
    ```json
    ["SW8 5EL", "N7 7AJ", "W1J 7BU"]
    ```

    ## Response

    Returns an object with two fields:
    - `results`: Dict mapping postcodes to [latitude, longitude] arrays
    - `errors`: Dict mapping invalid postcodes to error messages

    ## Example

    ```bash
    curl -X POST http://localhost:8000/api/ \\
      -H "Authorization: Token your-token-here" \\
      -H "Content-Type: application/json" \\
      -d '["SW8 5EL", "W1J 7BU", "invalid"]'
    ```

    Response:
    ```json
    {
      "results": {
        "SW8 5EL": [51.475, -0.121],
        "W1J 7BU": [51.509, -0.143]
      },
      "errors": {
        "invalid": "No result for 'invalid'"
      }
    }
    ```
    """
    logger.info(f'Looking up {len(postcodes)} postcodes')
    results, errors = service.lookup_batch(postcodes)
    logger.info(f'Found {len(results)} results, {len(errors)} errors. Errors: {errors}')
    return {'results': results, 'errors': errors}
