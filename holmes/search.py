#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging

from derpconf.config import ConfigurationError

from holmes.config import Config
from holmes.utils import load_classes
from holmes.search_providers import SearchProvider


def main():
    parser = SearchProvider.argparser()
    args = parser.parse_args()
    try:
        config = Config()
        if args.conf:
            config = config.load(args.conf[0])
        search_providers = load_classes(default=[config['SEARCH_PROVIDER']])
        if isinstance(search_providers, list) and len(search_providers) == 1:
            search_provider = search_providers.pop()
            search_provider.main()
        else:
            logging.error('Could not instantiate search provider!')
            sys.exit(1)
    except ConfigurationError:
        logging.error('Could not load config! Use --conf conf_file')
        sys.exit(1)
    except KeyError:
        logging.error('Could not parse config! Check it\'s contents')
        sys.exit(1)

if __name__ == '__main__':
    main()
