import airflow_client.client
from airflow_client.client.api import monitoring_api
from airflow_client.client.models import HealthInfo

from django.conf import settings


class SmartFlowClient:
    def get_health(self) -> HealthInfo:
        return self._monitoring_api.get_health()

    @property
    def _client(self):
        host: str = f'{settings.SMARTFLOW_URL}/api/v1'
        username: str = settings.SMARTFLOW_USERNAME
        password: str = settings.SMARTFLOW_PASSWORD
        configuration = airflow_client.client.Configuration(
            host=host,
            username=username,
            password=password,
        )
        with airflow_client.client.ApiClient(configuration) as api_client:
            return api_client

    @property
    def _monitoring_api(self):
        return monitoring_api.MonitoringApi(self._client)


smartflow = SmartFlowClient()
