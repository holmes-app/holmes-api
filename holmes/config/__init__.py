#!/usr/bin/python
# -*- coding: utf-8 -*-

from derpconf.config import Config  # NOQA


Config.define('WORKER_SLEEP_TIME', 10, 'Main loop sleep time', 'Worker')
Config.define('ZOMBIE_WORKER_TIME', 200,
              'Time to remove a Worker from API List (must be greater than WORKER_SLEEP_TIME + Validation time)', 'API')

Config.define('CONNECT_TIMEOUT_IN_SECONDS', 20, 'Number of seconds a connection can take.', 'Worker')
Config.define('REQUEST_TIMEOUT_IN_SECONDS', 60, 'Number of seconds a request can take.', 'Worker')

Config.define('HOLMES_API_URL', 'http://localhost:2368', 'URL that Worker will communicate with API', 'Worker')

Config.define('LOG_LEVEL', 'ERROR', 'Default log level', 'Logging')
Config.define('LOG_FORMAT', '%(asctime)s:%(levelname)s %(module)s - %(message)s',
              'Log Format to be used when writing log messages', 'Logging')
Config.define('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S',
              'Date Format to be used when writing log messages.', 'Logging')

Config.define('FACTERS', [], 'List of classes to get facts about a website', 'Review')
Config.define('VALIDATORS', [], 'List of classes to validate a website', 'Review')
Config.define('REVIEW_EXPIRATION_IN_SECONDS', 6 * 60 * 60, 'Number of seconds that a review expires in.', 'Review')

Config.define('MAX_ENQUEUE_BUFFER_LENGTH', 1000,
              'Number of urls to enqueue before submitting to the /pages route', 'Validators')

# Reference data retrieved from HTTP Archive in 06-jan-2014
Config.define('MAX_IMG_REQUESTS_PER_PAGE', 40,
              'Maximum number of images per page', 'Image Request Validator')
Config.define('MAX_KB_SINGLE_IMAGE', 26,
              'Maximum size of a single image', 'Image Request Validator')
Config.define('MAX_IMG_KB_PER_PAGE', 1028,
              'Maximum size of images per page', 'Image Request Validator')

# Reference data retrieved from HTTP Archive in 06-jan-2014
Config.define('MAX_CSS_REQUESTS_PER_PAGE', 8,
              'Maximum number of external stylesheets per page', 'CSS Request Validator')
Config.define('MAX_CSS_KB_PER_PAGE_AFTER_GZIP', 46,
              'Maximum size of stylesheets per page after gzip', 'CSS Request Validator')

# Reference data retrieved from HTTP Archive in 06-jan-2014
Config.define('MAX_JS_REQUESTS_PER_PAGE', 17,
              'Maximum number of external scripts per page', 'JS Request Validator')
Config.define('MAX_JS_KB_PER_PAGE_AFTER_GZIP', 272,
              'Maximum size of scripts per page after gzip', 'JS Request Validator')

Config.define('MAX_TITLE_SIZE', 70,
              'Title tags longer than 70 characters may be truncated in the results',
              'Title Validator')

Config.define('ORIGIN', '*', 'Access Control Allow Origin header value', 'Web')

Config.define('HTTP_PROXY_HOST', None, 'HTTP Proxy Host to use', 'Web')
Config.define('HTTP_PROXY_PORT', None, 'HTTP Proxy Port to use', 'Web')

Config.define('API_PROXY_HOST', None, 'HTTP Proxy Host to use to connect to the API', 'Web')
Config.define('API_PROXY_PORT', None, 'HTTP Proxy Port to use to connect to the API', 'Web')

Config.define('COMMIT_ON_REQUEST_END', True, 'Commit on request end', 'DB')

Config.define('REDISHOST', 'localhost', 'Redis host', 'Redis')
Config.define('REDISPORT', 7575, 'Redis port', 'Redis')
Config.define('REDISPASS', None, 'Redis password in case of auth', 'Redis')

Config.define('REQUIRED_META_TAGS', [], 'List of required meta tags', 'Meta tag Validator')

Config.define('SCHEMA_ORG_ITEMTYPE', [], 'List of Schema.Org ItemType', 'Schema.Org ItemType')

Config.define('FORCE_CANONICAL', False, 'Force canonical', 'Force canonical')

Config.define('BLACKLIST_DOMAIN', [], 'Domain blacklist', 'Domain blacklist')

Config.define('ERROR_HANDLERS', [], 'List of classes to handle errors', 'General')

# SENTRY ERROR HANDLER
Config.define('USE_SENTRY', False, 'If set to true errors will be sent to sentry.', 'Sentry')
Config.define('SENTRY_DSN_URL', '', 'URL to use as sentry DSN.', 'Sentry')

HOUR = 60 * 60
Config.define('PAGE_COUNT_EXPIRATION_IN_SECONDS', HOUR, 'Expiration for the cache key for each domain page count', 'Cache')
Config.define('VIOLATION_COUNT_EXPIRATION_IN_SECONDS', HOUR, 'Expiration for the cache key for each domain violation count', 'Cache')
Config.define('ACTIVE_REVIEW_COUNT_EXPIRATION_IN_SECONDS', HOUR, 'Expiration for the cache key for each domain violation count', 'Cache')
Config.define('URL_LOCK_EXPIRATION_IN_SECONDS', 30, 'Expiration for the url lock for each url', 'Cache')
Config.define('NEXT_JOB_URL_LOCK_EXPIRATION_IN_SECONDS', 3 * 60, 'Expiration for the url lock for next jobs', 'Cache')

Config.define('DEFAULT_PAGE_SCORE', 1000000, 'Page Score for pages that the user includes through the UI', 'General')
Config.define('PAGE_SCORE_TAX_RATE', 0.1, 'Default tax rate for scoring pages.', 'General')
