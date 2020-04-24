import os
import sys
import binascii
import msgpack
import logging
import sentry_sdk

from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest
from sentry_sdk.integrations.flask import FlaskIntegration


sentry_sdk.init(
    dsn='https://0f2f0bcedfa14cfe9c788179b51173b3@sentry.io/1495275',
    integrations=[FlaskIntegration()]
)


app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler())

# We have to split the postcode list into two files and access them one at a time to avoid
# exceeding Heroku's memory limits.
PC_FILE1 = os.path.join(os.path.dirname(__file__), 'postcodes_1.mp')
PC_FILE2 = os.path.join(os.path.dirname(__file__), 'postcodes_2.mp')
FILE_1_PREF_B = set(b'abcdefghijkl')
FILE_1_PREF = set('abcdefghijkl')


class PostcodeDatabase(object):
    def __init__(self):
        self._data_file = None
        self._data = None

    def get_dict(self, clean_pc):
        if clean_pc[0] in FILE_1_PREF_B:
            if self._data_file != PC_FILE1:
                self._load_file(PC_FILE1)
        else:
            if self._data_file != PC_FILE2:
                self._load_file(PC_FILE2)
        return self._data

    def _load_file(self, file_name):
        del self._data
        self._data = msgpack.unpack(open(file_name, 'rb'), use_list=False)
        self._data_file = file_name


postcode_database = PostcodeDatabase()


class PCException(Exception):
    pass


class PostcodeLookup(object):
    def __init__(self, postcodes):
        # sort so we only have to open each of the files once
        postcodes = sorted(postcodes, key=self._clean)
        self.results = {}
        self.errors = {}
        for pc in postcodes:
            self._lookup_postcode(pc)

    def _lookup_postcode(self, pc):
        clean_pc = self._clean(pc).encode()
        try:
            if clean_pc == b'':
                raise PCException()
            data = postcode_database.get_dict(clean_pc)
            try:
                coords = data[clean_pc].decode()
            except KeyError:
                raise PCException()
            else:
                lat, lng = coords.split(' ')
                lat, lng = round(float(lat) + 49.5, 3), round(float(lng) - 8.5, 3)
                self.results[pc] = (lat, lng)
        except PCException:
            self.errors[pc] = "No result for '%s'" % pc

    @staticmethod
    def _clean(s):
        return s.lower().replace(' ', '')


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    The main (and only) end point of the api.

    Usage:
    curl -X POST -d '["BS8 4EJ", "W1J 7BU"]' http://127.0.0.1:5000/ -H 'Authorization: Token <token>'
    """
    if request.method == 'GET':
        return 'Please make a post request with postcodes in a JSON list and Authorization header set\n', 405
    token = request.headers.get('Authorization', '')
    if token.replace('Token ', '') != AUTH_TOKEN:
        return 'Please insert coin\n', 403
    try:
        pcs = request.get_json(force=True)
    except BadRequest:
        return 'Invalid JSON, please check your syntax\n', 400
    if not isinstance(pcs, list):
        return 'The JSON you submit should be a simple list of postcodes\n', 400
    lookup = PostcodeLookup(pcs)
    return jsonify(results=lookup.results, errors=lookup.errors)


def generate_token():
    """
    Utility function to generate an auth token.

    Note this is not to be run in production but is instead a quick method of creating an authentication token
    you can then transfer to the server and set as an environment variable yourself.
    """
    token = binascii.hexlify(os.urandom(20)).decode()
    print(f'New token generated: AUTHKEY="{token}"')


def generate_msgpack():
    """
    Generate 'postcodes_X.mp' msg pack files, this is a utility and shouldn't be required as files are included in the
    repo.

    To use it you need to download a full list of uk postcodes csv file from
    from http://www.freemaptools.com/download-uk-postcode-lat-lng.htm
    and http://www.doogal.co.uk/UKPostcodes.php
    """
    # loaded locally as only required here
    from math import radians, sin, cos, sqrt, asin
    import csv

    def haversine(lat1, lon1, lat2, lon2):
        radius = 6372.8 * 1000  # Earth radius in meters
        d_lat = radians(lat2 - lat1)
        d_lon = radians(lon2 - lon1)
        lat1 = radians(lat1)
        lat2 = radians(lat2)
        a = sin(d_lat/2)**2 + cos(lat1)*cos(lat2)*sin(d_lon/2)**2
        c = 2*asin(sqrt(a))
        return radius * c

    all_pcs = []
    with open('freemaptools_postcodes.csv') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)  # heading
        for i, row in enumerate(csv_reader):
            pc = row[1]
            pc = pc.lower().replace(' ', '')
            lat = row[2]
            lng = row[3]
            if not lat or not lng:
                continue
            all_pcs.append((pc, float(lat), float(lng)))
    with open('doogle_postcodes.csv') as f:
        csv_reader = csv.DictReader(f)
        for i, row in enumerate(csv_reader):
            if row['Terminated']:
                continue
            pc = row['Postcode'].lower().replace(' ', '')
            lat = float(row['Latitude'])
            lng = float(row['Longitude'])
            all_pcs.append((pc, lat, lng))

    pcs1 = {}
    pcs2 = {}
    for pc, lat, lng in all_pcs:
        error = haversine(lat, lng, round(lat, 3), round(lng, 3))
        assert error < 100
        if pc[0] in FILE_1_PREF:
            pcs1[pc] = '%0.3f %0.3f' % (lat - 49.5, lng + 8.5)
        else:
            pcs2[pc] = '%0.3f %0.3f' % (lat - 49.5, lng + 8.5)
    msgpack.pack(pcs1, open(PC_FILE1, 'wb'))
    msgpack.pack(pcs2, open(PC_FILE2, 'wb'))
    print(f'saved {len(pcs1)} and {len(pcs2)} postcodes to {PC_FILE1} and {PC_FILE2} respectively')


def try_postcodes():
    """
    Allows you to try out the postcode api either locally or on a server.

    run with "python postcodes.py try [postcodes to try]"
    """
    import requests
    import json
    from pprint import pprint
    dft_url = 'http://127.0.0.1:5000/'
    url = input(
        f'Enter URL to make requests to (default is "{dft_url}" but you need to be running the sever locally): '
    ) or dft_url
    dft_token = 'testing'
    token = input(f'Enter token to use (dft "{dft_token}"); ') or dft_token
    cli_pcs = ', '.join(sys.argv[2:])
    pcs = input(f'Enter comma separated list of postcodes to try (default "{cli_pcs}"): ') or cli_pcs
    pcs = [pc.strip(', ') for pc in pcs.split(',')]
    data = json.dumps(pcs)
    r = requests.post(url, data=data, headers={'Authorization': f'Token {token}'})
    print(f'response status: {r.status_code}')
    if r.status_code != 200:
        print('bad response code, exiting')
        return
    result = r.json()
    print('content:')
    pprint(result)


AUTH_TOKEN = os.getenv('AUTH_TOKEN')
args, commands = ' '.join(sys.argv), ['generate_token', 'generate_msgpack', 'try']
if AUTH_TOKEN is None and all(cmd not in args for cmd in commands):
    raise Exception('You need to defined "AUTH_TOKEN" as an environment variable.')


if __name__ == '__main__':
    if 'generate_token' in args:
        generate_token()
    elif 'generate_msgpack' in args:
        generate_msgpack()
    elif 'try' in args:
        try_postcodes()
    else:
        # debug is ok here as it's only used for testing, in production gunicorn is used
        app.run(debug=True)
