# rhoso-gitops

Repository to demo installation of Red Hat OpenStack Services on OpenShift
(RHOSO) using OpenShift GitOps.

## Repository Layout

* `orchestration/`
    * contains the configuration for OpenShift GitOps (ArgoCD)
      for cluster-scoped management of the OpenStack installation
* `applications/`
    * contains the base Applications to get the OpenStack
      Operators running
* `overlays/`
    *  contains the OpenStack deployment application that is managed by the
       Operators

## Deployment

Manifests are managed with _kustomize_ (https://kustomize.io/) and can be
applied directly with `oc apply -k <directory>`.

Expected order of operations is:

* deploy OpenShift GitOps to the environment
* deploy `applications/openstack-common`
* deploy `overlays/stackops`

The deployment of `stackops` will require modification of the files to match
the network configuration.
