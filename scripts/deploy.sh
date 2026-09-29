#!/usr/bin/env bash
set -euo pipefail
kubectl apply -k k8s/
kubectl -n bugtrack rollout status deployment/bugtrack-blue
