# Security controls

GitHub Actions stores Docker Hub, SonarQube, and AI credentials as encrypted repository secrets. Kubernetes secrets are represented only by `secret.example.yaml`; create a local Secret from an ignored file before deployment. The image runs as a non-root user, Trivy blocks high/critical findings, and RBAC limits the application ServiceAccount to read-only configuration access.
