import time
import os
import psycopg2
import json
from subprocess import run, CalledProcessError, PIPE
from logzero import logger
import settings

def connect():
    global postgres_connection

    logger.info('connecting to database')
    postgres_connection = psycopg2.connect(
        "dbname='" + settings.DATABASE_NAME +
        "' user='" + settings.DATABASE_USERNAME +
        "' host='" + settings.DATABASE_HOST +
        "' password='" + settings.DATABASE_PASSWORD + "'")

def disconnect():
    logger.info('disconnecting from database')
    postgres_connection.close()

def lifecycle():
    while True:
        connect()
        # get next soonest item that is fewer than X days away
        item = get_next_item(window=settings.GUARD_WINDOW_DAYS)

        if item is not None:
            renew(item)

        disconnect()

        if settings.SLEEP_SECONDS > 0:
            logger.info('sleeping for %s seconds' % str(settings.SLEEP_SECONDS))

            time.sleep(settings.SLEEP_SECONDS)
        else:
            break
    logger.info('lifecycle ending.')

def get_next_item(window):

    cur = postgres_connection.cursor()

    cur.execute(
        """SELECT estate_id, region, hostname, due FROM item """ +
        """WHERE processing = false AND """ +
        """due < (CURRENT_DATE + INTERVAL '%s days') """
        """ORDER BY due ASC LIMIT 1""", [window])

    rows = cur.fetchall()

    if rows is None or len(rows) is 0:
        return None

    return {
        "estate_id": rows[0][0],
        "region": rows[0][1],
        "item_hostname": rows[0][2],
        "item_due": rows[0][3]
    }

def renew(item):

    logger.info('item: ')
    for k, v in item.items():
        logger.info('  %s: %s', k, str(v))

    logger.info('renewing %s on %s/%s which is due %s' %
                (item['item_hostname'], item['estate_id'],
                 item['region'], item['item_due']))

    # load up credentials for the target AWS estate

    parameter_result = run(args=["aws", "--region", item['region'],
                                 "ssm", "get-parameters",
                                 "--names", "%s%s" %
                                 (settings.SSM_KEY_PREFIX, item['estate_id']),
                                 "--with-decryption"], stdout=PIPE)

    logger.info('result was %s' % parameter_result.stdout)

    # parse the SSM results to get to the JSON blob
    value_payload = json.loads(parameter_result.stdout)

    # parse the JSON blob to get to the credentials
    keys_payload = json.loads(value_payload['Parameters'][0]['Value'])

    os.environ['AWS_ACCESS_KEY_ID'] = keys_payload['AWS_ACCESS_KEY_ID']
    os.environ['AWS_SECRET_ACCESS_KEY'] = keys_payload['AWS_SECRET_ACCESS_KEY']

    # and the target domain to renew
    os.environ['DOMAIN'] = item['item_hostname']

    try:
        run(args=['/opt/certbot/route53.sh'],
            check=True)
    except CalledProcessError as cpe:
        logger.error("exception: returned code was %d" % cpe.returncode)

    # revert to home credentials
    os.environ['AWS_ACCESS_KEY_ID'] = home_access_key_id
    os.environ['AWS_SECRET_ACCESS_KEY'] = home_secret_access_key

    return

def save_credentials():
    global home_access_key_id
    global home_secret_access_key

    logger.info("saving home AWS credentials")

    home_access_key_id = settings.ACCESS_KEY_ID
    home_secret_access_key = settings.SECRET_ACCESS_KEY

logger.info('remembrancer starting...')
save_credentials()
lifecycle()
logger.info('remembrancer done')
