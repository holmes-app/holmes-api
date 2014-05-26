#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from holmes import __version__

tests_require = [
    'mock',
    'nose',
    'coverage',
    'yanc',
    'preggy',
    'tox',
    'ipdb',
    'coveralls',
    'factory_boy',
    'sqltap',
    'sphinx',
    'honcho',
]

setup(
    name='holmes',
    version=__version__,
    description='Holmes is a service to investigate your website health.',
    long_description='''
Holmes is a service to investigate your website health.
''',
    keywords='seo health web',
    author='Globo.com',
    author_email='appdev@corp.globo.com',
    url='',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'cow-framework>=0.8.0,<0.9.0',
        'ujson>=1.33,<1.34.0',
        'requests>=2.2.1,<2.3.0',
        'lxml>=3.3.3,<3.4.0',
        'cssselect>=0.9.1,<0.10.0',
        'sheep>=0.3.10,<0.4.0',
        'pycurl>=7.19.0,<7.20.0',
        'alembic>=0.6.3,<0.7.0',
        'mysql-python>=1.2.5,<1.3.0',
        'six>=1.6.1,<1.7.0',
        'octopus-http>=0.6.3,<0.7.0',
        'redis>=2.9.1,<2.10.0',
        'toredis>=0.1.2,<0.2.0',
        'raven>=4.1.1,<4.2.0',
        'rotunicode>=1.0.1,<1.1.0',
        'materialgirl>=0.5.0,<0.6.0',
        'pyelasticsearch>=0.6.1,<0.7.0',
        'tornadoes>=2.0.0,<2.1.0',
        'Babel>=1.3,<1.4',
    ],
    extras_require={
        'tests': tests_require,
    },
    entry_points={
        'console_scripts': [
            'holmes-api=holmes.server:main',
            'holmes-worker=holmes.worker:main',
            'holmes-material=holmes.material:main',
            'holmes-search=holmes.search:main',
        ],
    },
)
