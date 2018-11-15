import pytest
from graypy import GELFTCPHandler, GELFUDPHandler
from tests.helper import get_unique_message, log_warning


STATIC_FIELDS = {
    '_ozzy': 'diary of a madman',
    '_van_halen': 1984,
    '_id': 42
}


@pytest.fixture(params=[
    GELFTCPHandler(host='127.0.0.1', port=12201, **STATIC_FIELDS),
    GELFUDPHandler(host='127.0.0.1', port=12202, **STATIC_FIELDS),
    GELFUDPHandler(host='127.0.0.1', port=12202, compress=False, **STATIC_FIELDS),
    GELFTCPHandler(host='127.0.0.1', port=12201, ),
    GELFUDPHandler(host='127.0.0.1', port=12202, ),
    GELFUDPHandler(host='127.0.0.1', port=12202, compress=False),
])
def handler(request):
    return request.param


def test_static_fields(logger):
    message = get_unique_message()
    graylog_response = log_warning(logger, message, fields=['ozzy', 'van_halen'])
    assert graylog_response['message'] == message
    assert graylog_response['ozzy'] == 'diary of a madman'
    assert graylog_response['van_halen'] == 1984
    assert graylog_response['_id'] != 42
    assert 'id' not in graylog_response
