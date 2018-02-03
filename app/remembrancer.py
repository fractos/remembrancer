import time
import os
import psycopg2
from subprocess import run, CalledProcessError
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
    connect()
    # get next soonest item that is fewer than X days away
    item = get_next_item(window=settings.GUARD_WINDOW_DAYS)

    if item is not None:
        renew(item)

    disconnect()

    logger.info('sleeping for %s seconds' % str(settings.SLEEP_SECONDS))

    time.sleep(settings.SLEEP_SECONDS)

def get_next_item(window):

    cur = postgres_connection.cursor()

    cur.execute(
        """SELECT estate.id, estate.name, estate.key_id, estate.secret_key, """ +
        """       item.hostname, item.due FROM estate JOIN item ON estate.id = item.estate_id """ +
        """WHERE item.processing = false AND """ +
        """item.due < (CURRENT_DATE + INTERVAL '""" + str(window) + """ days') """
        """ORDER BY item.due ASC LIMIT 1""")

    rows = cur.fetchall()

    if rows is None or len(rows) is 0:
        return None

    return {
        "estate_id": rows[0][0],
        "estate_name": rows[0][1],
        "estate_key_id": rows[0][2],
        "estate_secret_key": rows[0][3],
        "item_hostname": rows[0][4],
        "item_due": rows[0][5]
    }

def renew(item):

    logger.info('item: ')
    for k, v in item.items():
        logger.info('  %s: %s', k, str(v))

    logger.info('renewing %s on %s (%s) which is due %s' %
                (item['item_hostname'], item['estate_name'],
                 item['estate_id'], item['item_due']))

    # to renew an item:
    #   create shell with environment variables set for the estate
    os.environ['AWS_ACCESS_KEY_ID'] = item['estate_key_id']
    os.environ['AWS_SECRET_ACCESS_KEY'] = item['estate_secret_key']
    os.environ['DOMAIN'] = item['item_hostname']

    try:
        run(args=['/opt/certbot/route53.sh'],
            check=True)
    except CalledProcessError as cpe:
        logger.error("exception: returned code was %d" % cpe.returncode)

    return

logger.info('remembrancer starting...')
lifecycle()
logger.info('remembrancer done')
