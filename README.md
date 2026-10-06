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
