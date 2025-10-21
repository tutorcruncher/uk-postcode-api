from fastapi.testclient import TestClient

from app.services.postcode_lookup import PostcodeService


class TestPostcodesAPI:
    """Test the postcodes API endpoints."""

    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint returns API information."""
        r = client.get(client.app.url_path_for('root'))
        assert r.status_code == 200
        data = r.json()
        assert data == {
            'message': 'UK Postcode API',
            'version': '1.0.0',
            'docs': '/docs',
            'postcode_endpoint': '/api/',
        }

    def test_health_check(self, client: TestClient):
        """Test the health check endpoint."""
        r = client.get(client.app.url_path_for('health-check'))
        assert r.status_code == 200
        data = r.json()
        assert data['status'] == 'healthy'
        assert 'postcodes_loaded' in data

    def test_api_get_405(self, client: TestClient):
        """Test GET request to API endpoint returns message."""
        r = client.get(client.app.url_path_for('api-index'))
        assert r.status_code == 200
        data = r.json()
        assert data == {
            'message': 'Please make a post request with postcodes in a JSON list and Authorization header set',
            'status': 'method_not_allowed',
        }

    def test_post_403_no_auth(self, client: TestClient):
        """Test POST without auth returns 403."""
        r = client.post(client.app.url_path_for('lookup-postcodes'), json=['SW8 5EL'])
        assert r.status_code == 403

    def test_post_403_wrong_token(self, client: TestClient):
        """Test POST with wrong token returns 403."""
        r = client.post(
            client.app.url_path_for('lookup-postcodes'), json=['SW8 5EL'], headers={'Authorization': 'Token wrong'}
        )
        assert r.status_code == 403

    def test_post_422_invalid_json(self, client: TestClient, auth_headers: dict):
        """Test POST with invalid JSON format returns 422 (FastAPI validation error)."""
        r = client.post(client.app.url_path_for('lookup-postcodes'), json='not a list', headers=auth_headers)
        assert r.status_code == 422

    def test_post_empty_postcode(self, client: TestClient, auth_headers: dict):
        """Test POST with empty postcode returns error."""
        r = client.post(client.app.url_path_for('lookup-postcodes'), json=[''], headers=auth_headers)
        assert r.status_code == 200

        data = r.json()
        assert data == {'results': {}, 'errors': {'': "No result for ''"}}

    def test_post_wrong_postcode(self, client: TestClient, auth_headers: dict):
        """Test POST with invalid postcode returns error."""
        r = client.post(client.app.url_path_for('lookup-postcodes'), json=['abc123'], headers=auth_headers)
        assert r.status_code == 200

        data = r.json()
        assert data == {'results': {}, 'errors': {'abc123': "No result for 'abc123'"}}

    def test_post_correct_postcode(self, client: TestClient, auth_headers: dict):
        """Test POST with valid postcode returns coordinates."""
        r = client.post(client.app.url_path_for('lookup-postcodes'), json=['sw81hl'], headers=auth_headers)
        assert r.status_code == 200

        data = r.json()
        assert data == {'results': {'sw81hl': [51.475, -0.121]}, 'errors': {}}

    def test_post_multiple_correct_postcodes(self, client: TestClient, auth_headers: dict):
        """Test POST with multiple valid postcodes."""
        pcs = ['SW8 5EL', 'N7 7AJ', 'IG10 4QE', 'SW8 5JB', 'DD6 9DD', 'L3 9BE', 'KY99 4BS', 'LL47 6TJ', 'SS2 5JA']

        r = client.post(client.app.url_path_for('lookup-postcodes'), json=pcs, headers=auth_headers)
        assert r.status_code == 200

        data = r.json()
        assert data == {
            'results': {
                'SW8 5EL': [51.479, -0.133],
                'N7 7AJ': [51.554, -0.108],
                'IG10 4QE': [51.637, 0.051],
                'SW8 5JB': [51.477, -0.137],
                'DD6 9DD': [56.448, -2.878],
                'L3 9BE': [53.411, -2.996],
                'KY99 4BS': [56.051, -3.433],
                'LL47 6TJ': [52.903, -4.066],
                'SS2 5JA': [51.544, 0.72],
            },
            'errors': {},
        }

    def test_post_mixed_valid_invalid_postcodes(self, client: TestClient, auth_headers: dict):
        """Test POST with both valid and invalid postcodes."""
        correct_pcs = ['DD6 9DD', 'L3 9BE', 'KY99 4BS', 'LL47 6TJ', 'SS2 5JA']
        incorrect_pcs = ['ABC123', '@!"?A', 'bfoiieo', 'testing', 'SS2 LF4']

        r = client.post(
            client.app.url_path_for('lookup-postcodes'), json=correct_pcs + incorrect_pcs, headers=auth_headers
        )
        assert r.status_code == 200

        data = r.json()
        assert data == {
            'results': {
                'DD6 9DD': [56.448, -2.878],
                'L3 9BE': [53.411, -2.996],
                'KY99 4BS': [56.051, -3.433],
                'LL47 6TJ': [52.903, -4.066],
                'SS2 5JA': [51.544, 0.72],
            },
            'errors': {
                'ABC123': "No result for 'ABC123'",
                '@!"?A': "No result for '@!\"?A'",
                'bfoiieo': "No result for 'bfoiieo'",
                'testing': "No result for 'testing'",
                'SS2 LF4': "No result for 'SS2 LF4'",
            },
        }

    def test_auth_with_bearer_token(self, client: TestClient):
        """Test that Bearer token format also works."""
        r = client.post(
            client.app.url_path_for('lookup-postcodes'), json=['test'], headers={'Authorization': 'Bearer secret-key'}
        )
        assert r.status_code == 200

        data = r.json()
        assert data == {'results': {}, 'errors': {'test': "No result for 'test'"}}


class TestPostcodeService:
    """Test the PostcodeService directly."""

    def test_clean_postcode(self):
        """Test postcode cleaning logic."""
        service = PostcodeService('nonexistent1.mp', 'nonexistent2.mp')

        result = service.lookup('SW8 5EL')
        assert result is None

    def test_batch_lookup_empty_list(self):
        """Test batch lookup with empty list."""
        service = PostcodeService('nonexistent1.mp', 'nonexistent2.mp')
        results, errors = service.lookup_batch([])

        assert results == {}
        assert errors == {}
