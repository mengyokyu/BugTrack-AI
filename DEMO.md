# 10-minute demonstration

1. **0:00–0:30 — Repository:** show GitHub repository, `main`/`develop`, feature branches, and recent conventional commits.
2. **0:30–1:30 — Application:** start `docker compose up --build`; open the login/register UI.
3. **1:30–2:30 — CRUD:** register, create a CRITICAL bug, update its status, add a comment, and show the REST response.
4. **2:30–3:00 — AI:** click Analyze; explain that missing AI credentials produce a clean unavailable response without breaking CRUD.
5. **3:00–4:00 — CI:** push a small change and show GitHub Actions running lint, pytest, coverage, optional SonarQube, Docker build, and Trivy.
6. **4:00–5:00 — Image:** show the commit-SHA image tag and Trivy policy; point out non-root Dockerfile user.
7. **5:00–6:00 — Kubernetes:** run `kubectl apply -k k8s/`; show namespace, pods, Service, ConfigMap, Secret template, and PVC.
8. **6:00–7:00 — Reliability:** show `kubectl scale`, `rollout status`, `rollout history`, and `rollout undo`.
9. **7:00–8:00 — Blue/green:** run `./k8s/switch-blue-green.sh green`, verify the Service selector, then switch back to blue.
10. **8:00–9:00 — Observability:** show `/metrics`, Prometheus targets, and the Grafana dashboard panels.
11. **9:00–9:30 — Logging:** show Fluentd configuration and Elasticsearch/Kibana log search.
12. **9:30–10:00 — GitOps:** show the Argo CD Application, desired Git revision, sync status, and explain that Argo CD—not GitHub Actions—deploys to Kubernetes.
