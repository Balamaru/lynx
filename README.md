# Repository to Learn About ETL Processing
## 1. Prequisite
In every tools that we use, we would running them on Kubernetes
- Kubernetes cluster installed
- Kubectl with admin access
- Helm installed
- Storage class installed (Recommended File System : nfs, ceph fs, etc)

## 2. Testing the ETL Process
After setting up the environment and all the resources was running, we can test the ETL process 
- Create a RBAC to enabled running Spark-job with Airflow
```bash
kubectl apply -f kubernetes/rbac.yaml
```

- Create a ConfigMap for the Spark-job in namespace where Spark-operator was installed
```bash
kubectl create configmap example-job-py -n zeatarou --from-file=example_job.py=/Spark-operator/spark-job/example_job.py
```

- Create a ConfigMap for the Spark Application in namespace where Airflow was Installed
```bash
kubectl create spark-python-job -n airflow --from-file=/Spark-operator/applications/example-spark-job.yaml
```

- Copy DAG to airflow-scheduler pod
```bash
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

- Running the DAG in Airflow UI, or using command line with this command
```bash
kubectl exec -it -n airflow airflow-scheduler-pod-name -- airflow dags trigger spark_python_job
```

After doing all the steps above, we can see the ETL process was running in Airflow UI.
```bash
# make sure that any spark application was SUBMITED or COMPLETED
kubectl get sparkapp -n zeatarou

# output
NAME                STATUS      ATTEMPTS   START                  FINISH                 AGE
example-spark-job   COMPLETED   1          2025-03-13T05:22:52Z   2025-03-13T05:23:25Z   5m
```
Check the result of the ETL process on pod was created in namespace where Spark-operator was installed.
```bash
kubectl get pods -n zeatarou
    # output
    NAME                                                  READY   STATUS      RESTARTS      AGE
    example-spark-job-driver                              0/1     Completed   0             5m

# and the result of the ETL process is in the pod
kubectl logs -f example-spark-job-driver -n zeatarou
```

## 3. Running the Spark-job Where Need a Packages
In real cases, when defining spark-jobs, there are many connections or methods needed, to support this often requires its own packages. For example, the data we want to use is in the s3 bucket and after being transformed will be stored in the database, this requires its own packages. unlike if we run spark-job directly with spark running on the local computer. When running spark-job on a cluster, we must ensure that all required packages are installed first, to overcome this there are many methods that can be used, creating a custom image with packages as a Dockerfile, or using Spark Operator which can install packages automatically, creating a job to download packages and store them in a storage that can be accessed by our kubernetes cluster (pvc). In this tutorial we will use a job to download packages and store them in a storage that can be accessed by the kubernetes cluster.

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

- Create a ConfigMap for the Spark Application in namespace where Airflow was Installed
```bash
kubectl create configmap spark-s3-job -n airflow --from-file=/Spark-operator/applications/s3-spark-job.yaml
```

- Copy DAG to airflow-scheduler pod
```bash
kubectl cp /Apache-airflow/dags/dag-s3.py airflow/airflow-scheduler-pod-name:/opt/airflow/dags/
```

- Check if DAG was successfully define to airflow-scheduler
```bash
kubectl exec -it -n airflow airflow-scheduler-pod-name -- airflow dags list

# output
dag_id               | fileloc                               | owners  | is_paused
=====================+=======================================+=========+==========
spark_python_job     | /opt/airflow/dags/spark_python_job.py | airflow | None
UK_PRICE             | /opt/airflow/dags/dag-s3.py           | airflow | None
```

- Running the DAG in Airflow UI, or using command line with this command
```bash
kubectl exec -it -n airflow airflow-scheduler-pod-name -- airflow dags trigger UK_PRICE
```