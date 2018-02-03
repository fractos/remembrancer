import os

# home AWS credentials
ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

# SSM parameters
SSM_KEY_PREFIX = os.environ.get("SSM_KEY_PREFIX")

# database details
DATABASE_NAME = os.environ.get('DATABASE_NAME')
DATABASE_HOST = os.environ.get('DATABASE_HOST')
DATABASE_USERNAME = os.environ.get('DATABASE_USERNAME')
DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')

# criteria
GUARD_WINDOW_DAYS = int(os.environ.get('GUARD_WINDOW_DAYS'))

# lifecycle
SLEEP_SECONDS = int(os.environ.get('SLEEP_SECONDS'))
