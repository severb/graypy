from graypy.handler import GELFHandler, WAN_CHUNK, LAN_CHUNK
try:
    from graypy.rabbitmq import GELFRabbitHandler, ExcludeFilter
except ImportError:
    pass # amqplib is probably not installed
