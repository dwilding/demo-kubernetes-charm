"""Standalone module for interacting with Zinc, with no charming context."""

import logging
import requests


logger = logging.getLogger(__name__)

# TODO: Add logging statements
# TODO: Add tests


class ZincAPI:
    """Client for interacting with Zinc over HTTP."""
    def __init__(self, port: int):
        self.port = port
        self.base_url = f"http://localhost:{self.port}"
        # Define a requests session that retries failed connections.
        self._session_with_retry = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            max_retries=requests.packages.urllib3.util.retry.Retry(
                total=4,
                backoff_factor=1
            ) # Retry after 0, 2, 4, 8 seconds
        )
        self._session_with_retry.mount("http://", adapter)

    def get_version(self, session: requests.Session | None = None) -> str:
        response = self._session_with_retry.get(
            f"{self.base_url}/version",
            timeout=5
        )
        response_dict = response.json()
        version = response_dict["version"].strip("'") # Version is double quoted
        return version