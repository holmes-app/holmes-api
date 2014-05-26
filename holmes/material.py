#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from uuid import uuid4
from functools import partial
from collections import defaultdict

from holmes.cli import BaseCLI
from holmes.models.domain import Domain
from holmes.models.violation import Violation
from holmes.models.request import Request
from holmes.utils import get_domain_from_url


def configure_materials(girl, db, config):
    # The following material is grouped by domain and should be
    # expired whenever a new domain is added (see page.py:Page.add_domain)
    girl.add_material(
        'domains_details',
        partial(Domain.get_domains_details, db),
        config.MATERIALS_EXPIRATION_IN_SECONDS['domains_details'],
        config.MATERIALS_GRACE_PERIOD_IN_SECONDS['domains_details']
    )

    girl.add_material(
        'violation_count_by_category_for_domains',
        partial(Violation.get_group_by_category_id_for_all_domains, db),
        config.MATERIALS_EXPIRATION_IN_SECONDS['violation_count_by_category_for_domains'],
        config.MATERIALS_GRACE_PERIOD_IN_SECONDS['violation_count_by_category_for_domains']
    )

    girl.add_material(
        'blacklist_domain_count',
        partial(MaterialConveyor.get_blacklist_domain_count, db),
        config.MATERIALS_EXPIRATION_IN_SECONDS['blacklist_domain_count'],
        config.MATERIALS_GRACE_PERIOD_IN_SECONDS['blacklist_domain_count']
    )

    girl.add_material(
        'most_common_violations',
        partial(
            Violation.get_most_common_violations_names,
            db,
            config.get('MOST_COMMON_VIOLATIONS_SAMPLE_LIMIT')
        ),
        config.MATERIALS_EXPIRATION_IN_SECONDS['most_common_violations'],
        config.MATERIALS_GRACE_PERIOD_IN_SECONDS['most_common_violations']
    )

    # The following material is grouped by domain and should be
    # expired whenever a new domain is added (see page.py:Page.add_domain)
    girl.add_material(
        'failed_responses_count',
        partial(
            Request.get_requests_count_by_status,
            db,
            config.get('MAX_REQUESTS_FOR_FAILED_RESPONSES')
        ),
        config.MATERIALS_EXPIRATION_IN_SECONDS['failed_responses_count'],
        config.MATERIALS_GRACE_PERIOD_IN_SECONDS['failed_responses_count']
    )


class MaterialConveyor(object):
    @classmethod
    def get_blacklist_domain_count(cls, db):
        ungrouped = defaultdict(int)
        for urls, count in Violation.get_group_by_value_for_key(db, 'blacklist.domains'):
            for url in urls:
                domain, null = get_domain_from_url(url)
                ungrouped[domain] += count
        blacklist = sorted(ungrouped.items(), key=lambda xz: -xz[1])
        return [dict(zip(('domain', 'count'), x)) for x in blacklist]


class MaterialWorker(BaseCLI):
    def initialize(self):
        self.uuid = uuid4().hex

        self.error_handlers = [handler(self.config) for handler in self.load_error_handlers()]

        self.connect_sqlalchemy()
        self.connect_to_redis()

        self.configure_material_girl()

    def do_work(self):
        self.info('Running material girl...')
        self.db.begin(subtransactions=True)
        self.girl.run()
        self.db.close()


def main():
    worker = MaterialWorker(sys.argv[1:])
    worker.run()

if __name__ == '__main__':
    main()
