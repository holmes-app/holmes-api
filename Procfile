redis: redis-server ./redis-honcho.conf
api: holmes-api -vvv --debug -c ./holmes/config/local.conf
workers: holmes-worker -vvv -c ./holmes/config/local.conf -t 10 -w 5
material: holmes-material -c ./holmes/config/local.conf -vvv
