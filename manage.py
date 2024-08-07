#!/usr/bin/env python
import os
import sys

import configurations.importer

from django.core.management import execute_from_command_line


def main() -> None:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'rdwatch.settings'
    os.environ.setdefault('DJANGO_CONFIGURATION', 'DevelopmentConfiguration')
    configurations.importer.install(check_options=True)

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
