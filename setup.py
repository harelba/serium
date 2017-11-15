#!/usr/bin/env python

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

description = 'Sustainable case-class serialization library'

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='serium',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.1.10',

    description=description,
    long_description=long_description,

    url='https://github.com/harelba/serium',
    download_url='https://github.com/harelba/serium/archive/0.1.10.tar.gz',

    author='Harel Ben-Attia',
    author_email='harelba@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'License :: OSI Approved :: Apache Software License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only'
    ],

    keywords='serium case-classes serialization data-migration data-structures strict-typing schema-evolution schema',

    packages=find_packages(exclude=['docs', 'test_*']),

    install_requires=[],
    python_requires='>=2.6,<3',

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['pytest'],
        'test': ['pytest'],
    }
)
