resource "kubernetes_namespace" "this" { metadata { name = var.namespace } }
resource "kubernetes_config_map" "this" { metadata { name = "bugtrack-config", namespace = kubernetes_namespace.this.metadata[0].name }; data = { AI_MODEL = "gpt-4o-mini" } }
resource "kubernetes_service" "this" { metadata { name = "bugtrack", namespace = kubernetes_namespace.this.metadata[0].name }; spec { selector = { app = "bugtrack", version = "blue" }; port { port = 80; target_port = 5000 } } }
