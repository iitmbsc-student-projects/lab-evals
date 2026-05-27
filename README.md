# lab-evals

Full Stack Application for Managing Offline Lab Evaluations

## Local development

- Backend: `cd backend && make install && make run` (see `backend/.env.example`)
- Frontend: `cd frontend && make install && make run` (see `frontend/.env.example`)

## Deployment (Google Cloud)

The app deploys to **Cloud Run** (backend) + **Firebase Hosting** (frontend),
with **Cloud SQL** for Postgres and **Secret Manager** for all credentials.
Region is `asia-south1`.

One-time GCP project setup is documented in [`deploy/SETUP.md`](deploy/SETUP.md)
— devops runs through it once. After that, deploys are:

```bash
make -C backend deploy      # gcloud builds submit --config=backend/cloudbuild.yaml backend/
make -C frontend deploy     # gcloud builds submit --config=frontend/cloudbuild.yaml frontend/
```

or push to `master` if the GitHub Cloud Build triggers are configured.
