from django.contrib.auth.models import User
import factory.django
from rgd.models import ChecksumFile, Collection

from watch.core import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.SelfAttribute('email')
    email = factory.Faker('safe_email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class CollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Collection

    name = factory.Sequence(lambda n: f'collection_{n}')


class ChecksumFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ChecksumFile

    collection = factory.SubFactory(CollectionFactory)
    file = factory.django.FileField()

    # If we have an on_commit or post_save method that modifies the model, we
    # need to refresh it afterwards.
    @classmethod
    def _after_postgeneration(cls, instance, *args, **kwargs):
        super()._after_postgeneration(instance, *args, **kwargs)
        instance.refresh_from_db()


class STACFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.STACFile

    file = factory.SubFactory(ChecksumFileFactory)

    # If we have an on_commit or post_save method that modifies the model, we
    # need to refresh it afterwards.
    @classmethod
    def _after_postgeneration(cls, instance, *args, **kwargs):
        super()._after_postgeneration(instance, *args, **kwargs)
        instance.refresh_from_db()
