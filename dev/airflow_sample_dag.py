from datetime import datetime

from airflow import DAG
from airflow.decorators import task
from airflow.models import Param

with DAG(
    dag_id="RD-WATCH-AIRFLOW-DEMO-DAG",
    description="Test DAG",
    params={
        "region_id": Param(default="BR_R002", type="string", pattern=r"^.{1,255}$"),
        "model_run_title": Param(default="test_run", type="string"),
    },
    start_date=datetime(2022, 3, 1),
    catchup=False,
    schedule_interval=None,
    max_active_runs=1,
    default_view="grid",
    tags=["demo", "watch", "ta2", "rgd", "random"],
) as dag1:

    @task
    def print_region(**context):
        region_id = context["params"]["region_id"]
        print(f"region_id: {region_id}")

    @task
    def print_model_run_title(**context):
        model_run_title = context["params"]["model_run_title"]
        print(f"model_run_title: {model_run_title}")

    print_region() >> print_model_run_title()
