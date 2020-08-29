#!/usr/bin/env bash

# start a local graylog server for integration testing graypy

# do work within ./test/config directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ${DIR}

# remove a potential previous setup
docker-compose -f docker-compose-rmq.yml down
docker-compose -f docker-compose.yml down

# first setup RabbitMQ, as it requires extra setup before Graylog can connect to it.
docker-compose -f docker-compose-rmq.yml up -d

# wait for RabbitMQ to start
sleep 30

# Configure a user and exchange for graylog to use
RMQ_CONTAINER_ID="$(docker ps -qf "name=rabbit")"
docker exec -ti ${RMQ_CONTAINER_ID} sh /usr/local/bin/setup_rabbitmq.sh

# create ssl certs for enabling the graylog server to use a
# TLS connection for GELF input
bash create_ssl_certs.sh -h localhost -i 127.0.0.1

# start the graylog server docker container
docker-compose -f docker-compose.yml up -d

# wait for the graylog server docker container to start
sleep 40

# test that the graylog server docker container is started
curl -u admin:admin 'http://127.0.0.1:9000/api/search/universal/relative?query=test&range=5&fields=message' || true
