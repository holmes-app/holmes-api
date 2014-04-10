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


ElasticSearch
-------------

Holmes supports ElasticSearch for faster searches on big databases.

### Installing and running

After having ES properly installed and configured, *optionally* run:

```bash
make elasticsearch  # to start the ES server as daemon
```

To shut it down later, run:

```bash
make kill_elasticsearch  # to kill the ES server daemon
```

### Overriding default configuration (local.conf)

Bear in mind that, for testing purposes, overriding these variables is optional.

#### Optional configurations

To set it as the default search provider:

```conf
SEARCH_PROVIDER = 'holmes.search_providers.elastic.ElasticSearchProvider'
```

If -- and only if -- ES runs on a host and/or port other than localhost:9200, set one of or both the following variables accordingly:

```conf
ELASTIC_SEARCH_HOST = 'HOST'  # hostname or IP address
ELASTIC_SEARCH_PORT = PORT  # default is 9200
```

Should you need or want to use a different index name, just set it at your own will:

```conf
ELASTIC_SEARCH_INDEX = 'INDEX'  # name of the index
```

### Setting up

Prior to running the API, setup the index and optionally index all the active reviews:

```bash
make elasticsearch_setup  # to create the index
make elasticsearch_index  # to index all active reviews (optional, may take too long)
```

### Testing

Tests **expect** elasticsearch to be **running** on the default port **9200**. The index name is `holmes-test`. So, to test:

```bash
make test  # this creates the test index for you
```

or

```bash
make elasticsearch_drop_test  # to delete the test index
make elasticsearch_setup_test  # to create the test index
make unit  # to run unit tests
```

**Happy contributing!**
