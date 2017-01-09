#!/usr/bin/env python
import os
import shutil
import sys

from django.core.management import execute_from_command_line
from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'


def runtests():
    argv = sys.argv[:1] + ['test'] + sys.argv[1:]
    try:
        execute_from_command_line(argv)
    finally:
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)


if __name__ == '__main__':
    runtests()
