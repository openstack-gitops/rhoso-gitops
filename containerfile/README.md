# Container image

Provides a quick'n'easy environment from where you can run the various
`oc` commands, but also the needed `ansible` related steps as described
in this repository.

## Create the container image

Using buildah or podman, run the following commande from the root of
the repository:

```Bash
$ buildah bud -t rhoso-gitops:latest -f containerfile/oc-client .
$ podman build -t rhoso-gitops:latest -f containerfile/oc-client .
```

## Using the container image

Run the following command:

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

This will load the python virtualenv, exposing the needed libs and
binaries.

The current repository is copied in the container, and is available in
/root/rhoso-gitops directly.

You can, of course, bind-mount it from your workstation if you have anything
to test:

```Bash
$ podman run --rm -ti \
    -v $HOME/.kube:/root/.kube \
    -v /path/to/local/rhoso-gitops:/root/rhoso-gitops \
    --security-opt label=disable \
    rhoso-gitops:latest bash

```