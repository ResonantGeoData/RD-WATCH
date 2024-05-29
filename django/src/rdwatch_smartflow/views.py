from ninja import Router, Schema

from rdwatch_smartflow.utils import SmartFlowClient

router = Router()


class RunDagRequestSchema(Schema):
    dag_run_title: str


@router.get('/dags/')
def list_dags(request, **kwargs):
    return SmartFlowClient().list_dags(**kwargs).to_dict()


@router.post('/dags/{dag_id}/')
def run_dag(request, dag_id, data: RunDagRequestSchema):
    return (
        SmartFlowClient()
        .run_dag(dag_id=dag_id, dag_run_title=data.dag_run_title)
        .to_dict()
    )
