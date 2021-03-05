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
from google.api_core.exceptions import BadRequest

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


def trello_to_bq(
    gcp_project_id,
    trello_board_id,
    trello_key,
    trello_token,
    bq_dataset_id,
    gcs_bucket_name=None,
    write_raw_local=False,
    write_processed_local=False,
    write_raw_remote=False,
    write_processed_remote=False
):
    # If writing to remote, init storage client
    if write_raw_remote or write_processed_remote:
        log.info('Initializing Google Storage Client')
        if not gcs_bucket_name:
            raise ValueError(
                'if using write_raw_remote or write_processed_remote, you must provide a gcs_bucket_name')
        storage_client = storage.Client()
        # Get Bucket
        bucket = storage_client.get_bucket(gcs_bucket_name)

    # Init bigquery client
    log.info('Initializing BigQuery Client')
    bigquery_client = bigquery.Client()

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
        'card_customFieldItems': 'true',
        'customFields': 'true',
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
        log.info('Writing {path} locally'.format(path=raw_data_path))
        os.makedirs(os.path.dirname(raw_data_path), exist_ok=True)
        with open(raw_data_path, 'w') as outfile:
            json.dump(content, outfile, indent=4)

    # Upload raw board data
    if write_raw_remote:
        log.info('Uploading {path} to cloud storage'.format(
            path=raw_data_path))
        board_blob = bucket.blob(raw_data_path)
        board_blob.upload_from_string(response.text)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True,
        ignore_unknown_values=True,
        # WRITE_TRUNCATE: If the table already exists, BigQuery overwrites the table data
        # write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )

    bq_jobs = []
    for field in [
        'actions',
        'cards',
        'labels',
        'lists',
        'members',
        'memberships',
    ]:
        if field == 'actions':
            # TODO: handle actions
            pass
        field_datas = content.pop(field)
        # Add timestamp
        for field_data in field_datas:
            field_data['trelloQueryTime'] = now.isoformat()

        load_job = bigquery_client.load_table_from_json(
            field_datas,
            '{}.{}.{}'.format(gcp_project_id, bq_dataset_id, field),
            job_config=job_config
        )
        bq_jobs.append(load_job)

        processed_data_path = 'processed_data/{time}-{field}.jsonl'.format(
            time=now_str, field=field)

        jsonl_text = ''
        for field_data in field_datas:
            jsonl_text += json.dumps(field_data) + '\n'

        if write_processed_local:
            log.info('Writing {path} locally'.format(path=processed_data_path))
            os.makedirs(os.path.dirname(processed_data_path), exist_ok=True)
            with open(processed_data_path, 'w') as outfile:
                outfile.write(jsonl_text)

        if write_raw_remote:
            log.info('Uploading {path} to cloud storage'.format(
                path=processed_data_path))
            board_blob = bucket.blob(processed_data_path)
            board_blob.upload_from_string(jsonl_text)

    success = True
    for job in bq_jobs:
        try:
            job.result()
        except BadRequest as e:
            log.exception(e)
            success = False
    return success


if __name__ == "__main__":
    import configargparse

    parser = configargparse.ArgParser()

    # Trello
    parser.add(
        '--trello-board-id',
        required=True,
        env_var='TRELLO_BOARD_ID',
    )
    parser.add(
        '--trello-key',
        required=True,
        env_var='TRELLO_KEY',
    )
    parser.add(
        '--trello-token',
        required=True,
        env_var='TRELLO_TOKEN',
    )

    # BQ
    parser.add(
        '--bq-dataset-id',
        required=True,
        env_var='BQ_DATASET_ID',
    )

    # Cloud Storage
    parser.add(
        '--gcs-bucket-name',
        env_var='GCS_BUCKET_NAME',
    )

    # Save options
    parser.add(
        '--write-raw-local',
        env_var='WRITE_RAW_LOCAL',
    )
    parser.add(
        '--write-processed-local',
        env_var='WRITE_PROCESSED_LOCAL',
    )
    parser.add(
        '--write-raw-remote',
        env_var='WRITE_RAW_REMOTE',
    )
    parser.add(
        '--write-processed-remote',
        env_var='WRITE_PROCESSED_REMOTE',
    )
    args = parser.parse_args()

    trello_to_bq(
        trello_board_id=args.trello_board_id,
        trello_key=args.trello_key,
        trello_token=args.trello_token,
        bq_dataset_id=args.bq_dataset_id,
        gcs_bucket_name=args.gcs_bucket_name,
        write_raw_local=args.write_raw_local,
        write_processed_local=args.write_processed_local,
        write_raw_remote=args.write_raw_remote,
        write_processed_remote=args.write_processed_remote,
    )
