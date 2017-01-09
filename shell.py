#!/usr/bin/env python
import os
import sys

from django.core.management import execute_from_command_line

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'


def runshell():
    argv = sys.argv[:1] + ['shell'] + sys.argv[1:]
    execute_from_command_line(argv)


if __name__ == '__main__':
    runshell()
