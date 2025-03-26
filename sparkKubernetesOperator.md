# Menjalankan Spark Job dengan Airflow by SparkKubernetesOperator
- Spark-operator running on spark-operator namespace
- airflow running on airflow namespace with KubernetesExecutor
## 1. Create configmap of your spark-job
```bash
kubectl create configmap spark-job -n spark-operator --from-literal=spark-job.py=/path/to/spark-job.py
```
## 2. Create Airflow DAG with SparkKubernetesOperator
```python
# airflow-dag.py
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator
from airflow.utils.dates import days_ago

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(1),
}

dag = DAG(
    "spark_python_job",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
)

submit_spark_job = SparkKubernetesOperator(
    task_id='submit_spark_python_job',
    namespace='spark-operator',
    application_file="spark-application.yaml",
    is_delete_operator_pod=False,
    in_cluster=True,
    do_xcom_push=False,
    dag=dag,
)

submit_spark_job
```

Make sure that we must store the spark-application.yaml and airflow-dag.py in the same directory of container where airflow-scheduler running, otherwise we must mount the directory to container with volume mount in Kubernetes deployment of airflow-scheduler.

## 3. RBAC
```bash
kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=spark-operator:spark-operator-spark --namespace=spark-operator
kubectl create clusterrolebinding default-admin --clusterrole cluster-admin --serviceaccount=airflow:airflow-worker --namespace spark-operator
```
Another rbac that can be used, optionally but recommended if our SparkApplication want to acces spark-job configmap
```yaml
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: spark-operator-role
  namespace: spark-operator
rules:
- apiGroups: ["sparkoperator.k8s.io"]
  resources: ["sparkapplications"]
  verbs: ["create", "delete", "get", "list", "patch", "update", "watch"]
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: airflow-spark-operator-binding
  namespace: spark-operator
subjects:
- kind: ServiceAccount
  name: default
  namespace: airflow
- kind: ServiceAccount
  name: spark-operator-spark
  namespace: spark-operator
roleRef:
  kind: Role
  name: spark-operator-role
  apiGroup: rbac.authorization.k8s.io
```