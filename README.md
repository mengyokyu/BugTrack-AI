# BugTrack AI

BugTrack AI is a small Flask + PostgreSQL bug-tracking platform with an optional AI analysis feature. It remains a modular monolith: the application is intentionally simple, while GitHub Actions, Docker, Kubernetes, Argo CD, Terraform, Ansible, Prometheus, Grafana, Fluentd, Elasticsearch, Kibana, SonarQube, and Trivy provide the DevOps workflow.

## Features

Users can register, log in, log out, create and manage bugs, assign bugs, set severity and priority, describe reproduction details, search/filter/sort/paginate their accessible bugs, add comments, view activity history, organize bugs under owned projects, and request optional AI analysis. Admin users are selected by the `ADMIN_EMAIL` configuration value. Passwords are hashed; protected mutations require a CSRF header; authorization is enforced server-side.

## Local development

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
flask --app run.py db upgrade
python -m pytest -q
flask --app run.py run --debug
```

The application defaults to SQLite for a lightweight developer mode. Use PostgreSQL by setting `DATABASE_URL`. The app does not create tables at startup; migrations are applied explicitly with Flask-Migrate. AI is optional and never required by tests or core CRUD.

## Docker Compose

```bash
docker compose up --build
curl http://localhost:5000/health/ready
```

Compose starts PostgreSQL and the app. The container entrypoint runs `flask db upgrade` before Gunicorn. Compose credentials are development-only and must not be reused in production. Use a secret manager and a managed PostgreSQL backup strategy for production.

## API examples with curl

The API uses a session cookie for authentication. The following commands assume the application is running at `http://localhost:5000` and require `jq` for extracting the CSRF token. They store the session cookie in `/tmp/bugtrack-ai.cookies` so each request uses the same login session.

```bash
BASE_URL=http://localhost:5000
COOKIE_JAR=/tmp/bugtrack-ai.cookies
EMAIL="ada@example.com"
PASSWORD="password123"

# 1. Register and log in. Registration logs the user in automatically.
curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -X POST "$BASE_URL/api/auth/register" \
  -d "{\"name\":\"Ada Lovelace\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"

# If the account already exists, use login instead.
curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -H 'Content-Type: application/json' \
  -X POST "$BASE_URL/api/auth/login" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"

# 2. Get a CSRF token for state-changing API requests.
CSRF_TOKEN=$(curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  "$BASE_URL/api/auth/csrf" | jq -r '.csrf_token')

# 3. Create a project.
PROJECT=$(curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -H 'Content-Type: application/json' -H "X-CSRFToken: $CSRF_TOKEN" \
  -X POST "$BASE_URL/api/projects" \
  -d '{"name":"Web Platform","key":"WEB","description":"BugTrack AI web platform"}')
PROJECT_ID=$(printf '%s' "$PROJECT" | jq -r '.id')

# 4. Create a bug in that project.
BUG=$(curl -sS -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  -H 'Content-Type: application/json' -H "X-CSRFToken: $CSRF_TOKEN" \
  -X POST "$BASE_URL/api/bugs" \
  -d "{\"project_id\":$PROJECT_ID,\"title\":\"Login button fails\",\"description\":\"The login button returns an error\",\"severity\":\"HIGH\",\"priority\":\"P1\",\"reproduction_steps\":\"Open login, enter valid credentials, submit\",\"expected_behavior\":\"The dashboard opens\",\"actual_behavior\":\"The request returns an error\"}")
BUG_ID=$(printf '%s' "$BUG" | jq -r '.id')

# 5. Search, filter, sort, and paginate accessible bugs.
curl -sS -b "$COOKIE_JAR" \
  "$BASE_URL/api/bugs?q=login&severity=HIGH&sort=newest&page=1&per_page=20"

# 6. Read, update, and comment on the bug.
curl -sS -b "$COOKIE_JAR" "$BASE_URL/api/bugs/$BUG_ID"
curl -sS -b "$COOKIE_JAR" \
  -H 'Content-Type: application/json' -H "X-CSRFToken: $CSRF_TOKEN" \
  -X PUT "$BASE_URL/api/bugs/$BUG_ID" \
  -d '{"status":"IN_PROGRESS","assigned_to":null}'
curl -sS -b "$COOKIE_JAR" \
  -H 'Content-Type: application/json' -H "X-CSRFToken: $CSRF_TOKEN" \
  -X POST "$BASE_URL/api/bugs/$BUG_ID/comments" \
  -d '{"content":"The issue is being investigated."}'

# 7. Request optional AI analysis. This returns 503 when no AI provider is configured.
curl -sS -b "$COOKIE_JAR" \
  -H "X-CSRFToken: $CSRF_TOKEN" \
  -X POST "$BASE_URL/api/bugs/$BUG_ID/analyze"

# 8. Health, readiness, metrics, current user, and logout.
curl -sS "$BASE_URL/health/live"
curl -sS "$BASE_URL/health/ready"
curl -sS "$BASE_URL/metrics"
curl -sS -b "$COOKIE_JAR" "$BASE_URL/api/auth/me"
curl -sS -b "$COOKIE_JAR" -H "X-CSRFToken: $CSRF_TOKEN" -X POST "$BASE_URL/api/auth/logout"
```

