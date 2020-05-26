#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

setup(
    name='django-modelcluster',
    version='5.0.2',
    description="Django extension to allow working with 'clusters' of models as a single unit, independently of the database",
    author='Matthew Westcott',
    author_email='matthew.westcott@torchbox.com',
    url='https://github.com/wagtail/django-modelcluster',
    packages=find_packages(exclude=('tests*',)),
    license='BSD',
    long_description=open('README.rst').read(),
    python_requires=">=3.5",
    install_requires=[
        "pytz>=2015.2",
    ],
    extras_require={
        'taggit': ['django-taggit>=0.20'],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Framework :: Django',
    ],
)
