rabbitmqctl add_user graylog graylog
rabbitmqctl set_user_tags graylog administrator
rabbitmqctl set_permissions -p / graylog ".*" ".*" ".*"

rabbitmqadmin declare exchange name=log-messages type=direct -u graylog -p graylog