# trello-to-bigquery
This is a app which pulls data from trello and puts it into BigQuery (optionally writing it to a gcs bucket)


## Setup
(this needs some automating)
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
6. Build docker image
    ```bash
    make build
    ```
7. Push docker image to Google Container registry
    ```bash
    make push
    ```
8. Navigate to [cloud run](https://console.cloud.google.com/run) in the google console and "Create Service"
9. Name your service
10. Select the container created & pushed above
11. Under "Advanced"
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
