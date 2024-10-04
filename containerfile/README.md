# Using containerized client interfaces

Provides a containerized environment to run client commands, including `oc` and `ansible`.

## Creating the container image

### Prerequisite

You must have a valid account to access `registry.redhat.io`.

### Build

Using buildah or podman, run the following commands from the root of
the repository:

```Bash
$ buildah bud -t rhoso-gitops:latest -f containerfile/oc-client .
$ podman build -t rhoso-gitops:latest -f containerfile/oc-client .
```

## Using the container image

Use `podman` to connect to the the container image and access the clients:

```Bash
$ podman run --rm -ti \
    -v $HOME/.kube:/root/.kube \
    --security-opt label=disable \
    rhoso-gitops:latest bash
```

To access Ansible, source the activation file to load the Python virtual environment:

```Bash
# source .ansible/bin/activate
```

The current repository is copied into the container, and is available in
/root/rhoso-gitops.

Alternatively, you can bind-mount the repository from your workstation for testing purposes:

```Bash
$ podman run --rm -ti \
    -v $HOME/.kube:/root/.kube \
    -v /path/to/local/rhoso-gitops:/root/rhoso-gitops \
    --security-opt label=disable \
    rhoso-gitops:latest bash
```

## Updating `oc` binary

To update `oc` binary, you can download the wanted version from your OpenShift cluster,
then bind-mount it in the container:

```Bash
$ podman run --rm -ti \
    -v $HOME/.kube:/root/.kube \
    -v /path/to/local/oc:/usr/bin/oc \
    --security-opt label=disable \
    rhoso-gitops:latest bash
```

## Getting `helm` in the container

Download [helm](https://github.com/helm/helm/releases) binary, follow the
[installation documentation](https://helm.sh/docs/intro/install/) and bind-mount it in the
container:

```Bash
$ podman run --rm -ti \
    -v $HOME/.kube:/root/.kube \
    -v /path/to/local/helm:/usr/bin/helm \
    --security-opt label=disable \
    rhoso-gitops:latest bash
```
