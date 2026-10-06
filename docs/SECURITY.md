# Security controls and limitations

Application controls include Werkzeug password hashing, production secret enforcement, secure session cookie defaults, CSRF validation for state-changing browser/API requests, input validation, server-side ownership/RBAC checks, request IDs, security headers, rate limits on login and AI analysis, and generic production errors. Dynamic user content is escaped by the browser client.

CI uses pinned dependencies, pip-audit, secret detection, SonarQube when configured, and Trivy image scanning. The release workflow uses the ephemeral `GITHUB_TOKEN` for GHCR rather than a long-lived registry password. Kubernetes uses a ServiceAccount, least-privilege Role, security contexts, resource limits, and NetworkPolicy.

The example Secret is a template only and is excluded from Kustomize. Production still requires an external secret manager, TLS, managed database backups, and a real cluster policy review. The in-memory rate-limit store is suitable for one-process development only; use a shared limiter backend for horizontally scaled production.
