# rhoso-gitops

An implementation of Red Hat GitOps (GitOps, ArgoCD) for managing the
deployment of Red Hat OpenStack Services for OpenShift (RHOSO).

## Repository Layout

* `applications/`
    * contains the base GitOps Operator (ArgoCD) Application manifests for
      ArgoCD to manage push-install from the hub cluster to the managed cluster
* `base/`
    * contains base deployment knowledge not (yet) contained in the validated
      architectures repository in support of OpenStack deployments with RHOSO
* `orchestration/`
    * contains the configuration to deploy for OpenShift GitOps (ArgoCD)
      for cluster-scoped management on both the hub cluster and managed cluster

## Deployment

Manifests are managed with _kustomize_ (https://kustomize.io/) and can be
applied directly with `oc apply -k <directory>`.

Expected order of operations is:

* configure your networking environment and document the interfaces for
  configuration of NNCP
* deploy OpenShift GitOps to the environment from `orchestration/openshift-gitops`
* deploy `applications/openstack-common`
* create your `environments` in a private repository for deployment (TODO: provide working example)
* deploy `environments/`

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
  $ oc create -k applications/stackops/
  ```

## Accessing the user interface for OpenShift GitOps

You can view progress and management of the Applications by looking up the host address with `oc`.

_Procedure_

* Look up the host address of the OpenShift GitOps user interface:
  ```
  $ oc get route/openshift-gitops-server -nopenshift-gitops -ojsonpath='{.spec.host}'
  ```