For scripts that do not have `jq`, keep the complete JSON response from `/api/auth/csrf` and copy its `csrf_token` value into the `X-CSRFToken` header. Never put `SECRET_KEY`, database passwords, or AI provider keys in curl commands that may be saved in shell history.

## GitHub Actions and GHCR

`.github/workflows/ci.yml` is the only CI/CD workflow. Pull requests and pushes run linting, PostgreSQL-backed tests, migration smoke tests, dependency auditing, secret detection, YAML validation, and optional SonarQube. Pushes to `main` additionally build a non-root image, scan it with Trivy, publish an immutable SHA tag to GHCR, and update both GitOps overlays. `paths-ignore` prevents GitOps image commits from causing a release loop; concurrency cancels stale runs.

Required repository configuration: `SONAR_TOKEN` and `SONAR_HOST_URL` only when SonarQube is available. GHCR publishing uses the short-lived built-in `GITHUB_TOKEN` with `packages: write`; no registry password is needed. The package is `ghcr.io/mengyokyu/bugtrack-ai`.

## Kubernetes and GitOps

Create the runtime Secret out of band; `k8s/secret.example.yaml` is not part of the Kustomize resource chain:

```bash
minikube start
kubectl create namespace bugtrack
kubectl -n bugtrack create secret generic bugtrack-secrets \
  --from-literal=DATABASE_URL='postgresql+psycopg2://bugtrack:<password>@postgres:5432/bugtrack' \
  --from-literal=SECRET_KEY='<random-value>' \
  --from-literal=AI_API_KEY=''
kubectl apply -k k8s/
```

The manifests include blue/green Deployments, rolling-update controls, startup/readiness/liveness probes, resource requests and limits, HPA, NetworkPolicy, RBAC, ConfigMap, and persistent PostgreSQL storage. For GitOps, apply `gitops/argocd-application.yaml` after replacing the image tag through the release workflow. Argo CD is the deployment authority; CI only updates Git.

For promotion, update the active overlay in Git and let Argo CD sync. The existing `k8s/switch-blue-green.sh` is a local demonstration helper only; it is not the GitOps promotion mechanism and should not be used against an Argo-managed production Service.

## Ansible and Terraform

Ansible playbooks bootstrap a Linux development host, install Docker and Minikube prerequisites, create directories, and apply manifests. They contain no production credentials. Terraform is limited to the explicitly declared local Kubernetes provider/module scope; it must not independently manage resources owned by Argo CD. Validate with `terraform fmt -check`, `terraform init`, `terraform validate`, and `terraform plan` when a kubeconfig is available.

## Observability and security

`/health/live` checks process liveness, `/health/ready` checks database readiness, and `/metrics` exposes request, latency, error, health, database, and bug-lifecycle metrics. Prometheus rules and a Grafana dashboard are under `monitoring/`. Application logs go to stdout with request IDs; Fluentd can forward Kubernetes logs to Elasticsearch for Kibana search. The Docker image runs as non-root, drops Linux capabilities, uses secure response headers, and contains no secrets. Trivy blocks HIGH and CRITICAL findings when the release environment is configured.

## Validation

```bash
source .venv/bin/activate
ruff check app tests run.py --ignore E701,E702
python -m pytest -q --cov=app
SECRET_KEY=test python -m compileall app run.py
```

Offline validation is performed when Docker, Kubernetes, Terraform, Ansible, or full logging services are not installed. The final report must distinguish static validation from a real cluster deployment.

See `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/DEPLOYMENT.md`, and `docs/TROUBLESHOOTING.md` for operational details.
