# Menjalankan Spark Job dengan Airflow by SparkKubernetesOperator
- Spark-operator running on spark-operator namespace
- airflow running on airflow namespace with KubernetesExecutor
## 1. Create configmap of your spark-job and reapply the s3-credentials in the namespace spark-operator
```bash
kubectl create secret generic aws-credentials -n spark-operator \
  --from-literal=access_key=acces_key \
  --from-literal=secret_key=secret_key

kubectl create configmap s3-job-py -n spark-operator --from-file=s3_job.py=/Spark-operator/spark-job/s3_job.py
```
## 2. Edit the SparkApplication 
```yaml
apiVersion: "sparkoperator.k8s.io/v1beta2"
kind: SparkApplication
metadata:
  name: {{ params.job_name }}
spec:
  type: Python
  mode: cluster
  image: "spark:3.5.3"
  imagePullPolicy: Always
  mainApplicationFile: "local:///opt/spark/work-dir/s3_compatible.py"
  sparkVersion: "3.5.3"
  restartPolicy:
    type: Never
  hadoopConf:
    "fs.s3a.access.key": "acces_key"
    "fs.s3a.secret.key": "secret_key"
    "fs.s3a.endpoint": "https://s3-penyedia-layanan.com"
    "fs.s3.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem"
    "fs.s3a.path.style.access": "true"
    "fs.s3a.aws.credentials.provider": "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider"
    "fs.s3a.experimental.input.fadvise": "sequential"
    "mapreduce.fileoutputcommitter.algorithm.version": "2"
  volumes:
    - name: s3-job-volume
      configMap:
        name: book-job-py
    - name: jars-volume
      persistentVolumeClaim:
        claimName: spark-jars-pvc
  driver:
    cores: 1
    memory: "1G"
    labels:
      version: 3.5.3
    serviceAccount: zeatarou-spark-operator-spark
    volumeMounts:
      - name: s3-job-volume
        mountPath: /opt/spark/work-dir
      - name: jars-volume
        mountPath: /opt/spark/jars/shared
    envFrom:
      - secretRef:
          name: s3-credentials
  executor:
    cores: 1
    instances: 2
    memory: "1G"
    labels:
      version: 3.5.3
    volumeMounts:
      - name: s3-job-volume
        mountPath: /opt/spark/work-dir
      - name: jars-volume
        mountPath: /opt/spark/jars/shared
    envFrom:
      - secretRef:
          name: s3-credentials
  sparkConf:
    "spark.driver.extraClassPath": "/opt/spark/jars/shared/*"
    "spark.executor.extraClassPath": "/opt/spark/jars/shared/*"
    "spark.hadoop.fs.s3a.access.key": "acces_key"
    "spark.hadoop.fs.s3a.secret.key": "secret_key"
    "spark.hadoop.fs.s3a.endpoint": "https://s3-penyedia-layanan.com"
    "spark.hadoop.fs.s3.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem"
    "spark.hadoop.fs.s3a.path.style.access": "true"
    "spark.hadoop.fs.s3a.connection.ssl.enabled": "true"
    "spark.hadoop.fs.s3a.aws.credentials.provider": "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider"
    "spark.hadoop.fs.s3a.experimental.input.fadvise": "sequential"
```

## 3. Create Airflow DAG with SparkKubernetesOperator
```python
# airflow-dag.py
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator
from airflow.utils.dates import days_ago
from jinja2 import StrictUndefined


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(1),
}

dag = DAG(
    "book-job",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    template_undefined=StrictUndefined,
)

class CustomSparkKubernetesOperator(SparkKubernetesOperator):
    template_ext = ('.yaml', '.yaml.j2')
    template_fields = ('application_file',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

submit_spark_job = CustomSparkKubernetesOperator(
    task_id="book-job", #task id in airflow-dag will be a spesific name of spark-driver will be created
    namespace="spark-operator",
    application_file="book-job.yaml.j2",
    kubernetes_conn_id="kubernetes_default",
    in_cluster=True,
    do_xcom_push=False,
    get_logs=True,
    log_events_on_failure=True,
    params={"job_name": "book-job"},
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