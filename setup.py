#!/usr/bin/env python

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

description = 'Sustainable case-class serialization library'
long_description = "A serialization library that provides resiliency to data structure evolution"

setup(
    name='serium',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.1.0',

    description=description,
    long_description=long_description,

    url='https://github.com/harelba/serium',

    author='Harel Ben-Attia',
    author_email='harelba@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules'

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
    ],

    keywords='serium case-classes serialization data-migration data-structures strict-typing',

    packages=find_packages(exclude=['contrib', 'docs', 'test']),

    #   py_modules=["my_module"],

    install_requires=[],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['pytest'],
        'test': ['pytest'],
    }
#    ,
#    entry_points={
#        'console_scripts': [
#            'pycase=pycase:pycase_cli',
#        ],
#    }
)
