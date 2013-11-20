test: redis drop_test data_test unit integration kill_run

unit:
	@coverage run --branch `which nosetests` -vv --with-yanc -s tests/unit/
	@coverage report -m --fail-under=90

coverage-html: unit
	@coverage html -d cover

integration: kill_run run_daemon
	@`which nosetests` -vv --with-yanc -s tests/integration/;EXIT_CODE=$$?;$(MAKE) kill_run;exit $(EXIT_CODE)

tox:
	@PATH=$$PATH:~/.pythonbrew/pythons/Python-2.6.*/bin/:~/.pythonbrew/pythons/Python-2.7.*/bin/:~/.pythonbrew/pythons/Python-3.0.*/bin/:~/.pythonbrew/pythons/Python-3.1.*/bin/:~/.pythonbrew/pythons/Python-3.2.3/bin/:~/.pythonbrew/pythons/Python-3.3.0/bin/ tox

setup:
	@pip install -U -e .\[tests\]

kill_redis:
	-redis-cli -p 7575 shutdown

redis: kill_redis
	redis-server ./redis.conf; sleep 1
	redis-cli -p 7575 info > /dev/null

drop:
	@-cd holmes/ && alembic downgrade base
	@mysql -u root -e "DROP DATABASE IF EXISTS holmes; CREATE DATABASE IF NOT EXISTS holmes"
	@echo "DB RECREATED"

drop_test:
	@-cd tests/ && alembic downgrade base
	@mysql -u root -e "DROP DATABASE IF EXISTS test_holmes; CREATE DATABASE IF NOT EXISTS test_holmes"
	@echo "DB RECREATED"

data:
	@cd holmes/ && alembic upgrade head

data_test:
	@cd tests/ && alembic upgrade head

migration:
	@cd holmes/ && alembic revision -m "$(DESC)"

kill_run:
	@ps aux | awk '(/.+holmes-api.+/ && $$0 !~ /awk/){ system("kill -9 "$$2) }'

run_daemon:
	@holmes-api -vvv -c ./holmes/config/local.conf &

run:
	@holmes-api -vvv --debug -c ./holmes/config/local.conf

worker:
	@holmes-worker -vvv -c ./holmes/config/local.conf -t 1

workers:
	@holmes-worker -c ./holmes/config/local.conf -t 200 -w 20
