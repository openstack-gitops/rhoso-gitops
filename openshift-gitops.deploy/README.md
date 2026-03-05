# GitOps Initialization

Ansible script for managing deployment of Red Hat OpenShift GitOps Operator on
OpenShift.

## Getting started

Intent is for this code to be as self-contained as possible, avoiding reliance
on locally installed artifacts outside of the virtual environment. There may be
some exceptions.

_Prerequisites_

* You have Python 3 available on the workstation.
* You have [installed Kustomize](https://kubectl.docs.kubernetes.io/installation/kustomize/binaries/)

_Procedure_

* Create a local virtualenv to host the Ansible installation and collections required for use.
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install -r requirements.txt
    ```
* Login to your OpenShift cluster as an administrative user.
* Run the `./deployment.playbook` script which will deploy Red Hat OpenShift
  GitOps Operator and enable ArgoCD.

### Alternative initialization

You can deploy manually as well with Kustomize directly. There are two stages which need to be done sequentially:

* Deploy the Operator
  ```
  oc apply -k subscribe/
  ```
* Deploy ArgoCD
  ```
  oc apply -k enable/
  ```

### Review contents of manifests

Output the contents to standard out without applying them to the cluster:

* `kustomize build subscribe/`
* `kustomize build enable/`
