import logging
import os
from typing import Dict, Tuple

import msgpack

logger = logging.getLogger(__name__)


class PostcodeService:
    """Service for looking up UK postcode coordinates.

    Loads all postcode data into memory on initialization for fastest lookups.

    Memory usage: ~200MB for 1.7M postcodes (fits comfortably in Heroku 1X's 512MB)
    Lookup speed: O(1) - no file I/O during requests
    """

    def __init__(self, file1_path: str, file2_path: str):
        self.postcodes: Dict[str, str] = {}
        self._load_data(file1_path, file2_path)

    def _load_data(self, file1_path: str, file2_path: str):
        """Load both msgpack files into memory and merge into a single dict."""
        logger.info('Loading postcode data into memory...')

        if not os.path.exists(file1_path) or not os.path.exists(file2_path):
            logger.warning(
                f'Postcode data files not found: {file1_path}, {file2_path}. '
                'Run scripts/update_postcodes.py to generate them.'
            )
            return

        with open(file1_path, 'rb') as f:
            data1 = msgpack.unpack(f, use_list=False)
            self.postcodes.update(data1)
            logger.info(f'Loaded {len(data1):,} postcodes from {file1_path}')

        with open(file2_path, 'rb') as f:
            data2 = msgpack.unpack(f, use_list=False)
            self.postcodes.update(data2)
            logger.info(f'Loaded {len(data2):,} postcodes from {file2_path}')

        logger.info(f'Total postcodes loaded: {len(self.postcodes):,}')

    def lookup(self, postcode: str) -> Tuple[float, float] | None:
        """Look up coordinates for a postcode.

        Args:
            postcode: The postcode to look up (e.g., "SW8 5EL" or "sw85el")

        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        clean_pc = postcode.lower().replace(' ', '')

        if not clean_pc:
            return None

        encoded_coords = self.postcodes.get(clean_pc)
        if not encoded_coords:
            return None

        lat_str, lng_str = encoded_coords.split(' ')
        lat = round(float(lat_str) + 49.5, 3)
        lng = round(float(lng_str) - 8.5, 3)

        return lat, lng

    def lookup_batch(self, postcodes: list[str]) -> Tuple[dict, dict]:
        """Look up multiple postcodes at once.

        Args:
            postcodes: List of postcodes to look up

        Returns:
            Tuple of (results_dict, errors_dict)
        """
        results = {}
        errors = {}

        for pc in postcodes:
            coords = self.lookup(pc)
            if coords:
                results[pc] = list(coords)
            else:
                errors[pc] = f"No result for '{pc}'"

        return results, errors
