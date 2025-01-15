#!/usr/bin/env python3

import logging

import ops

from zinc import ZincConfig, Zinc


logger = logging.getLogger(__name__)


class ZincWorkload():
    """Represents Zinc inside its container."""

    def __init__(self, config: ZincConfig):
        self.config = config
        self.zinc = Zinc(config) # Zinc with no charming context

    @property
    def command(self) -> str:
        # go-runner achieves the equivalent of:`bash -c '/bin/zinc | tee PATH'`, but
        # without including bash etc. in the image.
        return "/bin/go-runner --log-file=/var/lib/zincsearch/zinc.log --also-stdout=true --redirect-stderr=true /bin/zincsearch"

    @property
    def pebble_layer(self) -> ops.pebble.Layer:
        if not self.config.admin_password:
            raise RuntimeError("Initial admin password is empty")
        layer: ops.pebble.LayerDict = {
            "summary": "Zinc service",
            "description": "Pebble layer that specifies how to run Zinc",
            "services": {
                "zinc": {
                    "override": "replace",
                    "summary": "zinc",
                    "command": self.command,
                    "startup": "enabled",
                    "environment": {
                        "ZINC_DATA_PATH": "/var/lib/zincsearch",
                        "ZINC_FIRST_ADMIN_USER": self.config.admin_user,
                        "ZINC_FIRST_ADMIN_PASSWORD": self.config.admin_password,
                    },
                },
            },
        }
        return ops.pebble.Layer(layer)

    @property
    def version(self) -> str:
        return self.zinc.version


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
        self._pebble = self.unit.get_container("zinc") # For managing the container

    def _on_zinc_pebble_ready(self, event: ops.PebbleReadyEvent):
        """Configure Zinc and use Pebble to start Zinc."""
        # Configure Zinc
        config = ZincConfig()
        if not self._update_config_from_peer_relation(config):
            if self.unit.is_leader():
                config.generate_admin_password()
                self._update_peer_relation_from_config(config)
            else:
                event.defer() # Wait for the leader put Zinc config in the peer relation
                return
        zinc = ZincWorkload(config)
        # Use Pebble to start Zinc
        self._pebble.add_layer("zinc", zinc.pebble_layer, combine=True)
        self._pebble.replan()
        self.unit.open_port(
            protocol="tcp",
            port=config.port
        )
        self.unit.status = ops.ActiveStatus()
        self.unit.set_workload_version(zinc.version)

    def _on_get_admin_password(self, event: ops.ActionEvent):
        """Return the initial admin password as an action response."""
        config = ZincConfig()
        if not self._update_config_from_peer_relation(config):
            event.defer() # TODO: Does it make sense to defer this event?
            return
        event.set_results({
            "admin-password": config.admin_password
        })

    def _update_config_from_peer_relation(self, config: ZincConfig) -> bool:
        """Get the initial admin password from the peer relation, then configure Zinc."""
        relation = self.model.get_relation("zinc-peers")
        if not relation:
            return False # Relation not ready
        secret_id = relation.data[self.app].get("admin-password")
        if not secret_id:
            return False # Secret not available
        secret = self.model.get_secret(id=secret_id)
        config.admin_password = secret.peek_content()["password"]
        return True

    def _update_peer_relation_from_config(self, config: ZincConfig) -> bool:
        """Set the initial admin password in the peer relation, based on Zinc config."""
        relation = self.model.get_relation("zinc-peers")
        if not relation:
            return False # Relation not ready
        secret = self.app.add_secret({
            "password": config.admin_password
        })
        relation.data[self.app]["admin-password"] = secret.id
        return True


if __name__ == "__main__":
    ops.main(ZincCharm)