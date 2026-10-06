# BugTrack AI architecture

The browser talks to a Flask modular monolith over HTML routes and JSON APIs. Flask-SQLAlchemy persists users, projects, bugs, comments, activity events, and optional AI analyses in PostgreSQL. Flask-Migrate owns schema changes. Sessions authenticate users; role and ownership checks authorize every protected bug/project operation.

GitHub Actions is responsible for verification, migrations smoke tests, dependency/secret/security checks, image build and publication, and GitOps tag updates. Argo CD watches the Git-managed Kustomize overlay and reconciles Kubernetes. Terraform and Ansible are bootstrap tools with documented non-overlapping scope.

Kubernetes runs blue and green application Deployments behind one Service, plus PostgreSQL persistence. Prometheus scrapes `/metrics`; Grafana visualizes metrics; Fluentd forwards stdout/container logs to Elasticsearch, where Kibana provides search.
