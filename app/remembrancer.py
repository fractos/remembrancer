import time
import os
import json
import http_client
import datetime
import requests
import boto3
from botocore.exceptions import ClientError
from subprocess import run, CalledProcessError, PIPE
from logzero import logger

import settings

def create_clients():
    global dynamodb_client
    global dynamodb_resource
    global ssm_client

    dynamodb_resource = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
    dynamodb_client = boto3.client('dynamodb', region_name=settings.AWS_REGION)
    ssm_client = boto3.client('ssm', region_name=settings.AWS_REGION)

def create_table(name):
    logger.info("creating table " + name)

    try:
        dynamodb_resource.create_table(
            AttributeDefinitions=[
                {
                    'AttributeName': 'Estate',
                    'AttributeType': 'S',
                },
                {
                    'AttributeName': 'Hostname',
                    'AttributeType': 'S',
                },
                {
                    'AttributeName': 'Due',
                    'AttributeType': 'S',
                },
                {
                    'AttributeName': 'Region',
                    'AttributeType': 'S',
                },
                {
                    'AttributeName': 'Status',
                    'AttributeType': 'S'
                }
            ],
            KeySchema=[
                {
                    'AttributeName': 'Hostname',
                    'KeyType': 'HASH'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1,
            },
            TableName=name,
        )

        dynamodb_client.get_waiter('table_exists').wait(TableName=name)

    except dynamodb_client.exceptions.ResourceInUseException:
        logger.info("table " + name + " already exists")
        pass

def lifecycle():
    while True:
        # get next soonest item that is fewer than X days away
        item = get_next_item(window=settings.GUARD_WINDOW_DAYS)

        if item is not None:
            renew(item)

        if settings.SLEEP_SECONDS > 0:
            logger.info('sleeping for %s seconds' % str(settings.SLEEP_SECONDS))

            time.sleep(settings.SLEEP_SECONDS)
        else:
            break
    logger.info('lifecycle ending.')

def get_next_item(window):
    table = boto3.dynamodb.Table(settings.DATABASE_TABLE)

    response = table.scan()
    data = response['Items']

    while response.get('LastEvaluatedKey'):
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    if len(data) == 0:
        return None

    latest_data = None
    latest_datetime = None

    present = datetime.datetime.now()
    logger.info('present = %s' % str(present))

    guard_window = present - datetime.timedelta(days=window)

    logger.info('guard window = %s' % str(guard_window))

    for candidate_data in data:
        candidate_datetime = datetime.datetime.strptime(candidate_data['Due'], "%Y-%m-%d")
        logger.info('candidate datetime = %s' % str(candidate_datetime))
        if candidate_datetime < guard_window:
            logger.info('candidate datetime is within guard window')
            if latest_datetime is not None and latest_datetime < candidate_datetime:
                logger.info('candidate is more recent than another')
                latest_data = candidate_data
                latest_datetime = candidate_datetime
            elif latest_datetime is None:
                logger.info('candidate is first item')
                latest_data = candidate_data
                latest_datetime = candidate_datetime
            else:
                logger.info('candidate is not selected')

    return latest_data

def renew(item):

    announce('renewing %s on %s/%s which is due %s' %
             (item['Hostname'], item['Estate'],
              item['Region'], item['Due']))

    return

    # load up credentials for the target AWS estate

    result = get_parameter(item["Estate"])

    # parse the JSON blob to get to the credentials
    keys_payload = json.loads(result)

    # set the target credentials in our environment
    os.environ['AWS_ACCESS_KEY_ID'] = keys_payload['AWS_ACCESS_KEY_ID']
    os.environ['AWS_SECRET_ACCESS_KEY'] = keys_payload['AWS_SECRET_ACCESS_KEY']

    # and the target domain to renew
    os.environ['DOMAIN'] = item['Hostname']

    # call the certbot script
    try:
        run(args=['/opt/certbot/route53.sh'],
            check=True, stderr=PIPE)
    except CalledProcessError as cpe:
        logger.error('exception: returned code was %d' % cpe.returncode)
        report_problem(item, cpe.stderr)
        return

    # read the certificates from the volume
    cert_body = ""
    chain_body = ""
    privkey_body = ""

    try:
        cert_body = read_file(file="/etc/letsencrypt/live/%s/cert.pem" % item['Hostname'])
        chain_body = read_file(file="/etc/letsencrypt/live/%s/chain.pem" % item['Hostname'])
        privkey_body = read_file(file="/etc/letsencrypt/live/%s/privkey.pem" % item['Hostname'])
    except OSError as ose:
        logger.error('exception: problem during read of file %s: %s' % (ose.filename, ose.strerror))
        report_problem(item, ose.strerror)
        mark_item_as_problem(item, 'reading certificates failed')
        return

    # store the certificates in SSM
    try:
        put_parameter(suffix="%s cert" % item["Hostname"],
                      body=cert_body,
                      description='SSL Certificate for %s' % item["Hostname"])
        put_parameter(suffix="%s chain" % item["Hostname"],
                      body=chain_body,
                      description='SSL Chain for %s' % item["Hostname"])
        put_parameter(suffix="%s privkey" % item["Hostname"],
                      body=privkey_body,
                      description='SSL PrivKey for %s' %item["Hostname"])
    except ClientError as ce:
        logger.error('exception: problem during parameter set - %s' % ce)
        report_problem(item, str(ce))
        mark_item_as_problem(item, "storing certificates failed")
        return

    # calculate when the certificates are next due
    next_due = datetime.datetime.now() + datetime.timedelta(days=90)

    # mark the item as done and store the due date
    mark_item_as_done(item, next_due)

    announce('Renewal of %s successful, due %s.\nCertificates can now be found in SSM/%s with prefix %s%s and also in the /etc/letsencrypt local volume.'
             % (item['Hostname'],
                next_due,
                settings.AWS_REGION,
                settings.SSM_KEY_PREFIX,
                item['Hostname']))

    # revert to home credentials
    os.environ['AWS_ACCESS_KEY_ID'] = home_access_key_id
    os.environ['AWS_SECRET_ACCESS_KEY'] = home_secret_access_key

def mark_item_as_problem(item, reason):
    mark_item(item, reason, due_date=datetime.datetime.strptime(item['Due'], "%Y-%m-%d"))

def mark_item_as_done(item, due_date):
    mark_item(item, "", due_date=due_date)

def mark_item(item, reason, due_date):

    table = dynamodb_resource.Table(settings.DATABASE_TABLE)
    table.put_item(
        Item={
            'Estate': item["Estate"],
            'Hostname': item["Hostname"],
            'Due': datetime.datetime.strftime(due_date, "%Y-%m-%d"),
            'Region': item["Region"],
            'Status': reason
        }
    )

def read_file(file):
    body = ""
    with open(file, 'r') as file_object:
        body = file_object.read()

    return body

def get_parameter(suffix):
    response = ssm_client.get_parameters(
        Names=[
            "%s%s" % (settings.SSM_KEY_PREFIX, suffix),
        ],
        WithDecryption=True
    )
    return response['Parameters'][0]['Value']

def put_parameter(suffix, body, description):

    response = ssm_client.put_parameter(
        Name="%s%s" % (settings.SSM_KEY_PREFIX, suffix),
        Value=body,
        Description=description,
        Type='SecureString',
        KeyId=settings.KMS_KEY_ALIAS,
        Overwrite=True
    )

def announce(announcement):
    message = '{"text": "%s", "link_names": 1}' % announcement

    slack_message(message, settings.SLACK_WEBHOOK_URL)
    activity_stream_message(message, settings.ACTIVITY_STREAM_URL)

def report_problem(item, problem):
    message = '{"text": "Remembrancer hit a problem renewing certificate for %s: %s", "link_names": 1}' % (item['Hostname'], problem)

    slack_message(message, settings.SLACK_WEBHOOK_URL)
    activity_stream_message(message, settings.ACTIVITY_STREAM_URL)

def activity_stream_message(message, activity_stream_url):
    # stub out for now
    pass

def slack_message(message, webhook_url):
    response = requests.post(
        webhook_url, data=message,
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        logger.error(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )

def save_credentials():
    # store the credentials as passed to us initially

    global home_access_key_id
    global home_secret_access_key

    logger.info("saving home AWS credentials")

    home_access_key_id = settings.ACCESS_KEY_ID
    home_secret_access_key = settings.SECRET_ACCESS_KEY

logger.info('remembrancer starting...')
create_clients()
create_table(settings.DATABASE_TABLE)
save_credentials()
lifecycle()
logger.info('remembrancer done')
