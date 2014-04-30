Contributing
============

Installation
------------

Installation instructions for development enviroments.

### Requirements

The holmes-api requires the following tools to work:

* MySQL
* Python
* python-pip
* Redis

### Installation

The holmes-api software has a Makefile to help with common tasks. To install, just type:

    make setup

To install data/migrations:

    make drop data

To run:

    make run

To test:

    make test

To test without migrations:

    make redis_test unit
