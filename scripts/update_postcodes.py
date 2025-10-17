#!/usr/bin/env python3
"""
Generate msgpack postcode files from CSV data.

This script downloads the latest UK postcode data from doogal.co.uk and freemaptools.com,
processes it, and generates two msgpack files for efficient loading.

Usage:
    python scripts/update_postcodes.py

The script will:
1. Download postcode CSVs
2. Process and deduplicate postcodes
3. Split into two files based on first letter (a-l and m-z)
4. Generate app/data/postcodes_1.mp and app/data/postcodes_2.mp
"""

import csv
import os
import tempfile
import urllib.request
import zipfile
from math import asin, cos, radians, sin, sqrt

import msgpack

# File prefixes for splitting data
FILE_1_PREF = set('abcdefghijkl')

# Paths
DATA_DIR = 'app/data'
PC_FILE1 = os.path.join(DATA_DIR, 'postcodes_1.mp')
PC_FILE2 = os.path.join(DATA_DIR, 'postcodes_2.mp')


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points on Earth using the Haversine formula."""
    radius = 6372.8 * 1000  # Earth radius in meters
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return radius * c


def download_doogal_postcodes():
    """Download postcodes from doogal.co.uk."""
    url = 'https://www.doogal.co.uk/files/postcodes.zip'
    print(f'Downloading from {url}...')

    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        urllib.request.urlretrieve(url, tmp_file.name)
        print(f'Downloaded to {tmp_file.name}')

        # Extract CSV
        with zipfile.ZipFile(tmp_file.name, 'r') as zip_ref:
            zip_ref.extractall(tempfile.gettempdir())

        csv_path = os.path.join(tempfile.gettempdir(), 'postcodes.csv')
        print(f'Extracted to {csv_path}')
        return csv_path


def process_postcodes():
    """Process postcode data and generate msgpack files."""
    print('Processing postcodes...')

    # Download data
    csv_path = download_doogal_postcodes()

    all_pcs = []

    # Process doogal data (UTF-8 with BOM)
    with open(csv_path, encoding='utf-8-sig') as f:
        csv_reader = csv.DictReader(f)
        for i, row in enumerate(csv_reader):
            if i % 100000 == 0 and i > 0:
                print(f'  Processed {i:,} rows...')

            # Skip terminated postcodes
            if row.get('Terminated'):
                continue

            # Skip rows without required fields
            if not row.get('Postcode') or not row.get('Latitude') or not row.get('Longitude'):
                continue

            pc = row['Postcode'].lower().replace(' ', '')
            try:
                lat = float(row['Latitude'])
                lng = float(row['Longitude'])
            except (ValueError, KeyError):
                continue

            all_pcs.append((pc, lat, lng))

    print(f'Loaded {len(all_pcs):,} postcodes')

    # Split into two files and encode coordinates
    pcs1 = {}
    pcs2 = {}

    print('Encoding coordinates...')
    for i, (pc, lat, lng) in enumerate(all_pcs):
        if i % 100000 == 0 and i > 0:
            print(f'  Encoded {i:,} postcodes...')

        # Verify rounding error is acceptable (< 100m)
        error = haversine(lat, lng, round(lat, 3), round(lng, 3))
        if error >= 100:
            print(f'Warning: Large rounding error for {pc}: {error:.1f}m')
            continue

        # Encode: subtract offsets to make numbers smaller
        encoded = f'{lat - 49.5:.3f} {lng + 8.5:.3f}'

        # Split based on first letter
        if pc and pc[0] in FILE_1_PREF:
            pcs1[pc] = encoded
        else:
            pcs2[pc] = encoded

    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)

    # Save msgpack files
    print(f'Saving {len(pcs1):,} postcodes to {PC_FILE1}...')
    with open(PC_FILE1, 'wb') as f:
        msgpack.pack(pcs1, f)

    print(f'Saving {len(pcs2):,} postcodes to {PC_FILE2}...')
    with open(PC_FILE2, 'wb') as f:
        msgpack.pack(pcs2, f)

    print('\nSuccess! Generated:')
    print(f'  {PC_FILE1} ({os.path.getsize(PC_FILE1) / 1024 / 1024:.1f} MB)')
    print(f'  {PC_FILE2} ({os.path.getsize(PC_FILE2) / 1024 / 1024:.1f} MB)')
    print(f'  Total: {len(pcs1) + len(pcs2):,} postcodes')

    # Cleanup
    try:
        os.remove(csv_path)
    except Exception:
        pass


if __name__ == '__main__':
    process_postcodes()
