import os
import json

os.environ['AUTH_TOKEN'] = 'testing'

from postcodes import app, generate_token
from unittest import TestCase, mock


class PostcodesTestCase(TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_get_405(self):
        r = self.client.get('/')
        assert r.status_code == 405

    def test_post_403(self):
        r = self.client.post('/')
        assert r.status_code == 403

    def test_post_with_token_400(self):
        r = self.client.post('/', headers={'Authorization': 'Token testing'})
        assert r.status_code == 400

    def test_json_not_list_400(self):
        r = self.client.post(
            '/',
            data=json.dumps('test'),
            headers={'Authorization': 'Token testing'},
            content_type='application/json',
        )
        assert r.status_code == 400

    def test_post_postcode_with_correct_result(self):
        r = self.client.post(
            '/',
            data=json.dumps(['sw81hl']),
            headers={'Authorization': 'Token testing'},
            content_type='application/json',
        )
        assert r.status_code == 200

        data = json.loads(r.data)
        assert data['results']['sw81hl']
        assert data['results']['sw81hl'] == [51.475, -0.121]

    def test_post_empty_postcode(self):
        r = self.client.post(
            '/',
            data=json.dumps(['']),
            headers={'Authorization': 'Token testing'},
            content_type='application/json',
        )
        assert r.status_code == 200

        data = json.loads(r.data)
        assert data['errors']['']
        assert data['errors'][''] == "No result for ''"

    def test_post_wrong_postcode_with_error(self):
        r = self.client.post(
            '/',
            data=json.dumps(['abc123']),
            headers={'Authorization': 'Token testing'},
            content_type='application/json',
        )
        assert r.status_code == 200

        data = json.loads(r.data)
        assert data['errors']['abc123']
        assert data['errors']['abc123'] == "No result for 'abc123'"

    def test_post_multiple_correct_postcodes(self):
        pcs = ['SW8 5EL', 'N7 7AJ', 'IG10 4QE', 'SW8 5JB', 'DD6 9DD', 'L3 9BE', 'KY99 4BS', 'LL47 6TJ', 'SS2 5JA']

        r = self.client.post(
            '/',
            data=json.dumps(pcs),
            headers={'Authorization': 'Token testing'},
            content_type='application/json',
        )
        assert r.status_code == 200

        data = json.loads(r.data)
        for pc in pcs:
            assert data['results'][pc]

    def test_post_some_wrong_some_correct_postcodes(self):
        correct_pcs = ['DD6 9DD', 'L3 9BE', 'KY99 4BS', 'LL47 6TJ', 'SS2 5JA']
        incorrect_pcs = ['ABC123', '@!"?A', 'bfoiieo', 'testing', 'SS2 LF4']

        r = self.client.post(
            '/',
            data=json.dumps(correct_pcs + incorrect_pcs),
            headers={'Authorization': 'Token testing'},
            content_type='application/json',
        )
        assert r.status_code == 200

        data = json.loads(r.data)
        for pc in correct_pcs:
            assert data['results'][pc]

        for pc in incorrect_pcs:
            assert data['errors'][pc]


class GenerateTokenTestCase(TestCase):

    @mock.patch('builtins.print')
    @mock.patch('binascii.hexlify')
    def test_generate_token(self, mock_token, mock_print):
        mock_token.return_value = b'abc123'
        generate_token()
        assert mock_print.mock_calls == [mock.call('New token generated: AUTHKEY="abc123"')]
