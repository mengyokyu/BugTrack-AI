module "kubernetes" { source = "./modules/kubernetes", namespace = var.namespace, image = var.image }
