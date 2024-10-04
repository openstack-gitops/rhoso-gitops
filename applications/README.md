# OpenShift GitOps Applications

Contains Application manifests for OpenShift GitOps to deploy Operators in
support of a Red Hat OpenStack Services on OpenShift (RHOSO).

Environment deployment examples are available at
https://github.com/openstack-gitops/environments.

There are two bases you can use:

* **va-base**: for [Validated
  Architecture](https://github.com/openstack-k8s-operators/architecture) based
  deployments
* **base**: for standard deployments

Applications in _va-base_ will use the Validated Architectures base to deploy
OpenStack Operators from a custom catalog source using an upstream index image.

Applications in _base_ will attempt to deploy primarily from the Red Hat
Operators and Certified Operators catalog sources.
