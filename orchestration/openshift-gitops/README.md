# OpenShift GitOps Bootstrap

You can bootstrap an OpenShift GitOps instance in preparation for deployment of
OpenStack with the contents of this repository. Deployment is managed with
kustomize. A ClusterRole is created and used by the openshift-gitops controller
to provide API access to various CustomResources for deployment of OpenStack.

## Deployment of OpenShift GitOps

Subscribing to the OpenShift GitOps Operator will provide a default ArgoCD
instance in the `openshift-gitops` namespace, and operates at the cluster-scope
for managed of resources for an OpenStack deployment.

_Procedure_

* Modify the contents of `gitrepo.env` to set the value of the `url` parameter
  to the internal git repo hosting your environment specific configuration

* Create an OpenShift GitOps deployment: ``` $ oc create -k . ```

**NOTE** It will likely be necessary to run the command twice as the
Subscription will not be ready prior to modification of the ArgoCD resource,
which is created automatically if you're deploying this manually.
