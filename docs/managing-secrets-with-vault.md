# Managing Secrets With Vault

When [Providing secure access to Red Hat OpenStack Services on OpenShift
services](https://docs.redhat.com/en/documentation/red_hat_openstack_services_on_openshift/18.0/html/deploying_red_hat_openstack_services_on_openshift/assembly_preparing-rhocp-for-rhoso#proc_providing-secure-access-to-the-RHOSO-services_preparing)
it's necessary to populate a `Secret` with contents used for authentication.

Manging `Secret` contents when using GitOps requires extra considerations, as
the sensitive data that exists in the Secret itself cannot be commited to a git
repository.

Use of HashiCorp Vault allows for storage of the sensitive contents separate of
the creation of the Secret objects required for OpenStack provisioning. Use of
the Vault Secrets Operator makes taking the sensitive data stored in Vault and
writes it to a Kubernetes native Secret.

## Deploying Vault

Deployment of Vault is done with Helm, and then configuration of Vault itself
is done within the `vault-0` pod with the `vault` CLI command. The deployment
shown is not a production capable deployment of Vault. For more information
about deploying Vault on Kubernetes for production, see [Vault on Kubernetes
deployment
guide](https://developer.hashicorp.com/vault/tutorials/kubernetes/kubernetes-raft-deployment-guide).

_Prerequisites_

* You're logged into the OpenShift Container Platform as a cluster adminstrator.
* You've installed `helm` version 3.15 or later.

_Procedure_

* Add the Hashicorp Helm repository:
  ```bash
  $ helm repo add hashicorp https://helm.releases.hashicorp.com
  ```
* Update all repositories:
  ```bash
  $ helm repo update
  ```
* Install Hashicorp Vault:
  * Create a project for Vault:
    ```bash
    $ oc new-project vault
    ```
  * Grant privileged access to the `vault` service:
    ```bash
    $ oc adm policy add-scc-to-user privileged -z vault -n vault
    ```
  * Deploy HashiCorp Vault with Helm:
    ```bash
    $ helm install vault hashicorp/vault --namespace=vault \
      --set "server.dev.enabled=true" \
      --set "injector.enabled=false" \
      --set "global.openshift=true"
    ```

_Additional Information_

* [Vault installation to Red Hat OpenShift via Helm](https://developer.hashicorp.com/vault/tutorials/kubernetes/kubernetes-openshift).
* [Mounting secrets from HashiCorp Vault](https://docs.openshift.com/container-platform/4.16/nodes/pods/nodes-pods-secrets-store.html#secrets-store-vault_nodes-pods-secrets-store) in the OpenShift Providing sensitive data to pods by using an external secrets store guide.

## Enabling Vault Access

Configure Vault to use Kubernetes authentication and a policy for OpenStack usage.

### Configuring Vault to use Kubernetes Authentication

These instructions match those documented at [Mounting secrets from HashiCorp
Vault](https://docs.openshift.com/container-platform/4.16/nodes/pods/nodes-pods-secrets-store.html#secrets-store-vault_nodes-pods-secrets-store)
in the OpenShift guide at procedure step 5 with minor modifications to enable
Vault specifically for the `openstack` namespace.

_Procedure_

* Enable the Kubernetes authentication method:
  ```bash
  $ oc exec vault-0 --namespace=vault -- vault auth enable kubernetes
  ```
* Configure the Kubernetes authentication method:
  * Set the token reviewer as an environment variable by running the following command:
    ```bash
    $ TOKEN_REVIEWER_JWT="$(oc exec vault-0 --namespace=vault -- cat /var/run/secrets/kubernetes.io/serviceaccount/token)"
    ```
  * Set the Kubernetes service IP address as an environment variable by running the following command:
    ```bash
    $ KUBERNETES_SERVICE_IP="$(oc get svc --namespace=default kubernetes -o go-template="{{ .spec.clusterIP }}")"
    ```
  * Update the Kubernetes auth method by running the following command:
    ```bash
    $ oc exec -i vault-0 --namespace=vault -- vault write auth/kubernetes/config \
    issuer="https://kubernetes.default.svc.cluster.local" \
    token_reviewer_jwt="${TOKEN_REVIEWER_JWT}" \
    kubernetes_host="https://${KUBERNETES_SERVICE_IP}:443" \
    kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    ```
* Create a policy for OpenStack:
  ```bash
  $ oc exec -i vault-0 --namespace=vault -- vault policy write openstack - <<EOF
  path "secret/data/openstack/*" {
  capabilities = ["read"]
  }
  EOF
  ```
* Create an authentication role for OpenStack:
  ```bash
  $ oc exec -i vault-0 --namespace=vault -- vault write auth/kubernetes/role/openstack bound_service_account_names=default bound_service_account_namespaces=default,openstack policies=openstack ttl=20m
  ```

## Deploying Vault Secrets Operator

Deploy the Vault Secrets Operator from the Operator Lifecycle Manager (OLM).

_Procedure_

* Subscribe to the Vault Secrets Operator:
  ```bash
  $ oc create --save-config -k https://github.com/openstack-gitops/rhoso-gitops/base/cluster/common/vault-secrets-operator
  ```

_Additional Information_

* [The Vault Secrets Operator on Kubernetes](https://developer.hashicorp.com/vault/tutorials/kubernetes/vault-secrets-operator).

## Populate Vault

Creating Secret objects in the `openstack` namespace is done by storing the
sensitive information in Vault, and then using the Vault Secrets Operator to
access the data using the Vault API and then creating a populated Secret for
use by the Red Hat OpenStack Services on OpenShift Operators.

Importing the data securely and more efficiently is out of scope for this
documentation. For more information about working with the `vault` command, see
[Your first
secret](https://developer.hashicorp.com/vault/tutorials/getting-started/getting-started-first-secret)
in the Hashicorp tutorial guide.

_Procedure_
* Create the initial `openstack/osp-secret` key-value data in Vault:
  ```bash
  $ oc exec -i vault-0 --namespace=vault -- vault kv put secret/openstack/osp-secret AdminPassword="$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 32)"
  ```

* Patch `openstack/osp-secret` with the rest of the data required for the Secret osp-secret:

  **WARNING**: Be sure to provide the full list of keys, and create a fernet key for `BarbicanSimpleCryptoKEK`.
  ```bash
  $ for key in AodhPassword AodhDatabasePassword BarbicanDatabasePassword
    do
      oc exec -i vault-0 --namespace=vault -- vault kv patch -mount=secret openstack/osp-secret $key="$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 32)"
    done
  ```

## Creating the Secret

Use the Vault Secrets Operator to create the Secret osp-secret from the data stored in Vault.

_Procedure_

* Login to the OpenShift environment as a cluster-admin.
* Create the Vault connection:
  ```yaml
  $ oc create --save-config -f - <<EOF
  apiVersion: secrets.hashicorp.com/v1beta1
  kind: VaultConnection
  metadata:
    name: openstack-vault-connection
    namespace: openstack
  spec:
    address: http://vault.vault.svc.cluster.local:8200
  EOF
  ```
* Create the Vault authentication:
  ```yaml
  $ oc create --save-config -f - <<EOF
  apiVersion: secrets.hashicorp.com/v1beta1
  kind: VaultAuth
  metadata:
    name: openstack-vault-auth
    namespace: openstack
  spec:
    kubernetes:
      role: openstack
      serviceAccount: default
      tokenExpirationSeconds: 600
    method: kubernetes
    mount: kubernetes
    vaultConnectionRef: openstack-vault-connection
  EOF
  ```
* Create the Vault static secret:
  ```yaml
  $ oc create --save-config -f - <<EOF
  apiVersion: secrets.hashicorp.com/v1beta1
  kind: VaultStaticSecret
  metadata:
    name: openstack-osp-secret
    namespace: openstack
  spec:
    destination:
      create: true
      name: osp-secret
      overwrite: false
      transformation: {}
    hmacSecretData: true
    mount: secret
    path: openstack/osp-secret
    refreshAfter: 30s
    type: kv-v2
    vaultAuthRef: openstack-vault-auth
  EOF
  ```
* Validate the Secret osp-secret was created and populated:
  ```bash
  $ oc get secret/osp-secret -oyaml
  ```
