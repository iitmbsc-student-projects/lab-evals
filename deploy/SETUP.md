# GCP Deployment Setup

One-time bootstrap of the GCP project that hosts `lab-evals`. Once these steps
are done, day-to-day deploys are just `gcloud builds submit` (see the root
`README.md`).

Architecture:

```
Browser  →  Firebase Hosting (frontend/dist, SPA)
            │
            └→ HTTPS → Cloud Run `lab-evals-backend` (asia-south1)
                       └→ Unix socket /cloudsql/<conn> → Cloud SQL Postgres 16
```

All secrets live in Google Secret Manager. Cloud Run mounts them as env vars
via `--set-secrets`. The frontend build pulls `VITE_*` secrets at build time
and bakes them into the static bundle.

---

## Variables

```bash
export PROJECT_ID=lab-evals          # change to your actual project ID
export REGION=asia-south1
export SQL_INSTANCE=lab-evals-db
export SQL_DB=lab_evals
export SQL_USER=lab_evals_app
export AR_REPO=lab-evals
export RUNTIME_SA=lab-evals-backend-sa
```

---

## 1. Project + APIs

```bash
gcloud projects create "$PROJECT_ID"    # skip if it already exists
gcloud config set project "$PROJECT_ID"

# Link a billing account (replace with your billing account ID)
# gcloud billing projects link "$PROJECT_ID" --billing-account=XXXXXX-XXXXXX-XXXXXX

gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  firebasehosting.googleapis.com \
  firebase.googleapis.com \
  iamcredentials.googleapis.com
```

Then link the project to Firebase and create a Hosting site (one-time, easiest
in the console: <https://console.firebase.google.com> → Add project → pick the
existing GCP project → Hosting → Get started → site ID `lab-evals`). The
default URL becomes `https://lab-evals.web.app`.

---

## 2. Artifact Registry

```bash
gcloud artifacts repositories create "$AR_REPO" \
  --repository-format=docker \
  --location="$REGION" \
  --description="lab-evals container images"
```

---

## 3. Cloud SQL

```bash
gcloud sql instances create "$SQL_INSTANCE" \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region="$REGION" \
  --storage-size=10GB \
  --storage-auto-increase \
  --backup-start-time=18:00

gcloud sql databases create "$SQL_DB" --instance="$SQL_INSTANCE"

# Generate a password and stash it locally for the secret step below
SQL_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
gcloud sql users create "$SQL_USER" \
  --instance="$SQL_INSTANCE" \
  --password="$SQL_PASSWORD"

CONN_NAME="$PROJECT_ID:$REGION:$SQL_INSTANCE"
echo "Cloud SQL connection name: $CONN_NAME"
```

---

## 4. Secrets

```bash
# JWT signing key
openssl rand -hex 32 | \
  gcloud secrets create jwt-secret --data-file=-

# OAuth client ID (the same value goes to backend env and frontend build)
printf '%s' 'YOUR_GOOGLE_OAUTH_CLIENT_ID.apps.googleusercontent.com' | \
  gcloud secrets create google-client-id --data-file=-

# Full DATABASE_URL with the password from step 3
printf '%s' "postgresql+psycopg://${SQL_USER}:${SQL_PASSWORD}@/${SQL_DB}?host=/cloudsql/${CONN_NAME}" | \
  gcloud secrets create database-url --data-file=-

# Placeholder for vite-api-base; we will populate it after the first backend deploy
printf '%s' 'https://placeholder.invalid' | \
  gcloud secrets create vite-api-base --data-file=-
```

---

## 5. Service accounts and IAM

```bash
# Backend runtime service account
gcloud iam service-accounts create "$RUNTIME_SA" \
  --display-name="lab-evals Cloud Run runtime"

RUNTIME_SA_EMAIL="${RUNTIME_SA}@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant runtime SA: Cloud SQL access, logs, scoped secret access
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${RUNTIME_SA_EMAIL}" --role="roles/cloudsql.client"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${RUNTIME_SA_EMAIL}" --role="roles/logging.logWriter"
for s in jwt-secret google-client-id database-url; do
  gcloud secrets add-iam-policy-binding "$s" \
    --member="serviceAccount:${RUNTIME_SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"
done

# Cloud Build SA
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Backend pipeline needs to push images, deploy Cloud Run, act-as runtime SA
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${CB_SA}" --role="roles/artifactregistry.writer"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${CB_SA}" --role="roles/run.admin"
gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA_EMAIL" \
  --member="serviceAccount:${CB_SA}" --role="roles/iam.serviceAccountUser"

# Frontend pipeline needs to read VITE_* secrets and deploy Firebase Hosting
for s in vite-api-base google-client-id; do
  gcloud secrets add-iam-policy-binding "$s" \
    --member="serviceAccount:${CB_SA}" \
    --role="roles/secretmanager.secretAccessor"
done
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${CB_SA}" --role="roles/firebasehosting.admin"
```

