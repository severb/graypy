######
graypy
######

.. image:: https://img.shields.io/pypi/v/graypy.svg
    :target: https://pypi.python.org/pypi/graypy
    :alt: PyPI Status

.. image:: https://travis-ci.org/severb/graypy.svg?branch=master
    :target: https://travis-ci.org/severb/graypy
    :alt: Build Status

.. image:: https://readthedocs.org/projects/graypy/badge/?version=stable
    :target: https://graypy.readthedocs.io/en/stable/?badge=stable
    :alt: Documentation Status

.. image:: https://codecov.io/gh/severb/graypy/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/severb/graypy
    :alt: Coverage Status

Description
===========

Python logging handlers that send log messages in the
Graylog Extended Log Format (GELF_).

graypy supports sending GELF logs to both Graylog2 and Graylog3 servers.

Installing
==========

Using pip
---------

Install the basic graypy python logging handlers:

.. code-block:: console

    pip install graypy

Install with requirements for ``GELFRabbitHandler``:

.. code-block:: console

    pip install graypy[amqp]

Using easy_install
------------------

Install the basic graypy python logging handlers:

.. code-block:: console

    easy_install graypy

Install with requirements for ``GELFRabbitHandler``:

.. code-block:: console

    easy_install graypy[amqp]

Usage
=====

graypy sends GELF logs to a Graylog server via subclasses of the python
`logging.Handler`_ class.

Below is the list of ready to run GELF logging handlers defined by graypy:

* ``GELFUDPHandler`` - UDP log forwarding
* ``GELFTCPHandler`` - TCP log forwarding
* ``GELFTLSHandler`` - TCP log forwarding with TLS support
* ``GELFHTTPHandler`` - HTTP log forwarding
* ``GELFRabbitHandler`` - RabbitMQ log forwarding

UDP Logging
-----------

UDP Log forwarding to a locally hosted Graylog server can be easily done with
the ``GELFUDPHandler``:

.. code-block:: python

    import logging
    import graypy

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFUDPHandler('localhost', 12201)
    my_logger.addHandler(handler)

    my_logger.debug('Hello Graylog.')

RabbitMQ Logging
----------------

Alternately, use ``GELFRabbitHandler`` to send messages to RabbitMQ and
configure your Graylog server to consume messages via AMQP. This prevents log
messages from being lost due to dropped UDP packets (``GELFUDPHandler`` sends
messages to Graylog using UDP). You will need to configure RabbitMQ with a
``gelf_log`` queue and bind it to the ``logging.gelf`` exchange so messages
are properly routed to a queue that can be consumed by Graylog (the queue and
exchange names may be customized to your liking).

.. code-block:: python

    import logging
    import graypy

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFRabbitHandler('amqp://guest:guest@localhost/', exchange='logging.gelf')
    my_logger.addHandler(handler)

    my_logger.debug('Hello Graylog.')

Django Logging
--------------

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

Traceback Logging
-----------------

By default log captured exception tracebacks are added to the GELF log as
``full_message`` fields:

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

Default Logging Fields
----------------------

By default a number of debugging logging fields are automatically added to the
GELF log if available:

    * function
    * pid
    * process_name
    * thread_name

You can disable automatically adding these debugging logging fields by
specifying ``debugging_fields=False`` in the handler's constructor:

.. code-block:: python

    handler = graypy.GELFUDPHandler('localhost', 12201, debugging_fields=False)

Adding Custom Logging Fields
----------------------------

graypy also supports including custom fields in the GELF logs sent to Graylog.
This can be done by using Python's LoggerAdapter_ and Filter_ classes.

Using LoggerAdapter
^^^^^^^^^^^^^^^^^^^

LoggerAdapter_ makes it easy to add static information to your GELF log
messages:

.. code-block:: python

    import logging
    import graypy

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFUDPHandler('localhost', 12201)
    my_logger.addHandler(handler)

    my_adapter = logging.LoggerAdapter(logging.getLogger('test_logger'),
                                       {'username': 'John'})

    my_adapter.debug('Hello Graylog from John.')

Using Filter
^^^^^^^^^^^^

Filter_ gives more flexibility and allows for dynamic information to be
added to your GELF logs:

.. code-block:: python

    import logging
    import graypy

    class UsernameFilter(logging.Filter):
        def __init__(self):
            # In an actual use case would dynamically get this
            # (e.g. from memcache)
            self.username = 'John'

        def filter(self, record):
            record.username = self.username
            return True

    my_logger = logging.getLogger('test_logger')
    my_logger.setLevel(logging.DEBUG)

    handler = graypy.GELFUDPHandler('localhost', 12201)
    my_logger.addHandler(handler)

    my_logger.addFilter(UsernameFilter())

    my_logger.debug('Hello Graylog from John.')

Contributors
============

  * Sever Banesiu
  * Daniel Miller
  * Tushar Makkar
  * Nathan Klapstein

.. _GELF: https://docs.graylog.org/en/latest/pages/gelf.html
.. _logging.Handler: https://docs.python.org/3/library/logging.html#logging.Handler
.. _LoggerAdapter: https://docs.python.org/howto/logging-cookbook.html#using-loggeradapters-to-impart-contextual-information
.. _Filter: https://docs.python.org/howto/logging-cookbook.html#using-filters-to-impart-contextual-information
