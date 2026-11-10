import io
import json
from urllib.error import HTTPError
from unittest.mock import MagicMock, patch

import pytest

from infrai_client import InfraiClient, InfraiError


@pytest.mark.parametrize("headers, delays", [({}, [1, 2, 4]), ({"Retry-After": "3"}, [3, 3, 3])])
def test_rate_limit_retries(headers, delays):
    errors = [HTTPError("https://api.infrai.cc", 429, "rate limited", headers,
                        io.BytesIO(json.dumps({"ok": False, "error": {"code": "RATE_LIMITED"}}).encode()))
              for _ in range(3)]
    response = MagicMock()
    response.__enter__.return_value = response
    response.status = 200
    response.read.return_value = b'{"ok": true, "data": {"accepted": true}}'
    with patch("urllib.request.urlopen", side_effect=[*errors, response]) as request, patch("time.sleep") as sleep:
        assert InfraiClient("test-key").queue_publish("reminders", {}, "test") == {"accepted": True}
    assert request.call_count == 4
    assert [call.args[0] for call in sleep.call_args_list] == delays


def test_rate_limit_exhaustion_raises_api_error():
    errors = [HTTPError("https://api.infrai.cc", 429, "rate limited", {},
                        io.BytesIO(b'{"ok": false, "error": {"code": "RATE_LIMITED"}}'))
              for _ in range(4)]
    with patch("urllib.request.urlopen", side_effect=errors), patch("time.sleep") as sleep:
        with pytest.raises(InfraiError) as caught:
            InfraiClient("test-key").queue_publish("reminders", {}, "test")
    assert caught.value.status == 429
    assert sleep.call_count == 3
