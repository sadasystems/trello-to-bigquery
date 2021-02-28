# General
import requests
import json
import re
import os
import logging as log
import datetime
import logging

# Google Cloud
from google.cloud import storage
from google.cloud import bigquery

# Logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def sanitize(value):
    if isinstance(value, dict):
        # BigQuery doesn't accept empty objects
        if not value:
            return None
        result = {}
        for k, v in value.items():
            # Sanitize key
            k_cleaned = re.sub(r"(^[^a-zA-Z_]+)|([^a-zA-Z_0-9]+)", "", k)
            # Add number to the end until it's unique
            k_renamed = k_cleaned
            i = 0
            while k_renamed in result:
                k_renamed = k_cleaned + str(i)
                i += 1
            result[k_renamed] = sanitize(v)
        value = result
    elif isinstance(value, list):
        value = [sanitize(v) for v in value]

    return value


def trello_to_bq():

    # Read Params Vars
    # Trello
    trello_board_id = os.getenv('TRELLO_BOARD_ID')
    trello_key = os.getenv('TRELLO_KEY')
    trello_token = os.getenv('TRELLO_TOKEN')

    # BigQuery
    dataset_id = os.getenv('BQ_DATASET_ID')
    # Google Storage
    bucket_name = os.getenv('GCS_BUCKET_NAME')

    # Upload Params
    write_raw_local = os.getenv('WRITE_RAW_LOCAL')
    write_processed_local = os.getenv('WRITE_PROCESSED_LOCAL')

    write_raw_remote = os.getenv('WRITE_RAW_REMOTE')
    write_processed_remote = os.getenv('WRITE_PROCESSED_REMOTE')

    # Raise error if values not set
    for name, val in [
        ('TRELLO_BOARD_ID', trello_board_id),
        ('TRELLO_KEY', trello_key),
        ('TRELLO_TOKEN', trello_token),
        ('GCS_BUCKET_NAME', bucket_name),
    ]:
        if not val:
            raise ValueError(
                '{name} Environment Variables not found'.format(name=name))

    # Init Clients
    log.info('Initializing BigQuery Client')
    bigquery_client = bigquery.Client()

    # If writing to remote, init storage client
    if write_raw_remote or write_processed_remote:
        log.info('Initializing Google Storage Client')
        storage_client = storage.Client()
        # Get Bucket
        bucket = storage_client.get_bucket(bucket_name)

    # Query all board data
    log.info('Querying trello board data')
    url = 'https://api.trello.com/1/boards/{trello_board_id}'.format(
        trello_board_id=trello_board_id)

    headers = {
        'Accept': 'application/json'
    }

    query = {
        'key': trello_key,
        'token': trello_token,
        'fields': 'all',
        'actions': 'all',
        'action_fields': 'all',
        'actions_limit': 1000,
        'cards': 'all',
        'card_fields': 'all',
        'card_attachments': 'true',
        'labels': 'all',
        'lists': 'all',
        'list_fields': 'all',
        'members': 'all',
        'member_fields': 'all',
        'checklists': 'all',
        'checklist_fields': 'all',
        'organization': 'false',
    }

    response = requests.request(
        'GET',
        url,
        headers=headers,
        params=query,
    )

    # Parse json into python dict
    content = json.loads(response.text)
    content = sanitize(content)  # fix bq stuff

    # Get current time
    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d-%H-%M-%S")

    raw_data_path = 'raw_data/{time}-board.json'.format(time=now_str)

    # Write raw data locally
    if write_raw_local:
        log.info('Writing board data locally')
        os.makedirs(os.path.dirname(raw_data_path), exist_ok=True)
        with open(raw_data_path, 'w') as outfile:
            json.dump(content, outfile, indent=4)

    # Upload raw board data
    if write_raw_remote:
        log.info('Uploading board data to cloud storage')
        board_blob = bucket.blob(raw_data_path)
        board_blob.upload_from_string(response.text)

    for field in [
        'actions',
        'cards',
        'labels',
        'lists',
        'members',
        'memberships',
    ]:
        field_datas = content.pop(field)
        if field == 'actions':
            # TODO: handle actions
            pass

        # bigquery_client.load_table_from_json(
        #     field_datas,
        #     field
        # )

        processed_data_path = 'processed_data/{time}-{field}.jsonl'.format(
            time=now_str, field=field)

        jsonl_text = ''
        for field_data in field_datas:
            jsonl_text += json.dumps(field_data) + '\n'

        if write_processed_local:
            os.makedirs(os.path.dirname(processed_data_path), exist_ok=True)
            with open(processed_data_path, 'w') as outfile:
                outfile.write(jsonl_text)

        if write_raw_remote:
            board_blob = bucket.blob(processed_data_path)
            board_blob.upload_from_string(jsonl_text)


if __name__ == "__main__":
    trello_to_bq()
