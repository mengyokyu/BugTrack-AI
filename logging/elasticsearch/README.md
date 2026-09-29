# Centralized logging

Run Elasticsearch and Kibana locally with the official images, then apply the Fluentd DaemonSet in the cluster. Fluentd tails Kubernetes container logs and forwards structured records to Elasticsearch; Kibana searches and visualizes the index.
