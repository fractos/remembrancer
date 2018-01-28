import os

DATABASE_NAME = os.environ.get('DATABASE_NAME')
DATABASE_HOST = os.environ.get('DATABASE_HOST')
DATABASE_USERNAME = os.environ.get('DATABASE_USERNAME')
DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')

GUARD_WINDOW_DAYS = int(os.environ.get('GUARD_WINDOW_DAYS'))
SLEEP_SECONDS = int(os.environ.get('SLEEP_SECONDS'))
