# Troubleshooting

- **SECRET_KEY error:** set a strong `SECRET_KEY`; production intentionally refuses insecure defaults.
- **Database not ready:** check `docker compose ps`, PostgreSQL health, and `DATABASE_URL`; then run `flask --app run.py db upgrade`.
- **401/403 responses:** authenticate first; a 403 means the current user does not own, belong to, or have assignment access to the bug/project.
- **CSRF validation failed:** obtain `/api/auth/csrf` and send its value as `X-CSRFToken`; the browser client does this automatically.
- **Argo CD drift:** do not patch an Argo-managed Service imperatively; make the promotion change in Git and sync the Application.
- **GHCR publish failure:** verify package permissions and that the workflow runs on `main`; the built-in `GITHUB_TOKEN` must have `packages: write`.
- **Trivy failure:** inspect HIGH/CRITICAL findings, update dependencies/base image, or document a justified exception. Do not silently disable the scan.
