# Work in progress…

## 0-initial-charm

Comes from:

```
charmcraft init --profile kubernetes
```

## 1-better-initial-charm

In _charmcraft.yaml_:

  - Set `name` to `demo-charm`

  - Set `title` to `Demo Charm`

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
        upstream-source: workload-repo/container-image:tag
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