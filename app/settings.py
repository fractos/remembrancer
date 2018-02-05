import os

# home AWS credentials
ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION")

# SSM parameters
SSM_KEY_PREFIX = os.environ.get("SSM_KEY_PREFIX")
KMS_KEY_ALIAS = os.environ.get("KMS_KEY_ALIAS")

# database details
DATABASE_TABLE = os.environ.get('DATABASE_TABLE')

# criteria
GUARD_WINDOW_DAYS = int(os.environ.get('GUARD_WINDOW_DAYS'))

# lifecycle
SLEEP_SECONDS = int(os.environ.get('SLEEP_SECONDS'))

# comms
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
ACTIVITY_STREAM_URL = os.environ.get('ACTIVITY_STREAM_URL')
