terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}

resource "kubernetes_namespace" "airflow" {
  metadata {
    name = "airflow"
  }
}

resource "kubernetes_namespace" "zeatarou" {
  metadata {
    name = "zeatarou"
  }
}

resource "helm_release" "airflow" {
  name       = "airflow"
  repository = "https://airflow.apache.org"
  chart      = "airflow"
  namespace  = kubernetes_namespace.airflow.metadata[0].name

  values = [
    file("/airflow/values.yaml")
  ]

  depends_on = [
    kubernetes_namespace.airflow
  ]
}

resource "helm_release" "zeatarou" {
  name       = "zeatarou"
  repository = "https://kubeflow.github.io/spark-operator"
  chart      = "spark-operator"
  namespace  = kubernetes_namespace.zeatarou.metadata[0].name

  values = [
    file("/spark/values.yaml")
  ]

  depends_on = [
    kubernetes_namespace.zeatarou
  ]
}






resource "kubernetes_role" "airflow-worker-role" {
  metadata {
    name      = "airflow-worker-role"
    namespace = kubernetes_namespace.zeatarou.metadata[0].name
  }

  rule {
    api_groups = [""]
    resources  = ["pods"]
    verbs      = ["get", "list", "watch", "create", "delete"]
  }

  rule {
    api_groups = [""]
    resources  = ["events"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = ["batch"]
    resources  = ["jobs"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }

  rule {
    api_groups = ["sparkoperator.k8s.io"]
    resources  = ["sparkapplications"]
    verbs      = ["get", "list", "watch", "create", "delete"]
  }

  depends_on = [
    helm_release.zeatarou
  ]
}

resource "kubernetes_role_binding" "airflow-worker-rolebinding" {
  metadata {
    name      = "airflow-worker-rolebinding"
    namespace = kubernetes_namespace.zeatarou.metadata[0].name
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.airflow-worker-role.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = "airflow-worker"
    namespace = kubernetes_namespace.airflow.metadata[0].name
  }

  depends_on = [
    kubernetes_role.airflow-worker-role,
    helm_release.zeatarou
  ]
}

resource "kubernetes_role" "spark-driver-role" {
  metadata {
    name      = "spark-driver-role"
    namespace = kubernetes_namespace.zeatarou.metadata[0].name
  }

  rule {
    api_groups = [""]
    resources  = ["pods", "services"]
    verbs      = ["create", "get", "list", "watch", "delete"]
  }

  rule {
    api_groups = [""]
    resources  = ["pods/log", "configmaps"]
    verbs      = ["get", "list", "watch"]
  }

  rule {
    api_groups = ["batch"]
    resources  = ["jobs"]
    verbs      = ["create", "get", "list", "watch", "delete"]
  }

  depends_on = [
    helm_release.spark_operator
  ]
}

resource "kubernetes_role_binding" "spark-driver-rolebinding" {
  metadata {
    name      = "spark-driver-rolebinding"
    namespace = kubernetes_namespace.zeatarou.metadata[0].name
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.spark-driver-role.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = "${var.release_name}-spark-operator-spark" # Menggunakan nilai dari variabel
    namespace = kubernetes_namespace.zeatarou.metadata[0].name
  }

  depends_on = [
    kubernetes_role.spark-driver-role,
    helm_release.zeatarou
  ]
}