---

## 6. OAuth client (manual, in the console)

<https://console.cloud.google.com/apis/credentials>

Edit the existing OAuth 2.0 Client ID (or create a new one) and add to
**Authorized JavaScript origins**:

- `https://lab-evals.web.app`
- `https://lab-evals.firebaseapp.com`
- (optionally) `http://localhost:5173` for local dev

No redirect URIs are needed — the app uses the Google Identity Services
ID-token flow only.

Make sure the Client ID matches what is stored in the `google-client-id`
Secret Manager secret (step 4).

---

## 7. First deploy

```bash
# Backend (from repo root)
gcloud builds submit --config=backend/cloudbuild.yaml backend/

# Capture the Cloud Run URL and write it to the vite-api-base secret
BACKEND_URL=$(gcloud run services describe lab-evals-backend \
  --region="$REGION" --format='value(status.url)')
echo "Backend URL: $BACKEND_URL"
printf '%s' "$BACKEND_URL" | \
  gcloud secrets versions add vite-api-base --data-file=-

# Frontend (now that vite-api-base points at the real backend)
gcloud builds submit --config=frontend/cloudbuild.yaml frontend/
```

If the Cloud Run URL turns out different from the placeholder
`https://lab-evals.web.app` we set in `FRONTEND_ORIGIN`, redeploy the backend
with `--substitutions=_FRONTEND_ORIGIN=$ACTUAL` so CORS matches the Hosting
domain.

---

## 8. Cloud Build triggers (optional but recommended)

Connect the GitHub repo once in the console
(<https://console.cloud.google.com/cloud-build/triggers>) and create two
triggers on push to `master`:

| Trigger              | Configuration file        | Included files          |
| -------------------- | ------------------------- | ----------------------- |
| `lab-evals-backend`  | `backend/cloudbuild.yaml` | `backend/**`            |
| `lab-evals-frontend` | `frontend/cloudbuild.yaml`| `frontend/**`           |

Use **Included files filter** so the backend trigger does not rebuild on
frontend-only changes and vice versa.

---

## Inventory after setup

| Resource             | Name                                          |
| -------------------- | --------------------------------------------- |
| GCP project          | `$PROJECT_ID`                                 |
| Region               | `asia-south1`                                 |
| Artifact Registry    | `lab-evals` (docker)                          |
| Cloud SQL instance   | `lab-evals-db` (Postgres 16, db-f1-micro)     |
| Cloud SQL database   | `lab_evals`                                   |
| Cloud SQL user       | `lab_evals_app`                               |
| Cloud Run service    | `lab-evals-backend`                           |
| Runtime SA           | `lab-evals-backend-sa@…`                      |
| Secrets              | `jwt-secret`, `google-client-id`, `database-url`, `vite-api-base` |
| Firebase Hosting     | `lab-evals` → `https://lab-evals.web.app`     |

---

## Rotation, smoke tests, troubleshooting

- **Rotate a secret**: `gcloud secrets versions add <name> --data-file=-`
  then `gcloud run services update lab-evals-backend --region="$REGION"`
  (Cloud Run rereads `:latest` on the new revision).
- **Health**: `curl https://lab-evals-backend-<hash>-as.a.run.app/healthz`.
- **DB shell**: `gcloud sql connect "$SQL_INSTANCE" --user="$SQL_USER" --database="$SQL_DB"`.
- **Logs**: `gcloud run services logs read lab-evals-backend --region="$REGION" --limit=200`.
- **Schema**: created at startup by `Base.metadata.create_all()` in
  `app/main.py`. New tables/columns appear on the next cold start; destructive
  changes still need a manual `ALTER` or — eventually — Alembic.
