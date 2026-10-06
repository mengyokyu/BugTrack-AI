# Deployment and recovery

## Local Docker

Run `docker compose up --build`; the app waits for PostgreSQL and applies migrations through `scripts/entrypoint.sh`. Back up the development database with `pg_dump` and restore it with `psql`; production backups must be scheduled and encrypted by the database operator.

## Kubernetes

Create the runtime Secret out of band, apply `kubectl apply -k k8s/`, and verify `kubectl -n bugtrack rollout status deployment/bugtrack-blue`. Scale with `kubectl -n bugtrack scale deployment/bugtrack-blue --replicas=3`; inspect revisions with `rollout history`; roll back with `rollout undo`.

## GitOps promotion

GitHub Actions publishes `ghcr.io/mengyokyu/bugtrack-ai:<commit-sha>` and edits the blue/green overlay tag. Argo CD detects the Git commit and syncs it. Promote by changing the Service selector in the intended overlay through Git, waiting for candidate readiness, and allowing Argo CD to sync. Roll back by reverting the Git commit. Database migrations must be backward-compatible across both colors.
