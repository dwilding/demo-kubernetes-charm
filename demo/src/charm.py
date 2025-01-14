#!/usr/bin/env python3
# Copyright 2025 Dave
# See LICENSE file for licensing details.

"""Charm the application."""

import logging

import ops

from demo_server import DemoServerConfig, DemoServer


logger = logging.getLogger(__name__)


class DemoServerWorkload():
    """Represents the workload inside its container."""

    def __init__(self):
        self.config = DemoServerConfig(
            port=8000 # (example)
        )
        self.demo_server = DemoServer(self.config) # The actual workload, with no charming context

    @property
    def command() -> str:
        return f"run-demo-server --port={self.config.port}" # (example)

    @property
    def pebble_layer() -> ops.pebble.pebbleLayer:
        layer: ops.pebble.LayerDict = {
            "summary": "The workload's services",
            "description": "Pebble layer that specifies how to run the workload"
            "services": {
                "demo-server": {
                    "override": "replace",
                    "summary": "demo-server",
                    "command": self.command,
                    "startup": "enabled"
                }
            }
        }
        return ops.pebble.layer(layer)

    @property
    def version() -> str:
        return self.demo_server.version


class DemoServerCharm(ops.CharmBase):
    """Charm the application."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on["demo_container"].pebble_ready, self._on_pebble_ready)

        self._workload = DemoServerWorkload() # For managing the workload inside its container
        self._pebble = self.unit.get_container("demo-container") # For managing the container itself

    def _on_pebble_ready(self, event: ops.PebbleReadyEvent):
        """Handle pebble-ready event."""

        self._pebble.add_layer("workload-layer", self._workload.pebble_layer, combine=True)
        self._pebble.replan()

        self.unit.status = ops.ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main(DemoServerCharm)  # type: ignore
