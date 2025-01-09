#!/usr/bin/env python3
# Copyright 2025 Dave
# See LICENSE file for licensing details.

"""Charm the application."""

import logging

import ops

from services import DemoServer

logger = logging.getLogger(__name__)


class DemoServerCharm(ops.CharmBase):
    """Charm the application."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on["demo_container"].pebble_ready, self._on_pebble_ready)

        # Use self._pebble to interact with Pebble, the container's service manager
        self._pebble = self.unit.get_container("demo-container")

        # Use self._services to TODO
        self._services = DemoServer()

    def _on_pebble_ready(self, event: ops.PebbleReadyEvent):
        """Handle pebble-ready event."""

        self._pebble.add_layer("demo-server", self._services.pebble_layer, combine=True)
        self._pebble.replan()

        self.unit.status = ops.ActiveStatus()

if __name__ == "__main__":  # pragma: nocover
    ops.main(DemoServerCharm)  # type: ignore
