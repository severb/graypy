Installing
==========

Using easy_install::

   easy_install graypy

Install with requirements for ``GELFRabbitHandler``::

  easy_install graypy[amqp]

Usage
=====

Messages are sent to Graylog2 using a custom handler for the builtin logging library in GELF format::

    import logging
    import graypy

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFHandler('localhost', 12201)
    my_logger.addHandler(handler)

    my_logger.debug('Hello Graylog2.')

Alternately, use ``GELFRabbitHandler`` to send messages to RabbitMQ and configure your Graylog2 server to consume messages via AMQP. This prevents log messages from being lost due to dropped UDP packets (``GELFHandler`` sends messages to Graylog2 using UDP). You will need to configure RabbitMQ with a 'gelf_log' queue and bind it to the 'logging.gelf' exchange so messages are properly routed to a queue that can be consumed by Graylog2 (the queue and exchange names may be customized to your liking)::

    import logging
    import graypy

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFRabbitHandler('amqp://guest:guest@localhost/', 'logging.gelf')
    my_logger.addHandler(handler)

    my_logger.debug('Hello Graylog2.')

Tracebacks are added as full messages::

    import logging
    import graypy

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFHandler('localhost', 12201)
    my_logger.addHandler(handler)

    try:
        puff_the_magic_dragon()
    except NameError:
        my_logger.debug('No dragons here.', exc_info=1)

Custom fields
=============

A number of custom fields are automatically added if available:
    * function
    * pid
    * process_name
    * thread_name

You can disable these additional fields if you don't want them by adding an argument to the hander::

    handler = graypy.GELFHandler('localhost', 12201, debugging_fields=False)

graypy also supports additional fields to be included in the messages sent to Graylog2. This can be done by using Python's LoggerAdapter_ and Filter_. In general, LoggerAdapter makes it easy to add static information to your log messages and Filters give you more flexibility, for example to add additional information based on the message that is being logged.

Example using LoggerAdapter_::

    import logging
    import graypy

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFHandler('localhost', 12201)
    my_logger.addHandler(handler)

    my_adapter = logging.LoggerAdapter(logging.getLogger('test_logger'),
                                        { 'username': 'John' })

    my_adapter.debug('Hello Graylog2 from John.')

Example using Filter_::

    import logging
    import graypy

    class UsernameFilter(logging.Filter):
        def __init__(self):
            # In an actual use case would dynamically get this (e.g. from memcache)
            self.username = "John"

        def filter(self, record):
            record.username = self.username
            return True

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFHandler('localhost', 12201)
    my_logger.addHandler(handler)

    my_logger.addFilter(UsernameFilter())

    mylogger.debug('Hello Graylog2 from John.')

Contributors:

  * Sever Banesiu
  * Daniel Miller

.. _LoggerAdapter: http://docs.python.org/howto/logging-cookbook.html#using-loggeradapters-to-impart-contextual-information
.. _Filter: http://docs.python.org/howto/logging-cookbook.html#using-filters-to-impart-contextual-information
