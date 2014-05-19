#!/usr/bin/python
# -*- coding: utf-8 -*-

from derpconf.config import Config  # NOQA

MINUTE = 60
HOUR = MINUTE * 60
DAY = 24 * HOUR

Config.define('WORKER_SLEEP_TIME', 10, 'Main loop sleep time', 'Worker')
Config.define('ZOMBIE_WORKER_TIME', 200,
              'Time to remove a Worker from API List (must be greater than WORKER_SLEEP_TIME + Validation time)', 'API')

Config.define('WORKERS_LOOK_AHEAD_PAGES', 1000, 'Number of pages that will be retrieved when looking for the next job', 'Worker')

Config.define('UPDATE_PAGES_SCORE_EXPIRATION', 30, 'The expiration for lock to update pages score', 'Worker')
Config.define('UPDATE_PAGES_SCORE_SLEEP_TIME', HOUR, 'The expiration for lock to update pages score', 'Worker')

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
Config.define('NUMBER_OF_REVIEWS_TO_KEEP', 4, 'Maximum number of reviews to keep', 'Review')

Config.define('DAYS_TO_KEEP_REQUESTS', 12, 'Number of days to keep requests', 'Requests')
Config.define('MAX_REQUESTS_FOR_FAILED_RESPONSES', 1000, 'Number of requests for falied responses', 'Requests')

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
Config.define('METATAG_DESCRIPTION_MAX_SIZE', 300,
              'Description Meta tags longer than 300 characters may be truncated in the results',
              'Metatag validator')
Config.define('MAX_HEADING_HIEARARCHY_SIZE', 150,
              'Heading Hierarchy tags longer than 150 characters may be truncated in the results',
              'Heading Hierarchy Validator')
Config.define('MAX_IMAGE_ALT_SIZE', 70,
              'Image alt attributes longer than 70 characters may be truncated in the results',
              'Image Alt Attribute Validator')

Config.define('ORIGIN', '*', 'Access Control Allow Origin header value', 'Web')

Config.define('HTTP_PROXY_HOST', None, 'HTTP Proxy Host to use', 'Web')
Config.define('HTTP_PROXY_PORT', None, 'HTTP Proxy Port to use', 'Web')

Config.define('API_PROXY_HOST', None, 'HTTP Proxy Host to use to connect to the API', 'Web')
Config.define('API_PROXY_PORT', None, 'HTTP Proxy Port to use to connect to the API', 'Web')

Config.define('COMMIT_ON_REQUEST_END', True, 'Commit on request end', 'DB')

Config.define('REDISHOST', 'localhost', 'Redis host', 'Redis')
Config.define('REDISPORT', 7575, 'Redis port', 'Redis')
Config.define('REDISPASS', None, 'Redis password in case of auth', 'Redis')

Config.define('MATERIAL_GIRL_REDISPORT', 7575, 'Redis port', 'Redis')
Config.define('MATERIAL_GIRL_REDISHOST', 'localhost', 'Redis host', 'Redis')
Config.define('MATERIAL_GIRL_REDISPASS', None, 'Redis password in case of auth', 'Redis')

Config.define('REQUIRED_META_TAGS', [], 'List of required meta tags', 'Meta tag Validator')

Config.define('SCHEMA_ORG_ITEMTYPE', [], 'List of Schema.Org ItemType', 'Schema.Org ItemType')

Config.define('FORCE_CANONICAL', False, 'Force canonical', 'Force canonical')

Config.define('BLACKLIST_DOMAIN', [], 'Domain blacklist', 'Domain blacklist')

Config.define('ERROR_HANDLERS', [], 'List of classes to handle errors', 'General')

# SENTRY ERROR HANDLER
Config.define('USE_SENTRY', False, 'If set to true errors will be sent to sentry.', 'Sentry')
Config.define('SENTRY_DSN_URL', '', 'URL to use as sentry DSN.', 'Sentry')

