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

* configure your networking environment and document the interfaces for
  configuration of NNCP
* deploy OpenShift GitOps to the environment from `orchestration/argocd`
* deploy `applications/openstack-common`
* copy and modify `overlays/stackops` into a new path and modify the
  openstack-nncp.yaml at the least
* deploy `overlays/stackops`

**NOTE**: The deployment of `stackops` will require modification of the files to match
the network configuration.

_Procedure_

* Deploy the OpenShift GitOps instance (will require executing the command twice):
    ```
    $ oc create -k orchestration/openshift-gitops/
    ```

* Deploy the required Operators for deploying an OpenStack environment using an Application:
  ```
  $ oc create -k applications/openstack-common/
  ```

* Deploy OpenStack:
  ```
  $ oc create -k overlays/stackops/
  ```

## Accessing the user interface for OpenShift GitOps

You can view progress and management of the Applications by looking up the host address with `oc`.

_Procedure_

* Look up the host address of the OpenShift GitOps user interface:
  ```
  $ oc get route/openshift-gitops-server -nopenshift-gitops -ojsonpath='{.spec.host}'
  ```
