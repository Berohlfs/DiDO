"""Matrix 6 — auth.TokenProvider(config, http_post) (fake transport)."""
import json
import unittest
import urllib.parse

from ingest import auth
from ingest.config import Config
from ingest.transport import HttpResponse


def cfg():
    return Config(
        base_url="http://localhost:8787",
        client_id="cl_id",
        client_secret="cs_secret",
        scopes="read write",
    )


class FakeTransport:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def __call__(self, url, data, headers):
        self.calls.append({"url": url, "data": data, "headers": headers})
        return self._responses.pop(0)


def token_response(access_token="tok-1"):
    body = json.dumps({"access_token": access_token, "token_type": "Bearer"}).encode()
    return HttpResponse(200, {"content-type": "application/json"}, body)


class TestTokenProvider(unittest.TestCase):
    # Matrix 6: mint success → token returned + correct form body
    def test_mint_success_and_form_body(self):
        fake = FakeTransport([token_response("tok-1")])
        tp = auth.TokenProvider(cfg(), http_post=fake)
        self.assertEqual(tp.get_token(), "tok-1")
        call = fake.calls[0]
        self.assertEqual(call["url"], "http://localhost:8787/token")
        form = urllib.parse.parse_qs(call["data"].decode())
        self.assertEqual(form["grant_type"], ["client_credentials"])
        self.assertEqual(form["client_id"], ["cl_id"])
        self.assertEqual(form["client_secret"], ["cs_secret"])
        self.assertEqual(form["scope"], ["read write"])

    # Matrix 6: get_token caches (second call → no second request)
    def test_get_token_caches(self):
        fake = FakeTransport([token_response("tok-1")])
        tp = auth.TokenProvider(cfg(), http_post=fake)
        tp.get_token()
        tp.get_token()
        self.assertEqual(len(fake.calls), 1)

    # Matrix 6: refresh() forces a new mint
    def test_refresh_forces_new_mint(self):
        fake = FakeTransport([token_response("tok-1"), token_response("tok-2")])
        tp = auth.TokenProvider(cfg(), http_post=fake)
        self.assertEqual(tp.get_token(), "tok-1")
        self.assertEqual(tp.refresh(), "tok-2")
        self.assertEqual(tp.get_token(), "tok-2")
        self.assertEqual(len(fake.calls), 2)

    # Matrix 6: token-endpoint error → clear error
    def test_error_raises(self):
        err = HttpResponse(400, {}, json.dumps({"error": "invalid_client"}).encode())
        fake = FakeTransport([err])
        tp = auth.TokenProvider(cfg(), http_post=fake)
        with self.assertRaises(auth.TokenError):
            tp.get_token()


if __name__ == "__main__":
    unittest.main()
