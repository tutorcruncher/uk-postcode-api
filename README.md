[![Build Status](https://travis-ci.com/tutorcruncher/uk-postcode-api.png)](https://travis-ci.com/tutorcruncher/uk-postcode-api/)
[![codecov](https://codecov.io/gh/tutorcruncher/uk-postcode-api/branch/master/graph/badge.svg)](https://travis-ci.com/tutorcruncher/uk-postcode-api/)

UK Postcode API
===============

Very simple API for geocoding UK postcodes.

It takes a list of postcodes and returns a dictionary mapping those postcodes to latitudes and longitudes.

See `postcodes.py` for an explanation on how to run it. Built with flask and suitable for deployment on Heroku.

The postcode list is combined from the CSV fields at
http://www.freemaptools.com/download-uk-postcode-lat-lng.htm (CSV ukpostcodes.zip) and http://www.doogal.co.uk/UKPostcodes.php (CSV on download dropdown).
