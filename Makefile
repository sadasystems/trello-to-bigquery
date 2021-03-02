projcet_name ?= trello-to-bigquery
# region ?= us-central1
gcp_project_id ?= $(shell gcloud config get-value project)
tag ?= gcr.io/$(gcp_project_id)/$(projcet_name)

build:
	docker build -t $(tag) .

run:
	docker run --rm -p 8080:8080 $(tag)

push:
	docker push $(tag)
	echo "tag: $(tag)"

# deploy:
# 	gcloud run deploy trello-to-bigquery --image $(tag) --region $(region) --platform managed
