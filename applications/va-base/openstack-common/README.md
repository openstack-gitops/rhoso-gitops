# openstack-common Application

Deploy the common OpenStack components in order to deploy the OpenStack Operators.

**NOTE:** Installation will be done via the [Validated
Architecture](https://github.com/openstack-k8s-operators/architecture)
repository, which installs the upstream OpenStack Operator CatalogSource and
Subscription by default. If you are looking to install from the Red Hat
Operators CatalogSource instead (production build of OpenStack Operators) then
see [base/prerequisites](base/prerequisites)

_Procedure_

* Create the _openstack-common_ Application in OpenShift GitOps:
  ```
  $ oc create -f .
  ```
