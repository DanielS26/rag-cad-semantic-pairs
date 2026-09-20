"""CPU tests must not open network connections or load a real encoder."""

import socket

import pytest


@pytest.fixture(autouse=True)
def refuse_network(monkeypatch):
    def refused(*args, **kwargs):
        raise AssertionError("CPU tests must use fake transports, not the network")

    monkeypatch.setattr(socket.socket, "connect", refused)
    monkeypatch.setattr(socket, "create_connection", refused)