tag ?= gcr.io/sada-aaron-brock/trello-to-bigquery
region ?= us-central1

build:
	docker build -t $(tag) .

run:
	docker run --rm -p 8080:8080 $(tag)

push:
	docker push $(tag)

deploy:
	gcloud run deploy trello-to-bigquery --image $(tag) --region $(region) --platform managed
