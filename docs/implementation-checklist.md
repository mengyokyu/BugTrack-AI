# Improvement checklist

- [x] Repository audit and dedicated feature branch
- [x] Roles, ownership checks, validation, filtering, sorting, pagination, projects, assignments, and activity history
- [x] Explicit Flask-Migrate workflow and production secret enforcement
- [x] CSRF, secure headers/cookies, rate limits, generic errors, and security tests
- [x] PostgreSQL-backed CI and migration smoke test
- [x] GHCR immutable release workflow with Trivy and GitOps loop prevention
- [x] Kubernetes resources, probes, HPA, NetworkPolicy, and external runtime Secret
- [x] Operational documentation updated
- [ ] Live Kubernetes, Terraform, Ansible, and logging-stack deployment (requires corresponding local tools/cluster)
- [ ] GHCR package publication (requires repository package permissions and a successful release run)
