#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

setup(
    name='django-modelcluster',
    version='6.3',
    description="Django extension to allow working with 'clusters' of models as a single unit, independently of the database",
    author='Matthew Westcott',
    author_email='matthew.westcott@torchbox.com',
    url='https://github.com/wagtail/django-modelcluster',
    packages=find_packages(exclude=('tests*',)),
    license='BSD',
    long_description=open('README.rst').read(),
    python_requires=">=3.9",
    install_requires=[
        "django>=4.2",
    ],
    extras_require={
        'taggit': ['django-taggit>=3.1'],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3 :: Only',
        'Framework :: Django',
    ],
)
