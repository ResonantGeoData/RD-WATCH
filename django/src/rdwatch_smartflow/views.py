from ninja import Router

from rdwatch_smartflow.utils import SmartFlowClient

router = Router()


@router.get('/dags/')
def list_dags(request, **kwargs):
    return SmartFlowClient().list_dags(**kwargs).to_dict()
