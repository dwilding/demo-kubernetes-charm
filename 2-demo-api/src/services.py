"""Description TODO"""

import logging

from ops import pebble

logger = logging.getLogger(__name__)


class DemoServer:
    def __init__(self):
        pass
        # TODO: What might we typically do here?

    @property
    def _pebble_layer(self) -> pebble.Layer:
        pass
        # TODO: Return the layer

    # TODO: What else might this class typically provide?
