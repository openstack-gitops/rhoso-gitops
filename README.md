# rhoso-gitops

An implementation of Red Hat GitOps (GitOps, ArgoCD) for managing the
deployment of Red Hat OpenStack Services on OpenShift (RHOSO).

**WARNING**: _Contents of this repository are a work in progress and not yet
ready for usage in a production environment. The organization or contents of
this repository may change drastically at any time._

## Repository Layout

* `applications/`
    * contains the base GitOps Operator (ArgoCD) Application manifests for
      ArgoCD to manage push-install from the hub cluster to the managed cluster
* `base/`
    * contains base deployment knowledge not (yet) contained in the validated
      architectures repository in support of OpenStack deployments with RHOSO
* `orchestration/` (deprecated)
    * contains the configuration to deploy for OpenShift GitOps (ArgoCD)
      for cluster-scoped management on both the hub cluster and managed cluster

## Deployment

Manifests are managed with _kustomize_ (https://kustomize.io/) and can be
applied directly with `oc apply -k <directory>`.

Expected order of operations is:

* (optional) Deploy Red Hat Advanced Cluster Manager (RHACM) and configure it
  so deployment of OpenShift clusters is possible (the hub cluster).
* Deploy ArgoCD to the hub cluster or unmanaged cluster.
  * Use the `base/initialize/gitops/` directory to deploy Red Hat OpenShift
    GitOps and the initial ArgoCD deployment.
* Create the base Applications from `applications/` to the hub or unmanaged cluster.
* Create your [environments](https://github.com/openstack-gitops/environments)
  in a private repository for deployment.
* Deploy `environments/`.

### Bootstrap Red Hat GitOps

You must first install Red Hat GitOps (GitOps) to provide the automation system
for deploying RHOSO. Installation of GitOps can be done on a hub cluster or an
unmanaged cluster. If installed on the hub cluster, you can use a GitOps
Application to deploy GitOps on the managed cluster. If you are not using a hub
cluster, then installation of GitOps on the unmanaged cluster must done first.

_Prerequisites_

* You have installed Ansible on the workstation.
* You have installed the Ansible collection `kubernetes.core.k8s`.
* You have installed Kustomize on the workstation.
* You have logged into the OpenShift cluster as the kubeadmin user you want GitOps to be deployed to.

_Procedure_

Use the `deployment.playbook` script to automate the installation of Red Hat GitOps with Ansible and Kustomize.

* Login to the OpenShift cluster as the kubeadmin user from the workstation.
* Install the Red Hat GitOps Operator and deploy an ArgoCD instance with the `deployment.playbook` script:
  ```
  $ ./base/initialize/gitops/deployment.playbook
  ```
Alternatively, deploy Red Hat GitOps and ArgoCD with Kustomize directly in stages.

* Login to the OpenShift cluster as the kubeadmin user from the workstation.
* Install the Red Hat GitOps Operator:
  ```
  $ oc create --save-config -k base/initialize/gitops/subscribe
  ```
* Validate the Subscription has been completed. The subscription status should return:
  ```
  $ oc get subscription.operators.coreos.com/openshift-gitops-operator \
      --namespace openshift-gitops-operator -ojsonpath='{.status.state}'
  ```
* When the value returned is `AtLastKnown`, then continue by deploying and ArgoCD instance.

* Create the ArgoCD instance:
  ```
  $ oc create --save-config -k base/initialize/gitops/enable
  ```

### Set up Red Hat Advanced Cluster Management for GitOps

When using Red Hat Advanced Cluster Management (RHACM) to support GitOps
Applications for managed clusters, we will configure the hub cluster in
preparation for using GitOps to support managed cluster configuration.

If you are using GitOps on an unmanaged cluster without RHACM, then this will
be unnecessary.

_Prerequisites_

* You have installed and setup RHACM (hub cluster) for your hardware
  environment that will host the managed OpenShift deployment.
* You are logged into the hub cluster as the kubeadmin user.
* You have installed Red Hat GitOps.

_Procedure_

* Setup RHACM for RHOSO cluster deployments and placements with GitOps:
  ```
  oc apply -k base/cluster/hub/advanced-cluster-managment/
  ```
* Add your cluster and place it in the `rhoso` ClusterSet

## Accessing the user interface for OpenShift GitOps

You can view progress and management of the Applications by looking up the host
address with `oc`.

_Procedure_

* Look up the host address of the OpenShift GitOps user interface:
  ```
  $ oc get route/openshift-gitops-server -nopenshift-gitops -ojsonpath='{.spec.host}'
  ```

## Deploy Prerequisites

Deploy the prerequisites for deployment of a RHOSO environment by creating the
`openstack-prerequisites` GitOps Application.

_Procedure_

* Create the `openstack-prerequisites` GitOps Application:
```
$ oc create --save-config -k applications/base/prerequisites
```
