#!/usr/bin/python

from setuptools import setup, find_packages
from version import get_version


def readme():
    with open('README.rst') as f:
        return f.read()


setup(
    name='panopto-python-soap',
    version=get_version('short'),
    author='Mark Brewster',
    author_email='mbrewster@panopto.com',
    description=('Panopto API client that wraps the zeep library for the heavy lifting'),
    long_description=readme(),
    keywords=['python', 'panopto', 'lambda', 'api', 'soap'],
    install_requires=[
        're',
        'urllib3',
        'zeep'
    ],
    package_dir={'': 'src'},
    packages=find_packages('src')
)
