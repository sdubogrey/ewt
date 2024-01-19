import os


conf = os.environ

BINOTEL_KEY = conf.get('BINOTEL_KEY')
BINOTEL_SECRET = conf.get('BINOTEL_SECRET')
BINOTEL_URL = conf.get('BINOTEL_URL') or 'https://api.binotel.com/api/4.0'

