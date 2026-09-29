# BugTrack AI architecture

## Application

A Flask modular monolith serves HTML pages and REST APIs. Flask-SQLAlchemy persists users, bugs, comments, and optional AI analyses. Session authentication keeps the implementation small. The AI provider is isolated in `app/ai.py` and is never required for core CRUD.

## CI/CD

GitHub Actions is the CI/CD control plane. Pull requests run lint, tests, coverage, and optional SonarQube. Pushes build a SHA-tagged image, run Trivy, publish to a configurable registry, and update the GitOps overlay. Secrets are GitHub encrypted secrets.

## Kubernetes

Minikube hosts the `bugtrack` namespace. PostgreSQL uses a PVC backed by a local PV. Blue and green application Deployments use the same Service; the Service selector chooses the active color. ConfigMap carries non-sensitive settings, Secret carries credentials, and RBAC limits the ServiceAccount.

## GitOps

Argo CD watches `gitops/overlays/blue` or `green`. GitHub Actions changes the desired image tag; Argo CD synchronizes it. No CI job directly applies application resources, avoiding competing deployment authorities.

## Observability

The application emits structured request logs and Prometheus metrics. Prometheus scrapes `/metrics`; Grafana consumes Prometheus for request rate, errors, latency, and health. Fluentd tails container logs and sends them to Elasticsearch, with Kibana as the query interface.

## Security

Credentials are externalized, images run without root, Trivy scans dependencies/images, SonarQube checks code quality, Kubernetes capabilities are dropped, and RBAC is explicit. Production deployments should replace local hostPath storage and example image names with environment-specific values.
