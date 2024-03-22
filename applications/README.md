= OpenStack Common Application

Contains the Application for OpenShift GitOps to get the common OpenStack
components installed (Operators) in preparation for network configuration and
deployment of an OpenStack control plane.

== Deploying

_Prerequisites_

* Deployment of OpenShift
* Deployment of OpenShift GitOps
* Local installation of kustomize

_Procedure_

* Deploy the `openstack-common` application with kustomize
```
oc apply -k .
```
