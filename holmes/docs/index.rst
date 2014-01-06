.. holmes documentation master file, created by
   sphinx-quickstart on Mon Jan  6 13:30:59 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Holmes - Overview
=================

Holmes is an agent meant to spy on your pages and report its findings. It will monitor SEO, broken links and images, page size and many others.

It is composed of two projects: `holmes-api`_ and `holmes-web`_.

The way holmes works is by crawling your website and then storing facts and violations about each page it can find.

For finding pages, holmes will parse sitemaps (if available) and crawl all links in the same sub-domain as the page you queued in the front-end.

holmes-web
----------

holmes-web is the front-end for holmes. It's an angularJS project and it relies on holmes-api to retrieve information from its central repository of information.

holmes-api
----------

holmes-api is the core of holmes. It's divided in two core components: the web api and the workers.

The workers are responsible for actually monitoring different pages and the web api is responsible for guiding both the workers and the front-end.

By having such an API, holmes is ready for different front-ends or workers to be created.

Info
----

For more info, please see one of the links below.

.. toctree::
  :maxdepth: 2

  getting-started
  facts
  violations


.. _holmes-api: https://github.com/heynemann/holmes-api
.. _holmes-web: https://github.com/heynemann/holmes-web
