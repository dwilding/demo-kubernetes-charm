#!/usr/bin/env python3

import logging
import secrets

import ops
import zinc


logger = logging.getLogger(__name__)
# TODO: Add logging statements


class ZincCharm(ops.CharmBase):
    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        framework.observe(
            self.on.zinc_pebble_ready,
            self._on_zinc_pebble_ready
        )
        framework.observe(
            self.on.get_admin_password_action,
            self._on_get_admin_password
        )
        self._pebble = self.unit.get_container("zinc") # For managing the workload container
        self._zinc_config = {
            "port": 4080,
            "admin_user": "admin",
            "admin_password": secrets.token_urlsafe(24),
        }
        self._zinc = zinc.ZincAPI(self._zinc_config["port"]) # For interacting with Zinc over HTTP

    def _on_zinc_pebble_ready(self, event: ops.PebbleReadyEvent):
        """Use Pebble to start Zinc."""
        self.unit.status = ops.MaintenanceStatus("configuring Zinc container")
        if not self._update_zinc_config_from_peer_relation():
            if self.unit.is_leader():
                self._update_peer_relation_from_zinc_config()
            else:
                event.defer() # Wait for the leader to put Zinc config in the peer relation
                return
        self._add_pebble_layer()
        self._pebble.replan()
        try:
            version = self._zinc.get_version()
        except RuntimeError as e:
            self.unit.status = ops.BlockedStatus(str(e))
            # TODO: Should we call event.defer() here?
            return
        self.unit.set_workload_version(version)
        self.unit.status = ops.ActiveStatus()
        # Open the port so that we can interact with Zinc from outside the pod
        self.unit.open_port(
            protocol="tcp",
            port=self._zinc_config["port"]
        )

    def _add_pebble_layer(self):
        # The OCI image for Zinc only has two binaries: zincsearch and go-runner
        # We'll use go-runner to achieve the equivalent of `bash -c '/bin/zincsearch | tee PATH'`
        # Testing only: To simulate a slow startup, we'll sleep for a few seconds before running zincsearch
        command = "/bin/dash -c '/bin/sleep 7 && /bin/go-runner --log-file=/var/lib/zincsearch/zinc.log --also-stdout=true --redirect-stderr=true /bin/zincsearch'"
        # This requires dash and sleep binaries to be injected into the Zinc container - don't do this in prod!
        self._push_binary_to_container("dash")
        self._push_binary_to_container("sleep")
        # Define a pebble layer and add it to the workload container
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
        }
        self._pebble.add_layer("zinc", layer, combine=True)

    def _push_binary_to_container(self, name: str):
        with open(f"/bin/{name}", "rb") as file:
            file_bytes = file.read()
        self._pebble.push(
            f"/bin/{name}",
            file_bytes,
            user_id=0,
            group_id=0,
            permissions=0o755
        )

    def _on_get_admin_password(self, event: ops.ActionEvent):
        """Return the initial admin password as an action response."""
        if not self._update_zinc_config_from_peer_relation():
            event.defer() # TODO: Change this
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