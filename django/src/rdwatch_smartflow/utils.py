from functools import cached_property

import airflow_client.client
import requests
from airflow_client.client.api import dag_api, monitoring_api
from airflow_client.client.models import DAGCollection, HealthInfo
from bs4 import BeautifulSoup

from django.conf import settings


class SmartFlowClient:
    @cached_property
    def _session_token(self) -> str:
        session = requests.Session()
        smartflow_url: str = settings.SMARTFLOW_URL
        username: str = settings.SMARTFLOW_USERNAME
        password: str = settings.SMARTFLOW_PASSWORD

        res = session.get(smartflow_url)
        soup = BeautifulSoup(res.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']

        login_url = f'{smartflow_url}/login/'
        login_form_data = {
            'csrf_token': csrf_token,
            'username': username,
            'password': password,
        }
        login_headers = {'referer': login_url}
        res = session.post(
            url=login_url,
            data=login_form_data,
            headers=login_headers,
        )
        res.raise_for_status()
        return session.cookies.get('session')

    @property
    def _client(self):
        host: str = f'{settings.SMARTFLOW_URL}/api/v1'

        configuration = airflow_client.client.Configuration(
            host=host,
            # api_key={'session': self._session_token}
        )
        with airflow_client.client.ApiClient(
            configuration=configuration,
            header_name='cookie',
            header_value=f'session={self._session_token}',
        ) as api_client:
            return api_client

    @property
    def _monitoring_api(self):
        return monitoring_api.MonitoringApi(self._client)

    @property
    def _dag_api(self):
        return dag_api.DAGApi(self._client)

    def get_health(self) -> HealthInfo:
        return self._monitoring_api.get_health()

    def list_dags(self, **kwargs) -> DAGCollection:
        return self._dag_api.get_dags(**kwargs)
