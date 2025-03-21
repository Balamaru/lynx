from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime, timedelta
from kubernetes.client import models as k8s

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 3, 13),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'book_job',
    default_args=default_args,
    schedule_interval=timedelta(days=1),
    catchup=False,
)

# Definisikan volume dan volume mount
volume_config = k8s.V1ConfigMapVolumeSource(name="book-job")
volume = k8s.V1Volume(name="spark-jobs-volume", config_map=volume_config)
volume_mount = k8s.V1VolumeMount(name="spark-jobs-volume", mount_path="/spark-jobs")

submit_spark_job = KubernetesPodOperator(
    task_id='submit_spark_s3_job',
    name='spark-s3-job-submitter',
    namespace='airflow',
    image='bitnami/kubectl:latest',
    cmds=['kubectl'],
    arguments=[
        'apply',
        '-f', '/spark-jobs/book-job.yaml',
        '-n', 'zeatarou'
    ],
    volumes=[volume],
    volume_mounts=[volume_mount],
    is_delete_operator_pod=True,
    in_cluster=True,
    dag=dag,
)