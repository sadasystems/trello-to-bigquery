# General
variable "project" {
  type = string
}
variable "region" {
  type = string
}
variable "location" {
  type    = string
  default = "US"
}

variable "deletion_protection" {
  default = true
}

variable "service_name" {
  type    = string
  default = "trello-to-bigquery"
}

# Cloud Run
variable "docker_tag" {
  type = string
}

# Cloud Scheduler
variable "scheduler_schedule" {
  type = string
  default = "0 1 * * *" # every day at 1 am
}

variable "scheduler_time_zone" {
  type = string
  default = "America/New_York"
}

# Bucket Name
variable "gcs_bucket_name" {
  type = string
}

# BigQuery
variable "bq_dataset_id" {
  type = string
}

# App vars
variable "other_env_vars" {
  type = map
}

