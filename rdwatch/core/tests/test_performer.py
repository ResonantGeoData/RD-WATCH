import pytest
from ninja.testing import TestClient

from django.forms.models import model_to_dict

from rdwatch.core.models import Performer


@pytest.mark.django_db()
def test_list_performer(test_client: TestClient):
    Performer.objects.all().delete()  # remove lookups data

    performers = Performer.objects.bulk_create(
        [
            Performer(team_name='Foobar', short_code='FOO'),
            Performer(team_name='Barfoo', short_code='BAR'),
        ]
    )
    response = test_client.get('/performers/')
    assert response.status_code == 200
    assert sorted(response.json()['items'], key=lambda p: p['id']) == sorted(
        [
            {
                actual_name: getattr(p, db_name)
                for actual_name, db_name in [
                    ('id', 'id'),
                    ('team_name', 'team_name'),
                    ('short_code', 'short_code'),
                ]
            }
            for p in performers
        ],
        key=lambda p: p['id'],
    )


@pytest.mark.django_db()
def test_get_performer(test_client: TestClient):
    Performer.objects.all().delete()  # remove lookups data

    performer = Performer.objects.create(team_name='Foobar', short_code='FOO')
    response = test_client.get(f'/performers/{performer.id}/')
    assert response.status_code == 200
    assert response.json() == model_to_dict(performer)


@pytest.mark.django_db()
def test_create_performer(test_client: TestClient):
    Performer.objects.all().delete()  # remove lookups data

    # Test creating a performer
    response = test_client.post(
        '/performers/', json={'team_name': 'Foobar', 'short_code': 'FOO'}
    )
    assert response.status_code == 201
    assert Performer.objects.count() == 1
    response_json = response.json()
    assert model_to_dict(Performer.objects.first()) == {
        'team_name': 'Foobar',
        'short_code': 'FOO',
        'id': response_json['id'],
    }

    # Test creating a performer with the same team_name (should fail)
    response = test_client.post(
        '/performers/', json={'team_name': 'Foobar', 'short_code': 'FOO'}
    )
    assert response.status_code == 409
    assert Performer.objects.count() == 1
    assert response.json() == 'Performer already exists'
