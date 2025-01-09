"""Represents the services in the workload container.
The services are managed by Pebble."""

import logging

from ops import pebble

logger = logging.getLogger(__name__)


class DemoServices:
    def __init__(self):
        pass
        # TODO: What (if anything) would we typically do here?

    @property
    def pebble_layer(self) -> pebble.Layer:
        layer: pebble.LayerDict = {
            "summary": "Services in the workload container",
            "description": "Pebble layer that specifies the services"
            "services": {
                "demo-service": {
                    "override": "replace",
                    "summary": "A service in the workload container",
                    "command": "run-demo-service",
                    "startup": "enabled"
                }
            }
        }
        return pebble.layer(layer)

    # TODO: What else might this class typically provide?
    #       We might contact the service (via localhost) to get its version/status
    #
    #       BUT, suppose we want to push a new config file for a service...
    #       Can we use pebble.push() from within this module? Would we even want to do that?
    #       Would we be better to have this module build the service config,
    #       then charm.py uses self._pebble.push() - similarly to how we handle the layer spec
