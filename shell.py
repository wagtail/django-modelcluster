#!/usr/bin/env python
import sys

from django.conf import settings
from django.core.management import execute_from_command_line


if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        INSTALLED_APPS=[
            'modelcluster',
            'tests',
        ]
    )


def runtests():
    argv = sys.argv[:1] + ['shell'] + sys.argv[1:]
    execute_from_command_line(argv)


if __name__ == '__main__':
    runtests()
