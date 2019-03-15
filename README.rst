######
graypy
######

.. image:: https://travis-ci.org/severb/graypy.svg?branch=master
    :target: https://travis-ci.org/severb/graypy
    :alt: Build Status

.. image:: https://codecov.io/gh/severb/graypy/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/severb/graypy
    :alt: Coverage Status

.. image:: https://img.shields.io/pypi/v/graypy.svg
    :target: https://pypi.python.org/pypi/graypy
    :alt: PyPI Status

Description
===========

Python logging handlers that send messages in the Graylog Extended
Log Format (GELF_).

Installing
==========

Using pip
---------

Install the basic graypy python logging handlers

.. code-block:: bash

    pip install graypy

Install with requirements for :class:`graypy.rabbitmq.GELFRabbitHandler`

.. code-block:: bash

    pip install graypy[amqp]

Using easy_install
------------------

Install the basic graypy python logging handlers

.. code-block:: bash

   easy_install graypy

Install with requirements for :class:`graypy.rabbitmq.GELFRabbitHandler`

.. code-block:: bash

  easy_install graypy[amqp]

Usage
=====

Messages are sent to Graylog2 using a custom handler for the builtin logging
library in GELF format

.. code-block:: python

    import logging
    import graypy

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFUDPHandler('localhost', 12201)
    my_logger.addHandler(handler)

    my_logger.debug('Hello Graylog2.')

Alternately, use :class:`graypy.rabbitmq.GELFRabbitHandler` to send messages
to RabbitMQ and configure your Graylog2 server to consume messages via AMQP.
This prevents log messages from being lost due to dropped UDP packets
(:class:`graypy.handler.GELFUDPHandler` sends messages to Graylog2 using UDP).
You will need to configure RabbitMQ with a 'gelf_log' queue and bind it to the
'logging.gelf' exchange so messages are properly routed to a queue that can be
consumed by Graylog2 (the queue and exchange names may be customized to
your liking).

.. code-block:: python

    import logging
    import graypy

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFRabbitHandler('amqp://guest:guest@localhost/', exchange='logging.gelf')
    my_logger.addHandler(handler)

    my_logger.debug('Hello Graylog2.')

Tracebacks are added as full messages

.. code-block:: python

    import logging
    import graypy

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFUDPHandler('localhost', 12201)
    my_logger.addHandler(handler)

    try:
        puff_the_magic_dragon()
    except NameError:
        my_logger.debug('No dragons here.', exc_info=1)


For more detailed usage information please see the documentation provided
within graypy's handler's docstrings.

Using with Django
=================

It's easy to integrate ``graypy`` with Django's logging settings. Just add a
new handler in your ``settings.py``:

.. code-block:: python

    LOGGING = {
        ...

        'handlers': {
            'graypy': {
                'level': 'WARNING',
                'class': 'graypy.GELFUDPHandler',
                'host': 'localhost',
                'port': 12201,
            },
        },

        'loggers': {
            'django.request': {
                'handlers': ['graypy'],
                'level': 'ERROR',
                'propagate': True,
            },
        },
    }

Custom fields
=============

A number of custom fields are automatically added if available:
    * function
    * pid
    * process_name
    * thread_name

You can disable these additional fields if you don't want them by adding
an the ``debugging_fields=False`` to the handler:

.. code-block:: python

    handler = graypy.GELFUDPHandler('localhost', 12201, debugging_fields=False)

graypy also supports additional fields to be included in the messages sent
 to Graylog2. This can be done by using Python's LoggerAdapter_ and
Filter_. In general, LoggerAdapter makes it easy to add static information
to your log messages and Filters give you more flexibility, for example to
add additional information based on the message that is being logged.

Example using LoggerAdapter_

.. code-block:: python

    import logging
    import graypy

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFUDPHandler('localhost', 12201)
    my_logger.addHandler(handler)

    my_adapter = logging.LoggerAdapter(logging.getLogger('test_logger'),
                                       {'username': 'John'})

    my_adapter.debug('Hello Graylog2 from John.')

Example using Filter_

.. code-block:: python

    import logging
    import graypy

    class UsernameFilter(logging.Filter):
        def __init__(self):
            # In an actual use case would dynamically get this
            # (e.g. from memcache)
            self.username = "John"

        def filter(self, record):
            record.username = self.username
            return True

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFUDPHandler('localhost', 12201)
    my_logger.addHandler(handler)

    my_logger.addFilter(UsernameFilter())

    my_logger.debug('Hello Graylog2 from John.')

Contributors:

  * Sever Banesiu
  * Daniel Miller
  * Tushar Makkar
  * Nathan Klapstein

.. _GELF: http://docs.graylog.org/en/latest/pages/gelf.html
.. _LoggerAdapter: http://docs.python.org/howto/logging-cookbook.html#using-loggeradapters-to-impart-contextual-information
.. _Filter: http://docs.python.org/howto/logging-cookbook.html#using-filters-to-impart-contextual-information
