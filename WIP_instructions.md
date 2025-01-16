```host
multipass launch --cpus 4 --disk 50G --memory 4G --name zinc-vm 24.04
mulitpass stop zinc-vm
multipass mount --type native ~/workspace/zinc-vm-250114 zinc-vm:~/outside
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
cd ~/workspace/zinc-vm-250114
git clone https://github.com/operatorinc/zinc-k8s-operator.git
```

```zinc-vm
cd ~/outside/zinc-k8s-operator
charmcraft pack # charmcraft internal error: PermissionError(13, 'Permission denied')
```

Trying this instead...

```host
cd ~/workspace/zinc-vm-250114
charmcraft pack
```

```zinc-vm
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