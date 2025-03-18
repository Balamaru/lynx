# Setup Airflow
```bash
# adding helm repo
helm repo add apache-airflow https://airflow.apache.org
helm repo update

helm install airflow apache-airflow/airflow -f values.yaml -n airflow --create-namespace --debug
```