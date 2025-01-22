"""Standalone module for interacting with Zinc, with no charming context."""

import logging
import requests


logger = logging.getLogger(__name__)
# TODO: Add logging statements


class ZincAPI:
    """Client for interacting with Zinc over HTTP."""
    def __init__(self, port: int):
        self.port = port
        # Define a requests session that retries failed connections
        self._requests = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            max_retries=requests.packages.urllib3.util.retry.Retry(
                total=4,
                backoff_factor=1
            ) # Retry after 0, 2, 4, 8 seconds
        )
        self._requests.mount("http://", adapter)

    def get_version(self) -> str:
        response = self._requests.get(f"http://localhost:{self.port}/version", timeout=5)
        response_dict = response.json()
        version = response_dict["version"].strip("'") # Version is double quoted for some reason
        return version