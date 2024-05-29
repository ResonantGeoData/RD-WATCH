from typing import Any

from ninja import Router, Schema

from django.http import HttpRequest

from rdwatch_smartflow.utils import SmartFlowClient

router = Router()


class RunDagRequestSchema(Schema):
    dag_run_title: str
    conf: dict[str, Any]


@router.get('/dags/')
def list_dags(request: HttpRequest):
    print(request.GET.dict())
    return SmartFlowClient().list_dags(**request.GET.dict()).to_dict()


@router.get('/dags/{dag_id}/dagRuns/')
def list_dag_runs(request: HttpRequest, dag_id: str):
    return SmartFlowClient().list_dag_runs(dag_id=dag_id).to_dict()


@router.post('/dags/{dag_id}/dagRuns/')
def create_dag_run(request, dag_id, data: RunDagRequestSchema):
    return (
        SmartFlowClient()
        .create_dag_run(dag_id=dag_id, dag_run_title=data.dag_run_title, conf=data.conf)
        .to_dict()
    )


@router.get('/dags/{dag_id}/dagRuns/{dag_run_id}/')
def get_dag_run(request, dag_id: str, dag_run_id: str):
    return SmartFlowClient().get_dag_run(dag_id=dag_id, dag_run_id=dag_run_id).to_dict()
