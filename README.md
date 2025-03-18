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
