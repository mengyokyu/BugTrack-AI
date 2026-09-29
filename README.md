# BugTrack AI

A deliberately small Flask + PostgreSQL bug tracker built to demonstrate an end-to-end DevOps capstone. **GitHub Actions replaces Jenkins** as the CI/CD engine; Argo CD remains the Kubernetes deployment authority.

## Features

Register/login/logout, bug CRUD, status and severity changes, comments, responsive vanilla HTML/CSS/JS UI, REST API, health endpoint, Prometheus metrics, optional LLM analysis, clean error handling, and PostgreSQL support.

## Local development

```bash
cp .env.example .env
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
flask --app run.py run --debug
```

The default local database is SQLite. Set `DATABASE_URL` to PostgreSQL for production-like testing. AI is optional: set `AI_API_KEY`, `AI_API_URL`, and `AI_MODEL`; without a key the analysis endpoint returns `503` while the rest of the application works.

## Docker

```bash
docker compose up --build
curl http://localhost:5000/health
```

The image uses a slim Python base, a non-root user, no embedded secrets, and a health check.

## GitHub Actions CI/CD

`.github/workflows/ci.yml` runs on pushes and pull requests. It checks out the code, installs dependencies, runs Ruff and pytest/coverage, optionally runs SonarQube, builds the image, scans it with Trivy, pushes a SHA-tagged image when registry secrets exist, and updates GitOps image tags on `main`.

Configure these encrypted repository secrets as needed: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `SONAR_TOKEN`, `SONAR_HOST_URL`, and `AI_API_KEY`. GitHub's built-in `GITHUB_TOKEN` is used for GitOps commits. The workflow does not contain credentials.

## Kubernetes / Minikube

```bash
minikube start
kubectl apply -k k8s/
kubectl -n bugtrack get pods,svc,pvc
kubectl -n bugtrack scale deployment/bugtrack-blue --replicas=3
kubectl -n bugtrack rollout status deployment/bugtrack-blue
kubectl -n bugtrack rollout history deployment/bugtrack-blue
kubectl -n bugtrack rollout undo deployment/bugtrack-blue
./k8s/switch-blue-green.sh green
./k8s/switch-blue-green.sh blue
```

Create real secrets locally from the example and do not commit them:

```bash
kubectl apply -f k8s/secret.example.yaml
```

Blue and green deployments share the application image. The Service selector switches traffic. Readiness/liveness probes support rolling updates and rollback.

## Ansible

Playbooks in `ansible/playbooks/` install Docker, install kubectl/Minikube, configure a local host, and apply manifests. Validate with `ansible-playbook --syntax-check ansible/playbooks/*.yml`.

## Terraform

The Kubernetes provider and reusable `terraform/modules/kubernetes` module provision a namespace, ConfigMap, and Service without cloud resources:

```bash
cd terraform
terraform init
terraform validate
terraform plan
terraform apply
terraform destroy
```

## Monitoring and logging

`/metrics` exposes request count, latency, health, and status labels. Prometheus configuration is in `monitoring/prometheus/prometheus.yml`; Grafana dashboard JSON is in `monitoring/grafana/dashboard.json`. Fluentd tails Kubernetes container logs and forwards them to Elasticsearch; Kibana is the search/visualization layer.

## GitOps with Argo CD

`gitops/` contains Kustomize base and blue/green overlays. Apply an Argo CD Application pointing at this repository and `gitops/overlays/blue` (or green). Argo CD detects image-tag commits and synchronizes Kubernetes. Git is the desired state; GitHub Actions never directly deploys application resources.

## Security

No real secrets are committed. The image is non-root and Trivy blocks HIGH/CRITICAL findings. Kubernetes uses a ServiceAccount, Role, RoleBinding, Secret, dropped capabilities, and probes. SonarQube settings are in `security/sonar-project.properties`.

## Validation

```bash
python -m pytest -q
ruff check app tests run.py --ignore E701,E702
python -m compileall app run.py
```

See [ARCHITECTURE.md](ARCHITECTURE.md), [DEMO.md](DEMO.md), [VIVA.md](VIVA.md), and [docs/report-outline.md](docs/report-outline.md).
