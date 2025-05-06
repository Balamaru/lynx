# Repository to Learn About ETL Processing
## 1. Prequisite
In every tools that we use, we would running them on Kubernetes
- Kubernetes cluster installed
- Kubectl with admin access
- Helm installed
- Storage class installed (Recommended File System : nfs, ceph fs, etc)

## 2. Testing the ETL Process
After setting up the environment and all the resources was running, we can test the ETL process

- Create a ConfigMap for the Spark-job in namespace where Spark-operator was installed
```bash
kubectl create configmap example-job-py -n zeatarou --from-file=example_job.py=/Spark-operator/spark-job/example_job.py
```

- Copy DAG and SparkApplication to airflow-scheduler pod
```bash
kubectl cp /Spark-operator/applications/example-spark-job.yaml.j2 airflow/airflow-scheduler-pod-name:/opt/airflow/dags/
kubectl cp /Apache-airflow/dags/dag_for_example_job.py airflow/airflow-scheduler-pod-name:/opt/airflow/dags/
```

- Check if DAG was successfully define to airflow-scheduler
```bash
kubectl exec -it -n airflow airflow-scheduler-pod-name -- airflow dags list

# output
dag_id               | fileloc                               | owners  | is_paused
=====================+=======================================+=========+==========
spark_python_job     | /opt/airflow/dags/spark_python_job.py | airflow | None
```

- Running the DAG in Airflow UI

After doing all the steps above, we can see the ETL process was running in Airflow UI. Log of the process can be seen in Airflow UI as well.


## 3. Running the Spark-job Where Need a Packages
In real cases, when defining spark-jobs, there are many connections or methods needed, to support this often requires its own packages. For example, the data we want to use is in the s3 bucket and after being transformed will be stored in the database, this requires its own packages. unlike if we run spark-job directly with spark running on the local computer. When running spark-job on a cluster, we must ensure that all required packages are installed first, to overcome this there are many methods that can be used, creating a custom image with packages as a Dockerfile, or using Spark Operator which can install packages automatically, creating a job to download packages and store them in a storage that can be accessed by our kubernetes cluster (pvc). In this tutorial we will use a job to download packages and store them in a storage that can be accessed by the kubernetes cluster. This part using public dataset where we can download the dataset [here](https://www.kaggle.com/datasets/willianoliveiragibin/uk-property-price-data-1995-2023-04).

- Create PVC to store the packages
```bash
kubectl apply -f kubernetes/jars-dependencies.yaml
```

- Create a job to download packages
```bash
kubectl apply -f kubernetes/download-jar-dependencies.yaml
```

- Create Secret to store credentials
```bash
kubectl create secret generic aws-credentials -n zeatarou \
  --from-literal=access_key=acces_key \
  --from-literal=secret_key=secret_key

kubectl create secret generic aws-credentials -n airflow \
  --from-literal=access_key=acces_key \
  --from-literal=secret_key=secret_key
```

- Creat a ConfigMap for the new Spark-job in namespace where Spark-operator was installed
```bash
kubectl create configmap s3-job-py -n zeatarou --from-file=s3_job.py=/Spark-operator/spark-job/s3_job.py
```

- Copy DAG and SparkApplication to airflow-scheduler pod
```bash
kubectl cp /Spark-operator/applications/s3-spark-job.yaml.j2 airflow/airflow-scheduler-pod-name:/opt/airflow/dags/
kubectl cp /Apache-airflow/dags/dag-s3.py airflow/airflow-scheduler-pod-name:/opt/airflow/dags/
```

- Running the DAG in Airflow UI

## 4. Acces File From Compatible S3 Storage, and Manipulation of Data
Accescing file from aws s3 or s3 compatible using the same method, but we need to adding another jars dependencies where can acces the endpoint of s3 storage. In this part we will use public data where can be acces [here](https://www.kaggle.com/datasets/mohamedbakhet/amazon-books-reviews/data).

- Create secret like previous part, with s3 compatible credentials with name s3-credentials in namespace where Spark-operator and Airflow was installed

- Reapply job to download jar packages
```bash
kubectl apply -f kubernetes/download-jar-dependencies.yaml
```

- Create a ConfigMap for the new Spark-job in namespace where Spark-operator was installed
```bash
kubectl create configmap book-job-py -n zeatarou --from-file=s3_compatible.py=/Spark-operator/spark-job/s3_compatible.py
```

- Copy DAG and SparkApplication to airflow-scheduler pod
```bash
kubectl cp /Spark-operator/applications/s3_compatible.yaml.j2 airflow/airflow-scheduler-pod-name:/opt/airflow/dags/
kubectl cp /Apache-airflow/dags/s3_compatible.py airflow/airflow-scheduler-pod-name:/opt/airflow/dags/
```

- Running the DAG in Airflow UI

# Reference
- [Deploying Spark on Kubernetes using Helm Charts: Simplified Cluster Management and Configuration](https://medium.com/@SaphE/deploying-apache-spark-on-kubernetes-using-helm-charts-simplified-cluster-management-and-ee5e4f2264fd)
- [Helm chart for Spark on Kubernetes operator.](https://github.com/kubeflow/spark-operator/tree/master/charts/spark-operator-chart)
- [Helm Chart for Apache Airflow](https://airflow.apache.org/docs/helm-chart/stable/index.html)
- [Connect to AWS S3 and Read Files Using Apache Spark](https://medium.com/@Shamimw/connect-to-aws-s3-and-read-files-using-apache-spark-186943a5169a)
- [Spark SQL Documentation](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/index.html)