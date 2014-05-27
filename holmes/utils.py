#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from os.path import abspath, join, dirname
import logging
import gettext

try:
    from tornado import httputil

    from six.moves.urllib.parse import urlparse
except ImportError:
    logging.warning('Could not import some dependencies. Probably setup.py installing holmes...')

EMPTY_DOMAIN_RESULT = ('', '')

locale_path = abspath(join(dirname(__file__), 'i18n/locale/'))
languages = {}

def _(message):
    return message

def load_languages():
    global languages

    for language in os.listdir(locale_path):
        languages[language] = gettext.translation('api', locale_path, languages=[language])

def install_i18n(language="en_US"):
    global languages

    english = languages.get("en_US")
    lang = languages.get(language, english)
    return lang.ugettext


def get_domain_from_url(url, default_scheme='http'):
    if not url:
        return EMPTY_DOMAIN_RESULT

    scheme = default_scheme
    result = urlparse(url)
    domain = result.netloc

    if (result.scheme and result.scheme in ['http', 'https']):
        scheme = result.scheme

    if (result.scheme and result.scheme not in ['http', 'https']) and not domain:
        domain = result.scheme
    else:
        if not domain:
            domain = result.path.split('/')[0]
            if not '.' in domain:
                return EMPTY_DOMAIN_RESULT

        if ':' in domain:
            domain = domain.split(':')[0]

    original_domain = domain.strip()
    domain = original_domain.replace('www.', '')

    return domain, '%s://%s' % (scheme, original_domain)


def get_class(klass):
    module_name, class_name = klass.rsplit('.', 1)

    module = __import__(module_name)

    if '.' in module_name:
        module = reduce(getattr, module_name.split('.')[1:], module)

    return getattr(module, class_name)


def load_classes(classes=None, classes_to_load=None, default=None):
    if classes_to_load is None:
        classes_to_load = default

    if classes is None:
        classes = []

    for class_full_name in classes_to_load:
        if isinstance(class_full_name, (tuple, set, list)):
            load_classes(classes, class_full_name)
            continue

        try:
            klass = get_class(class_full_name)
            classes.append(klass)
        except ValueError:
            logging.warn('Invalid class name [%s]. Will be ignored.' % class_full_name)
        except AttributeError:
            logging.warn('Class [%s] not found. Will be ignored.' % class_full_name)
        except ImportError:
            logging.warn('Module [%s] not found. Will be ignored.' % class_full_name)

    return classes


def get_status_code_title(status_code):
    status_code = int(status_code)
    try:
        title = httputil.responses[status_code]
    except KeyError:
        if status_code == 599:
            title = 'Tornado Timeout'
        else:
            title = 'Unknown'

    return title


def is_valid(url):
    try:
        return urlparse(url)
    except ValueError:
        return None


def count_url_levels(url):
    parse = is_valid(url)
    if parse:
        path = parse.path
        if path.startswith('/'):
            path = path[1:]
        return len(path.split('/'))
    return None
