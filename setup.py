#!/usr/bin/env python

from distutils.core import setup

setup(
    name='django-modelcluster',
    version='0.1',
    description="Django extension to allow working with 'clusters' of models as a single unit, independently of the database",
    author='Matthew Westcott',
    author_email='matthew.westcott@torchbox.com',
    url='https://github.com/torchbox/django-modelcluster',
    packages=['modelcluster', 'tests'],
    license='BSD',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Framework :: Django',
    ],
)