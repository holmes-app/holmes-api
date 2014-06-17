test: elasticsearch redis_test drop_test data_test elasticsearch_drop_test elasticsearch_setup_test unit integration kill_run

unit:
	@coverage run --branch `which nosetests` -vv --with-yanc -s tests/unit/
	@coverage report -m --fail-under=80

coverage-html: unit
	@coverage html -d cover

integration: kill_run run_daemon
	@`which nosetests` -vv --with-yanc -s tests/integration/;EXIT_CODE=$$?;$(MAKE) kill_run;exit $(EXIT_CODE)

tox:
	@PATH=$$PATH:~/.pythonbrew/pythons/Python-2.6.*/bin/:~/.pythonbrew/pythons/Python-2.7.*/bin/:~/.pythonbrew/pythons/Python-3.0.*/bin/:~/.pythonbrew/pythons/Python-3.1.*/bin/:~/.pythonbrew/pythons/Python-3.2.3/bin/:~/.pythonbrew/pythons/Python-3.3.0/bin/ tox

setup:
	@gem install crowdin-cli
	@pip install -U -e .\[tests\]

kill_redis:
	-redis-cli -p 7575 shutdown

redis: kill_redis
	redis-server ./redis.conf; sleep 1
	redis-cli -p 7575 info > /dev/null

flush_redis:
	redis-cli -p 7575 FLUSHDB

kill_redis_test:
	-redis-cli -p 57575 shutdown

redis_test: kill_redis_test
	redis-server ./redis_test.conf; sleep 1
	redis-cli -p 57575 info > /dev/null

flush_redis_test:
	redis-cli -p 57575 FLUSHDB

drop:
	@-cd holmes/ && alembic downgrade base
	@$(MAKE) drop_now

drop_now:
	@mysql -u root -e "DROP DATABASE IF EXISTS holmes; CREATE DATABASE IF NOT EXISTS holmes"
	@echo "DB RECREATED"

drop_test:
	@-cd tests/ && alembic downgrade base
	@mysql -u root -e "DROP DATABASE IF EXISTS test_holmes; CREATE DATABASE IF NOT EXISTS test_holmes"
	@echo "DB RECREATED"

data db:
	@cd holmes/ && alembic upgrade head

data_test:
	@cd tests/ && alembic upgrade head

kill_elasticsearch:
	-@pkill -F elasticsearch.pid

elasticsearch: kill_elasticsearch
	elasticsearch -d -p elasticsearch.pid

elasticsearch_setup:
	@python holmes/search_providers/elastic.py -vv -c ./holmes/config/local.conf --create

elasticsearch_drop:
	@python holmes/search_providers/elastic.py -vv -c ./holmes/config/local.conf --delete

elasticsearch_index:
	@python holmes/search_providers/elastic.py -vv -c ./holmes/config/local.conf --all-keys

elasticsearch_setup_test:
	@python holmes/search_providers/elastic.py -vv -c ./holmes/config/local.conf --create --index holmes-test

elasticsearch_drop_test:
	@python holmes/search_providers/elastic.py -vv -c ./holmes/config/local.conf --delete --index holmes-test

search_setup:
	@holmes-search -vv -c ./holmes/config/local.conf --create

search_drop:
	@holmes-search -vv -c ./holmes/config/local.conf --delete

search_index:
	@holmes-search -vv -c ./holmes/config/local.conf --all-keys

migration:
	@cd holmes/ && alembic revision -m "$(DESC)"

kill_run:
	@ps aux | awk '(/.+holmes-api.+/ && $$0 !~ /awk/){ system("kill -9 "$$2) }'

run_daemon:
	@holmes-api -vvv -c ./holmes/config/local.conf &

run: redis
	@holmes-api -vvv --debug -c ./holmes/config/local.conf

run-prod: redis
	@holmes-api -w 10 -c ./holmes/config/local.conf

worker:
	@holmes-worker -vvv -c ./holmes/config/local.conf -t 1

workers:
	@holmes-worker -c ./holmes/config/local.conf -t 10 -w 20

girl:
	@holmes-material -c ./holmes/config/local.conf -vvv

docs:
	@cd holmes/docs && make html && open _build/html/index.html

sqltap:
	@open 'http://localhost:8000/report.html'; python -m SimpleHTTPServer

publish:
	@python setup.py sdist upload

hon:
	@honcho start

ensure_crowdin_conf:
	@if [ ! -f ./crowdin.yaml ] ; then echo "\nWARNING:\n\nYou do not have a crowdin.yaml file.\\nThis configuration file is required in order to work with holmes translations.\\nThere's a sample file called crowdin.yaml.sample you can use to create your own version.\n\n" && exit 1; fi

ensure_directories:
	@mkdir -p ./holmes/i18n/{locale,sources}

extract_translations: ensure_directories
	@pybabel extract -F ./holmes/config/babel.conf -o ./holmes/i18n/sources/api.pot --add-comments=NOTE ./holmes/

upload_translations: ensure_crowdin_conf ensure_directories extract_translations
	@crowdin-cli upload sources

download_translations: ensure_crowdin_conf ensure_directories
	@crowdin-cli download
	@pybabel compile -D api -d ./holmes/i18n/locale
