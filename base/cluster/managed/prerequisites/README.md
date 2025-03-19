# Prerequisites

Contains the prerequisite Operators that need to be installed on the OpenShift
cluster prior to install of OpenStack Operator.

Provides the prerequisite Operators as documented at
[Prerequisites](https://docs.redhat.com/en/documentation/red_hat_openstack_services_on_openshift/18.0/html/deploying_red_hat_openstack_services_on_openshift/assembly_installing-and-preparing-the-operators#prerequisites)
in the _Red Hat OpenStack on OpenShift Deployment guide_.

Also creates the `openstack` namespace for deployment of objects related to
RHOSO.

The following Operators will be installed and enabled:

- NMstate Operator
- MetalLB Operator
- Certificate Manager Operator
- Cluster Observability Operator
