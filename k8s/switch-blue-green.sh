#!/usr/bin/env bash
set -euo pipefail
version=${1:?Usage: $0 blue|green}
[[ "$version" == blue || "$version" == green ]] || exit 2
kubectl -n bugtrack patch service bugtrack --type merge -p "{\"spec\":{\"selector\":{\"app\":\"bugtrack\",\"version\":\"$version\"}}}"
kubectl -n bugtrack rollout status deployment/bugtrack-$version
