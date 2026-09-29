variable "kubeconfig" { type = string, default = "~/.kube/config" }
variable "namespace" { type = string, default = "bugtrack" }
variable "image" { type = string, default = "ghcr.io/example/bugtrack-ai:latest" }
