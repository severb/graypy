#! /usr/bin/env python
import argparse
import logging
import logging.config
import sys
import time

def main(argv=sys.argv):
    parser = argparse.ArgumentParser(prog="perftest.py")
    parser.add_argument('--graylog-host',
        help='Graylog2 host. Do not test GELFHandler if not specified.')
    parser.add_argument('--graylog-port', type=int, default=12201,
        help='Graylog2 GELF UDP port. Default: 12201')
    parser.add_argument('--graylog-chunked', action='store_true', default=None,
        help='Test graylog with chunked messages')
    parser.add_argument('--rabbit-url',
        help='RabbitMQ url (ex: amqp://guest:guest@localhost/). '
             'Do not test GELFRabbitHandler if not specified.')
    parser.add_argument('--rabbit-exchange', default='logging.gelf',
        help='RabbitMQ exchange. Default: logging.gelf')
    parser.add_argument('--console-logger', action='store_true', default=None)
    parser.add_argument('--stress', action='store_true',
        help='Enable performance/stress test. WARNING this logs MANY warnings.')
    args = parser.parse_args(argv[1:])

    if all(v is None for v in
            [args.graylog_host, args.rabbit_url, args.console_logger]):
        parser.print_help()

    config = {
        'version': 1,
        'formatters': {
            'brief': {'format': "%(levelname)-7s %(name)s - %(message)s"},
            'message': {'format': "%(message)s"},
        },
        'handlers': {},
        'root': {'handlers': [], 'level': 'DEBUG'},
        'disable_existing_loggers': False,
    }
    
    if args.graylog_host is not None:
        config['handlers']['graylog_udp'] = {
            'class': 'graypy.GELFHandler',
            'host': args.graylog_host,
            'port': args.graylog_port,
            'debugging_fields': 0,
            'formatter': 'message',
        }
        if args.graylog_chunked:
            config['handlers']['graylog_udp']['chunk_size'] = 1

        config['root']['handlers'].append('graylog_udp')

    if args.rabbit_url is not None:
        config['handlers']['graylog_rabbit'] = {
            'class': 'graypy.GELFRabbitHandler',
            'url': args.rabbit_url,
            'exchange': args.rabbit_exchange,
            'debugging_fields': 0,
            'formatter': 'message',
        }
        config['root']['handlers'].append('graylog_rabbit')

    if args.console_logger:
        config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'formatter': 'brief',
        }
        config['root']['handlers'].append('console')

    logging.config.dictConfig(config)

    log = logging.getLogger()
    t_start = time.time()
    total = 0

    log.debug('debug')
    log.info('info')
    log.warn('warning')
    log.error('error')
    log.critical('critical')
    total += 5

    if args.stress:
        t_end = time.time() + 10
        tx = t_end - 9
        cx = 0
        while True:
            log.warn('warning')
            cx += 1
            total += 1
            if time.time() > tx:
                elapsed = time.time() - (tx - 1)
                tx += 1
                print('%s messages in %.3f seconds (%.3f msg/s)'
                    % (cx, elapsed, cx / elapsed))
                cx = 0
                if tx > t_end:
                    break

    elapsed = time.time() - t_start
    print('%s messages in %.3f seconds (%.3f msg/s)'
        % (total, elapsed, total / elapsed))

if __name__ == '__main__':
    main()
