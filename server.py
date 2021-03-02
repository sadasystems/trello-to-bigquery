import os

from flask import Flask
from get_data import trello_to_bq

app = Flask(__name__)


@app.route("/")
def index():
    return "trello-to-bigquery is running."


@app.route("/get_data")
def get_data():
    # Trello
    trello_board_id = os.getenv('TRELLO_BOARD_ID')
    trello_key = os.getenv('TRELLO_KEY')
    trello_token = os.getenv('TRELLO_TOKEN')

    # BigQuery
    bq_dataset_id = os.getenv('BQ_DATASET_ID')

    # Google Storage
    gcs_bucket_name = os.getenv('GCS_BUCKET_NAME')

    # Upload Params
    write_raw_local = os.getenv('WRITE_RAW_LOCAL')
    write_processed_local = os.getenv('WRITE_PROCESSED_LOCAL')

    write_raw_remote = os.getenv('WRITE_RAW_REMOTE')
    write_processed_remote = os.getenv('WRITE_PROCESSED_REMOTE')

    success = trello_to_bq(
        trello_board_id=trello_board_id,
        trello_key=trello_key,
        trello_token=trello_token,
        bq_dataset_id=bq_dataset_id,
        gcs_bucket_name=gcs_bucket_name,
        write_raw_local=write_raw_local,
        write_processed_local=write_processed_local,
        write_raw_remote=write_raw_remote,
        write_processed_remote=write_processed_remote,
    )

    if success:
        return "Trello data successfully moved to bigquery"
    else:
        return "Trello data failed moved to bigquery (see logs for more details)"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
