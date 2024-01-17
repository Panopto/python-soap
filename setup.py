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
    description='Panopto API client that wraps the zeep library for the heavy lifting',
    long_description=readme(),
    keywords=['python', 'panopto', 'lambda', 'api', 'soap'],
    install_requires=[
        # zeep -> lxml. lxml 5.0.0 is not compatible with Python 3.9 or lower.
        'lxml<5.0.0; python_version < "3.10"',
        'zeep'
    ],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    python_requires='>=3.8',
)
