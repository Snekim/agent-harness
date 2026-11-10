"""Acceptance check for the completed smoke task; expected to fail on the starter."""

import json
from http.client import HTTPResponse
from io import BytesIO

from server import Handler


class InMemoryHandler(Handler):
    def setup(self):
        self.rfile = BytesIO(b"GET /api/status HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.wfile = self.request

    def finish(self):
        pass


class ResponseStream:
    def __init__(self, buffer):
        self.buffer = buffer

    def makefile(self, *args):
        return self.buffer


# Exercise the real HTTP parser and handler without requiring a sandboxed port bind.
buffer = BytesIO()
InMemoryHandler(buffer, ("127.0.0.1", 0), None)
buffer.seek(0)
with HTTPResponse(ResponseStream(buffer)) as response:
    response.begin()
    assert response.status == 200, response.status
    assert response.headers.get_content_type() == "application/json", response.headers
    data = json.load(response)
    assert data.get("status") == "ok", data
    assert data.get("message") == "Service is healthy", data

print("Backend acceptance check passed")
