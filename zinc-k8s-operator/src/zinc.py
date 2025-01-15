"""A standalone module for managing Zinc, with no charming context."""

from dataclasses import dataclass

import logging
import secrets
import requests


logger = logging.getLogger(__name__)


@dataclass
class ZincConfig:
    """Represents a configuration of Zinc"""
    port: int = 4080
    admin_user: str = "admin"
    admin_password: str = ""

    def generate_admin_password(self):
        self.admin_password = secrets.token_urlsafe(24)


class Zinc:
    """Represents a configured & running instance of Zinc."""
    def __init__(self, config: ZincConfig):
        self.config = config

    @property
    def version(self) -> str:
        response = requests.get(
            f"http://localhost:{self.config.port}/version",
            timeout=10
        )
        response_dict = response.json()
        version = response_dict["version"].strip("'") # Version is double quoted for some reason
        return version