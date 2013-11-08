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
        'cow-framework',
        'ujson',
        'motorengine',
        'requests',
        'lxml',
        'cssselect',
        'sheep==0.3.1',
    ],
    extras_require={
        'tests': tests_require,
    },
    entry_points={
        'console_scripts': [
            'holmes-api=holmes.server:main',
            'holmes-worker=holmes.worker:main',
        ],
    },
)