Config.define('PAGE_COUNT_EXPIRATION_IN_SECONDS', HOUR, 'Expiration for the cache key for each domain page count', 'Cache')
Config.define('VIOLATION_COUNT_EXPIRATION_IN_SECONDS', HOUR, 'Expiration for the cache key for each domain violation count', 'Cache')
Config.define('ACTIVE_REVIEW_COUNT_EXPIRATION_IN_SECONDS', HOUR, 'Expiration for the cache key for each domain violation count', 'Cache')
Config.define('RESPONSE_TIME_AVG_EXPIRATION_IN_SECONDS', HOUR, 'Expiration for the cache key for each domain average response time', 'Cache')
Config.define('VIOLATIONS_BY_CATEGORY_EXPIRATION_IN_SECONDS', 6 * 60, 'Expiration for the cache key for each domain violation count by category', 'Cache')
Config.define('TOP_CATEGORY_VIOLATIONS_EXPIRATION_IN_SECONDS', 6 * 60, 'Expiration for the cache key for each domain top violation in a category', 'Cache')
Config.define('TOP_CATEGORY_VIOLATIONS_LIMIT', 10, 'Limit for the size of the list of top vilations of a key category for a domain', 'Domain Handler')
Config.define('URL_LOCK_EXPIRATION_IN_SECONDS', 30, 'Expiration for the url lock for each url', 'Cache')
Config.define('NEXT_JOB_URL_LOCK_EXPIRATION_IN_SECONDS', 3 * 60, 'Expiration for the url lock for next jobs', 'Cache')
Config.define('NEXT_JOBS_COUNT_EXPIRATION_IN_SECONDS', HOUR, 'Expiration for the cache key for next jobs count', 'Cache')

materials_expiration_in_seconds = {
    'domains_details': 0.5 * MINUTE + 1,
    'violation_count_by_category_for_domains': 3 * MINUTE + 11,
    'blacklist_domain_count': 10 * MINUTE + 1,
    'most_common_violations': HOUR + 7,
    'failed_responses_count': HOUR + 13,
}
Config.define('MATERIALS_EXPIRATION_IN_SECONDS', materials_expiration_in_seconds, 'Expire times for materials', 'material')

materials_grace_period_in_seconds = {
    'domains_details': 2 * materials_expiration_in_seconds['domains_details'],
    'violation_count_by_category_for_domains': 2 * materials_expiration_in_seconds['violation_count_by_category_for_domains'],
    'blacklist_domain_count': 2 * materials_expiration_in_seconds['blacklist_domain_count'],
    'most_common_violations': 2 * materials_expiration_in_seconds['most_common_violations'],
    'failed_responses_count': 2 * materials_expiration_in_seconds['failed_responses_count'],
}
Config.define('MATERIALS_GRACE_PERIOD_IN_SECONDS', materials_grace_period_in_seconds, 'Grace period times for materials', 'material')

Config.define('DEFAULT_PAGE_SCORE', 1, 'Page Score for pages that the user includes through the UI', 'General')
Config.define('PAGE_SCORE_TAX_RATE', 0.1, 'Default tax rate for scoring pages.', 'General')
Config.define('MAX_PAGE_SCORE', 15000000, 'Maximum score of page', 'General')

Config.define('REQUEST_CACHE_EXPIRATION_IN_SECONDS', HOUR, 'Expiration in seconds for cache storage of responses.', 'Cache')

Config.define('MAX_URL_LEVELS', 20, 'Maximum levels of URL')

Config.define('GOOGLE_CLIENT_ID', None, 'Google client ID')

Config.define('LIMITER_LOCKS_EXPIRATION', 120, 'The expiration for locks in the limiter')
Config.define('LIMITER_VALUES_CACHE_EXPIRATION', 600, 'The expiration for valus in the limiter')
Config.define('DEFAULT_NUMBER_OF_CONCURRENT_CONNECTIONS', 5, 'Default number of concurrent connections', 'Limiter')

Config.define('MOST_COMMON_VIOLATIONS_CACHE_EXPIRATION', 3 * HOUR, 'Expiration for the cache key for the most common violations', 'Cache')
Config.define('MOST_COMMON_VIOLATIONS_SAMPLE_LIMIT', 50000, 'Limit for the size of the Vilation sample used in the aggregation', 'Violation Handler')

throttling_message_type = {
    'new-request': 5,
    'new-page': 2,
    'new-review': 2,
}
Config.define('EVENT_BUS_THROTTLING_MESSAGE_TYPE', throttling_message_type, 'Trottling by message type', 'Event Bus')

Config.define('SQLALCHEMY_AUTO_FLUSH', True, 'Defines whether auto-flush should be used in sqlalchemy')
