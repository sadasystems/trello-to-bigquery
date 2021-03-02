# trello-to-bigquery
This is a app which pulls data from trello and puts it into BigQuery (optionally writing it to a gcs bucket)

## Prereqs
1. Set project account and project id
    ```
    gcloud config set account <email address>
    gcloud config set project <project_id>
    ```
2. Authenticate account and application to use default login
    ```
    gcloud auth login
    gcloud auth application-default login
    ```
3. Create a BigQuery Dataset 
4. Create tables for each scheme in `./schemas/`
5. (optional) Create GCS bucket

## CLI usage

Run the following commands to see options:
```bash
python get_data.py --help
```
(**Tip:** you can also use environment variables as outlined below)

## Setup Cloud Run
1. Build docker image
    ```bash
    make build
    ```
2. Push docker image to Google Container registry
    ```bash
    make push
    ```
3. Navigate to [cloud run](https://console.cloud.google.com/run) in the google console and "Create Service"
4. Name your service
5.  Select the container created & pushed above
6.  Under "Advanced"
    1.  Memory Allocated to `1 gb`
    2.  Under "Variables" set env vars as outlined in the "Env Vars" below

## Env Vars
| Variable Name          | Description                                             |
| ---------------------- | ------------------------------------------------------- |
| TRELLO_KEY             | trello api key                                          |
| TRELLO_TOKEN           | trello secret token                                     |
| TRELLO_BOARD_ID        | trello board id                                         |
| BQ_DATASET_ID          | BigQuery dataset id (including gcp project id)          |
| GCS_BUCKET_NAME        | (Required if uploading to to gcs) gcs bucket name.      |
| WRITE_RAW_LOCAL        | (Optional) Whether to save raw json query locally       |
| WRITE_PROCESSED_LOCAL  | (Optional) Whether to save bigquery-safe jsonl locally  |
| WRITE_RAW_REMOTE       | (Optional) Whether to upload raw json query to GCS      |
| WRITE_PROCESSED_REMOTE | (Optional) Whether to upload bigquery-safe jsonl to GCS |
