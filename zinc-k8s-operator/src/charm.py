#!/usr/bin/env python3

import logging
import secrets

import ops
import zinc


logger = logging.getLogger(__name__)

# TODO: Add logging statements
# TODO: Add tests


class ZincCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        self._observe_events(framework)
        self._pebble = self.unit.get_container("zinc") # For managing the workload container
        self._zinc_config = {
            "port": 4080,
            "admin_user": "admin",
            "admin_password": secrets.token_urlsafe(24),
        }
        self._zinc = zinc.ZincAPI(self._zinc_config["port"]) # For interacting with Zinc over HTTP

    def _observe_events(self, framework: ops.Framework):
        framework.observe(self.on.collect_unit_status, self._on_collect_unit_status)
        framework.observe(self.on["zinc"].pebble_ready, self._on_zinc_pebble_ready)
        framework.observe(self.on.get_admin_password_action, self._on_get_admin_password)

    def _on_collect_unit_status(self, event: ops.CollectStatusEvent):
        """Report the status of the unit."""
        event.add_status(self._get_unit_status_for_container())
        # For a more complex charm, there might be other aspects to check.

    def _get_unit_status_for_container(self) -> ops.StatusBase:
        """Determine the status of the workload container and return an appropriate unit status."""
        try:
            service_info = self._pebble.get_service("zinc")
        except (ops.pebble.APIError, ops.ModelError):
            return ops.MaintenanceStatus("waiting for Pebble to be ready")
        if not service_info.is_running():
            return ops.MaintenanceStatus("waiting for Zinc to start")
        # Zinc didn't exit on startup, but it might not be ready yet, so check its health.
        checks = self._pebble.get_checks(level=ops.pebble.CheckLevel.READY)
        for check_info in checks.values():
            if check_info.status == ops.pebble.CheckStatus.DOWN:
                return ops.MaintenanceStatus("waiting for Zinc to be ready")
                # TODO: Should we return BlockedStatus instead?
                #       To inspect failing checks, the admin could run:
                #       ```
                #       juju ssh <unit> PEBBLE_SOCKET=/charm/containers/zinc/pebble.socket \
                #       /charm/bin/pebble checks --level ready
                #       ```
                #       The command needs to be like this because the OCI image for Zinc has
                #       no shell binaries (so `juju ssh --container zinc <unit> ...` won't work).
        return ops.ActiveStatus()

    def _on_zinc_pebble_ready(self, event: ops.PebbleReadyEvent):
        """Use Pebble to start Zinc."""
        self.unit.status = ops.MaintenanceStatus("starting Zinc")
        if not self._update_zinc_config_from_peer_relation():
            if self.unit.is_leader():
                self._update_peer_relation_from_zinc_config()
            else:
                event.defer() # Wait for the leader to put Zinc config in the peer relation
                return
        self._add_pebble_layer()
        self._pebble.replan()
        version = self._zinc.get_version() # Retries with delay (in case of slow startup)
        self.unit.set_workload_version(version)

    def _add_pebble_layer(self):
        # The OCI image for Zinc only has two binaries: zincsearch and go-runner.
        # We use go-runner to achieve the equivalent of `bash -c '/bin/zincsearch | tee PATH'`.
        command = "/bin/go-runner --log-file=/var/lib/zincsearch/zinc.log --also-stdout=true --redirect-stderr=true /bin/zincsearch"
        # Define a pebble layer and add it to the workload container.
        layer: ops.pebble.LayerDict = {
            "summary": "Zinc service",
            "description": "Pebble layer that specifies how to run Zinc",
            "services": {
                "zinc": {
                    "override": "replace",
                    "summary": "zinc",
                    "command": command,
                    "startup": "enabled",
                    "environment": {
                        "ZINC_DATA_PATH": "/var/lib/zincsearch",
                        "ZINC_FIRST_ADMIN_USER": self._zinc_config["admin_user"],
                        "ZINC_FIRST_ADMIN_PASSWORD": self._zinc_config["admin_password"],
                    },
                },
            },
            "checks": {
                "zinc-ready": {
                    "override": "replace",
                    "level": "ready",
                    "period": "30s",
                    "timeout": "5s",
                    "threshold": 1,
                    "http": {
                        "url": f"{self._zinc.base_url}/version",
                    },
                }
            },
        }
        self._pebble.add_layer("zinc", layer, combine=True)

    def _on_get_admin_password(self, event: ops.ActionEvent):
        """Return the initial admin password as an action response."""
        if not self._update_zinc_config_from_peer_relation():
            event.fail("admin password is not available")
            return
        event.set_results({
            "admin-password": self._zinc_config["admin_password"]
        })

    def _update_zinc_config_from_peer_relation(self) -> bool:
        """Fetch the initial admin password from the peer relation."""
        relation = self.model.get_relation("zinc-peers")
        if not relation:
            return False # Relation not ready
        secret_id = relation.data[self.app].get("admin-password")
        if not secret_id:
            return False # Secret not available
        secret = self.model.get_secret(id=secret_id)
        self._zinc_config["admin_password"] = secret.peek_content()["password"]
        return True

    def _update_peer_relation_from_zinc_config(self) -> bool:
        """Store the initial admin password in the peer relation."""
        relation = self.model.get_relation("zinc-peers")
        if not relation:
            return False # Relation not ready
        secret = self.app.add_secret({
            "password": self._zinc_config["admin_password"]
        })
        relation.data[self.app]["admin-password"] = secret.id
        return True


if __name__ == "__main__":
    ops.main(ZincCharm)