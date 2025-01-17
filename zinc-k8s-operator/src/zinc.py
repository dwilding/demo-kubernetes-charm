"""Standalone module for interacting with Zinc, with no charming context."""

import logging
import requests
import time


logger = logging.getLogger(__name__)
# TODO: Add logging statements


class ZincAPI:
    """Client for interacting with Zinc over HTTP."""
    def __init__(self, port: int):
        self.port = port

    def get_version(self) -> str:
        try:
            response = self._get_with_retry(f"http://localhost:{self.port}/version")
        except requests.exceptions.RequestException:
            raise RuntimeError("unable to get version from Zinc")
        try:
            response_dict = response.json()
        except requests.exceptions.JSONDecodeError:
            raise RuntimeError("received invalid version from Zinc")
        version = response_dict["version"].strip("'") # Version is double quoted for some reason
        return version

    def _get_with_retry(self, url: str) -> requests.Response:
        wait_interval = 5 # wait 5 seconds between attempts
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                return requests.get(url, timeout=wait_interval)
            except requests.exceptions.ConnectionError:
                time.sleep(wait_interval)
            except requests.exceptions.Timeout:
                continue
        raise requests.exceptions.RequestException("no response from Zinc")