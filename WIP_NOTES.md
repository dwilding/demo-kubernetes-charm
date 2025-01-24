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
═══════════════════════════════════════════════════════
                                                       
 Charm container     Workload container                
━━━━━━━━━━━━━━━━┓   ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
 charm.py       ┃   ┃ Service manager                 ┃
 ▲              ┃   ┃ (self._pebble / event.workload) ┃
 └─ services.py ┃   ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
━━━━━━━━━━━━━━━━┛   ┃ Service 1                       ┃
                    ┃ Service 2 and so on…            ┃
                    ┃ (self._services)                ┃
                    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

```host
multipass launch --cpus 4 --disk 50G --memory 4G --name zinc-vm 24.04
mulitpass stop zinc-vm
multipass mount --type native ~/repos/dwilding/demo-kubernetes-charm zinc-vm:~/repo
multipass start zinc-vm
multipass shell zinc-vm
```

```zinc-vm
sudo snap install microk8s --channel 1.32-strict/stable
sudo adduser $USER snap_microk8s
newgrp snap_microk8s
microk8s status --wait-ready
sudo microk8s enable hostpath-storage

lxd init --auto

sudo snap install charmcraft --classic

sudo snap install juju
mkdir -p ~/.local/share
juju bootstrap microk8s microk8s-controller # Maybe change this because we get controller-microk8s-controller
juju add-model development
```

```host
cd ~/repos/dwilding/demo-kubernetes-charm
git clone https://github.com/operatorinc/zinc-k8s-operator.git
```

```zinc-vm
cd ~/repo/zinc-k8s-operator
charmcraft pack # charmcraft internal error: PermissionError(13, 'Permission denied')
```

Trying this instead...

```host
~/repos/dwilding/demo-kubernetes-charm/zinc-k8s-operator
charmcraft pack
```

```zinc-vm
cd ~/repo/zinc-k8s-operator
juju deploy ./zinc-k8s_ubuntu-22.04-amd64.charm --resource zinc-image=ghcr.io/jnsgruk/zinc:0.4.10
juju status --watch 1s
# Wait for active idle
curl http://10.1.107.76:4080/version
```

Summary:

```
# Deploy the charm
$ juju deploy ./zinc-k8s_ubuntu-22.04-amd64.charm --resource zinc-image=ghcr.io/jnsgruk/zinc:0.4.10

# Check that the status is active and the version is 0.4.10
$ juju status
Model        Controller           Cloud/Region        Version  SLA          Timestamp
development  microk8s-controller  microk8s/localhost  3.6.1    unsupported  11:11:32+08:00

App       Version  Status  Scale  Charm     Channel  Rev  Address         Exposed  Message
zinc-k8s  0.4.10   active      1  zinc-k8s            13  10.152.183.153  no       

Unit         Workload  Agent  Address      Ports  Message
zinc-k8s/0  active    idle   10.1.107.96

# Get the initial admin password from the leader unit
$ juju run zinc-k8s/0 get-admin-password
admin-password: KF3lLSbygt1fxL0CDKZLP_RqCAWAC52X

# Add another unit
$ juju add-unit zinc-k8s

# Show status again
$ juju status
Model        Controller           Cloud/Region        Version  SLA          Timestamp
development  microk8s-controller  microk8s/localhost  3.6.1    unsupported  11:15:41+08:00

App       Version  Status  Scale  Charm     Channel  Rev  Address         Exposed  Message
zinc-k8s  0.4.10   active      2  zinc-k8s            13  10.152.183.153  no       

Unit         Workload  Agent  Address      Ports  Message
zinc-k8s/0*  active    idle   10.1.107.96         
zinc-k8s/1   active    idle   10.1.107.97

# Check that the second unit has the same initial admin password
$ juju run zinc-k8s/1 get-admin-password
admin-password: KF3lLSbygt1fxL0CDKZLP_RqCAWAC52X
```


For debugging/testing, list binaries in the workload container of unit 0

```
$ ./pebble.sh 0 ls /bin
go-runner
zincsearch
```

Push `dash` and `sleep` from the charm container to the workload container
```
$ ./pebble.sh 0 push /bin/dash /bin/dash
$ ./pebble.sh 0 push /bin/sleep /bin/sleep
$ ./pebble.sh 0 ls /bin
dash
go-runner
sleep
zincsearch
```

Or at charm runtime:

```py
    # Testing only: To simulate a slow startup, we'll sleep for a few seconds before running zincsearch
    command = "/bin/dash -c '/bin/sleep 7 && /bin/go-runner --log-file=/var/lib/zincsearch/zinc.log --also-stdout=true --redirect-stderr=true /bin/zincsearch'"
    # This requires dash and sleep binaries to be injected into the Zinc container - don't do this in prod!
    self._push_binary_to_container("dash")
    self._push_binary_to_container("sleep")

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
    # TODO: Why doesn't self._pebble.push_path() work? Becuase it's not running as root?
```