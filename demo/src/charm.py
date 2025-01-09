#!/usr/bin/env python3
# Copyright 2025 Dave
# See LICENSE file for licensing details.

"""Charm the application."""

import logging

import ops

from services import DemoServices

logger = logging.getLogger(__name__)


class DemoCharm(ops.CharmBase):
    """Charm the application."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on["demo_container"].pebble_ready, self._on_pebble_ready)

        # Use self._pebble to interact with Pebble, the service manager in the workload container
        self._pebble = self.unit.get_container("demo-container")

        # Use self._services to specify the services and communicate with running services
        self._services = DemoServices()

    def _on_pebble_ready(self, event: ops.PebbleReadyEvent):
        """Handle pebble-ready event."""

        self._pebble.add_layer("base-layer", self._services.pebble_layer, combine=True)
        self._pebble.replan()

        self.unit.status = ops.ActiveStatus()

if __name__ == "__main__":  # pragma: nocover
    ops.main(DemoCharm)  # type: ignore
