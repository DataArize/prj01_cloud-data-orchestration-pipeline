import os

import airflow
import logging
from airflow import DAG
from datetime import timedelta
from google.cloud import storage
from airflow.operators.python import ShortCircuitOperator
from airflow.providers.google.cloud.transfers.gcs_to_gcs import GCSToGCSOperator
from airflow.operators.dummy import DummyOperator
from airflow.providers.google.cloud.operators.dataflow import DataflowStartFlexTemplateOperator
from airflow.models import Variable
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)

DATASET_BUCKET_NAME = os.getenv("DATASET_BUCKET_NAME")
SOURCE_FOLDER = os.getenv("SOURCE_FOLDER")
ARCHIVE_FOLDER = os.getenv("ARCHIVE_FOLDER")
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
PROJECT_REGION = os.getenv("GCP_PROJECT_REGION")
CLUSTER_NAMESPACE = os.getenv("CLUSTER_NAMESPACE")
CLUSTER_SERVICE_ACCOUNT_NAME = os.getenv("CLUSTER_SERVICE_ACCOUNT_NAME")
ARTIFACTORY_IMAGE_NAME = os.getenv("GCP_ARTIFACTORY_IMAGE_NAME")



default_args = {
    'start_date': airflow.utils.dates.days_ago(0),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'data_ingestion_da',
    default_args=default_args,
    description='CSV file load dag',
    schedule_interval='* 10 * * *',
    max_active_runs=2,
    catchup=False,
    dagrun_timeout=timedelta(minutes=10),
)

start = DummyOperator(
    task_id="start"
)

#function to check files
def check_files_exist():
    client = storage.Client(project=PROJECT_ID)
    bucket = client.get_bucket(DATASET_BUCKET_NAME)
    blobs = list(bucket.list_blobs(prefix=SOURCE_FOLDER))
    file_names = [blob.name for blob in blobs if blob.name.endswith(".csv")]

    for file_name in file_names:
        logging.info(f"File - {file_name}")

    return len(file_names) > 0

check_files_task = ShortCircuitOperator(
    task_id="check_files_task",
    python_callable=check_files_exist,
    ignore_downstream_trigger_rules=False,
    show_return_value_in_logs=True,
    dag=dag
)

start_dataflow = KubernetesPodOperator(
    task_id="pod-ex-minimum",
    name="pod-ex-minimum",
    namespace=CLUSTER_NAMESPACE,
    service_account_name=CLUSTER_SERVICE_ACCOUNT_NAME,
    image="asia-south1-docker.pkg.dev/optimal-karma-439613-g6/prj01-cloud-data-orch-repository/prj01-cloud-data-orch-dataflow",
)

archive_files = GCSToGCSOperator(
    task_id="archive_files",
    source_bucket=DATASET_BUCKET_NAME,
    source_object=f"{SOURCE_FOLDER}*.csv",
    destination_bucket=DATASET_BUCKET_NAME,
    destination_object=f"{ARCHIVE_FOLDER}/{{{{ ds }}}}/",
    move_object=True,  # Move file instead of copy
    dag=dag
)

end = DummyOperator(
    task_id="end"
)

start >> check_files_task >> start_dataflow >> archive_files >> end