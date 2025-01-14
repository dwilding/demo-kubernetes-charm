"""A standalone module for managing the workload, with no charming context."""

from dataclasses import dataclass

import logging


logger = logging.getLogger(__name__)


@dataclass
class DemoServerConfig:
    """Represents a configuration of the workload."""
    port: int # (example)


class DemoServer:
    """Represents a configured & running instance of the workload."""
    def __init__(self, config: DemoServerConfig):
        self.config = config

    @property
    def version(self) -> str:
        return '1.0.0' # Implement this by communicating with the running instance
