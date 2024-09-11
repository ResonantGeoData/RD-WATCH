from django.core.management.base import BaseCommand

from rdwatch.core.models import ModelRun


class Command(BaseCommand):
    help = 'Deletes all ModelRuns with the corresponding Title, useful with argument\
    "Ground Truth" to reload data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--title',
            type=str,
            help='Specify the model to delete objects from',
            required=True,
        )

    def handle(self, *args, **kwargs):
        title = kwargs['title']
        if title:
            try:
                deleted_count, _ = ModelRun.objects.filter(title=title).delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully deleted {deleted_count} objects from {title}'
                    )
                )
            except KeyError:
                self.stdout.write(
                    self.style.ERROR(f'Error: Title {title} does not exist')
                )
        else:
            self.stdout.write(self.style.ERROR('Error: title name is required'))
