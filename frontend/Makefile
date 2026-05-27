install:
	bun install

run:
	bun dev

format:
	bun format

lint:
	bun lint

type-check:
	bun type-check

build:
	bun run build

# Build and deploy to Firebase Hosting via Cloud Build. See deploy/SETUP.md.
deploy:
	gcloud builds submit --config=cloudbuild.yaml .