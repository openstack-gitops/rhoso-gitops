# Using containerized client interfaces

Provides a containerized environment to run client commands, including `oc` and `ansible`.

## Creating the container image

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

If you want to access ansible, you can then run:

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
