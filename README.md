UK Postcode API
===============

Very simple API for geocoding UK postcodes.

It takes a list of postcodes and returns a dictionary mapping those postcodes to latitudes and longitudes.

See `postcodes.py` for an explanation on how to run it. Build with flask and suitable for deployment on Heroku.

The postcode list is combine from the CSV fields at 
http://www.freemaptools.com/download-uk-postcode-lat-lng.htm and http://www.doogal.co.uk/UKPostcodes.php.
