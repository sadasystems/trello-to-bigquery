-include .env

# App vars
REGION       ?= us-east1
SERVICE_NAME ?= trello-to-bigquery
DOCKER_TAG   ?= gcr.io/$(GCP_PROJECT_ID)/$(SERVICE_NAME)

# Map to Terraform Vars
TF_VAR_region          ?= $(REGION)
TF_VAR_project         ?= $(GCP_PROJECT_ID)
TF_VAR_service_name    ?= $(SERVICE_NAME)
TF_VAR_docker_tag      ?= $(DOCKER_TAG)
TF_VAR_gcs_bucket_name ?= $(GCS_BUCKET_NAME)
TF_VAR_bq_dataset_id   ?= $(BQ_DATASET_ID)

# Cloud Run Env Vars
define TF_VAR_other_env_vars
{
	"TRELLO_KEY": "$(TRELLO_KEY)",
	"TRELLO_TOKEN": "$(TRELLO_TOKEN)",
	"TRELLO_BOARD_ID": "$(TRELLO_BOARD_ID)",
}
endef
export

# Makefile Vars
terraform = cd ./terraform/ && terraform

build:
	docker build -t $(DOCKER_TAG) ./app

run:
	docker run --rm -p 8080:8080 $(DOCKER_TAG)

push:
	docker push $(DOCKER_TAG)

init: tf-init 
plan: tf-plan
apply: tf-apply
destroy: tf-destroy

tf-%:
	$(terraform) $*

#
# Here be dragons
#
import: import-table-cards import-table-labels import-table-lists import-table-members import-table-memberships
	# Bucket
	-$(terraform) import google_storage_bucket.default $(GCS_BUCKET_NAME)
	# BigQuery Dataset
	-$(terraform) import google_bigquery_dataset.default $(GCP_PROJECT_ID)/$(BQ_DATASET_ID)
	# Cloud Run
	-$(terraform) import google_cloud_run_service.default $(REGION)/$(GCP_PROJECT_ID)/$(SERVICE_NAME)
	# Cloud Scheduler
	-$(terraform) import google_cloud_scheduler_job.default $(GCP_PROJECT_ID)/$(REGION)/$(SERVICE_NAME)

import-table-%:
	-$(terraform) import google_bigquery_table.default[\"$*\"] $(GCP_PROJECT_ID)/$(BQ_DATASET_ID)/$*
