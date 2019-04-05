#!/usr/bin/env bash

# stop the local graylog server used for integration testing graypy

# do work within ./test/config directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ${DIR}

docker-compose -f docker-compose.yml down
