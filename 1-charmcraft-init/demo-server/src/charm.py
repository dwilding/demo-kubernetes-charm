#!/usr/bin/env python3
# Copyright 2025 Dave
# See LICENSE file for licensing details.

"""Charm the application."""

import logging

import ops

logger = logging.getLogger(__name__)


class DemoServerCharm(ops.CharmBase):
    """Charm the application."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(self.on["some_container"].pebble_ready, self._on_pebble_ready)

    def _on_pebble_ready(self, event: ops.PebbleReadyEvent):
        """Handle pebble-ready event."""
        self.unit.status = ops.ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main(DemoServerCharm)  # type: ignore
