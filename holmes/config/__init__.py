#!/usr/bin/python
# -*- coding: utf-8 -*-

from derpconf.config import Config  # NOQA


Config.define('WORKER_SLEEP_TIME', 10, 'Main loop sleep time', 'Worker')
Config.define('ZOMBIE_WORKER_TIME', 200,
              'Time to remove a Worker from API List (must be greater than WORKER_SLEEP_TIME + Validation time)', 'API')

Config.define('HOLMES_API_URL', 'http://localhost:2368', 'URL that Worker will communicate with API', 'Worker')

Config.define('LOG_LEVEL', 'ERROR', 'Default log level', 'Logging')
Config.define('LOG_FORMAT', '%(asctime)s:%(levelname)s %(module)s - %(message)s',
              'Log Format to be used when writing log messages', 'Logging')
Config.define('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S',
              'Date Format to be used when writing log messages.', 'Logging')

Config.define('VALIDATORS', [], 'List of classes to validate a website', 'Review')
Config.define('REVIEW_EXPIRATION_IN_SECONDS', 6 * 60 * 60, 'Number of seconds that a review expires in.', 'Review')

Config.define('MAX_ENQUEUE_BUFFER_LENGTH', 1000,
              'Number of urls to enqueue before submitting to the /pages route', 'Validators')

Config.define('MAX_IMG_REQUESTS_PER_PAGE', 50,
              'Maximum number of images per page', 'Image Request Validator')
Config.define('MAX_KB_SINGLE_IMAGE', 100,
              'Maximum size of a single image', 'Image Request Validator')
Config.define('MAX_IMG_KB_PER_PAGE', 1000,
              'Maximum size of images per page', 'Image Request Validator')

Config.define('MAX_CSS_REQUESTS_PER_PAGE', 5,
              'Maximum number of external stylesheets per page', 'CSS Request Validator')
Config.define('MAX_CSS_KB_PER_PAGE_AFTER_GZIP', 50,
              'Maximum size of stylesheets per page after gzip', 'CSS Request Validator')

Config.define('MAX_JS_REQUESTS_PER_PAGE', 5,
              'Maximum number of external scripts per page', 'JS Request Validator')
Config.define('MAX_JS_KB_PER_PAGE_AFTER_GZIP', 50,
              'Maximum size of scripts per page after gzip', 'JS Request Validator')

Config.define('MAX_TITLE_SIZE', 80,
              'Title tags longer than 80 characters may be truncated in the results', 'Title Validator')

Config.define('ORIGIN', '*', 'Access Control Allow Origin header value', 'Web')
