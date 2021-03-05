provider "google" {
  project = var.project
  region  = var.region
}

# Cloud Run
resource "google_cloud_run_service" "default" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      containers {
        image = var.docker_tag

        env {
          name = "GCP_PROJECT_ID"
          value = var.project
        }

        # BigQuery
        env {
          name  = "BQ_DATASET_ID"
          value = google_bigquery_dataset.default.dataset_id
        }

        # Bucket
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.default.name
        }

        # Other Env Vars
        dynamic "env" {
          for_each = var.other_env_vars
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Backup Bucket
resource "google_storage_bucket" "default" {
  name          = var.gcs_bucket_name
  location      = var.location
  force_destroy = !var.deletion_protection
}

# BigQuery
# Dataset
resource "google_bigquery_dataset" "default" {
  dataset_id          = var.bq_dataset_id
  description         = "Dataset used for trello data"
  location            = var.location
}

# Tables
resource "google_bigquery_table" "default" {
  for_each = toset( ["cards", "labels", "lists", "members", "memberships"])
  # for_each = fileset(path.module, "schemas/*_schema.json")

  dataset_id = google_bigquery_dataset.default.dataset_id
  table_id   = each.key

  deletion_protection = var.deletion_protection

  schema = file("${path.module}/schemas/${each.key}_schema.json")
}

# Cloud scheduler
resource "google_cloud_scheduler_job" "default" {
  name             = var.service_name
  schedule         = var.scheduler_schedule
  time_zone        = var.scheduler_time_zone

  http_target {
    http_method = "GET"
    uri         = "${google_cloud_run_service.default.status[0].url}/get_data"
  }
}
