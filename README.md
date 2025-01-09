# Work in progress…

## Step 1

```sh
mkdir demo-server # The name of the dir is important, as it will be included in the charm metadata
cd demo-server
charmcraft init --profile kubernetes
```

## Step 2

In _charmcraft.yaml_:

  - Change `title` from `Charm Template` to `Demo Server`

  - After the `bases` block, add:

    ```yaml
    # (Optional, but recommended for Kubernetes charms)
    assumes:
      - juju >= 3.6
      - k8s-api
    ```

  - Replace the `containers` block by:

    ```yaml
    # Your workload’s containers.
    containers:
      demo-container:
        resource: demo-container-image
    ```

  - Replace the `resources` block by:

    ```yaml
    # This field populates the Resources tab on Charmhub.
    resources:
      # An OCI image resource for each container listed above.
      # You may remove this if your charm will run without a workload sidecar container.
      demo-container-image:
        type: oci-image
        description: OCI image for the 'demo-container' container
        # The upstream-source field is ignored by Juju. It is included here as a reference
        # so the integration testing suite knows which image to deploy during testing. This field
        # is also used by the 'canonical/charming-actions' Github action for automated releasing.
        upstream-source: some-repo/some-image:some-tag
    ```

In _src/charm.py_:

  - Replace:

    ```py
    self.on["some_container"]
    ```

    by:

    ```py
    self.on["demo_container"]
    ```

TODO: In _requirements.txt_, does `ops ~= 2.8` need changing?


## An artistic interlude

```
Unit (self.unit)
═══════════════════════════════════════════════════
charm.py         Container                         
▲               ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
│               ┃ Service manager                 ┃
│               ┃ (self._pebble / event.workload) ┃
└─ services.py  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
                ┃ Service 1                       ┃
                ┃ Service 2 and so on…            ┃
                ┃ (self._services)                ┃
                ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```