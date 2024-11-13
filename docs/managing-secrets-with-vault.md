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

### Prerequisites

* You're logged into the OpenShift Container Platform as a cluster adminstrator.
* Your OCP has persistent volumes in some way.
* You've installed `helm` version 3.15 or later.

### Procedure

_Add the Hashicorp Helm repository_
```bash
$ helm repo add hashicorp https://helm.releases.hashicorp.com
```

_Update all repositories_
```bash
$ helm repo update
```

#### Prepare TLS data

_A few preliminary notes_
    * In the example bellow, the OCP domain is `ocp.openstack.lab`. You might need to update that value for your own environment.
    * You can also consume a certificate signed by any other CA. Be sure you set the correct alt_names and CN if you want to use
      any existing CA.

_Create a custom Certificate Authority_
```bash
$ mkdir ~/vault-cert
$ cd ~/vault-cert
$ openssl genrsa -out ca.key 4096
$ openssl req -x509 -new -nodes -key ca.key -sha256 -days 1024 -out ca.crt
```

_Create a certificate configuration `vault-csr.conf` (set `CN` accordingly)_
```
[req]
default_bits = 4096
prompt = no
encrypt_key = yes
default_md = sha256
distinguished_name = kubelet_serving
req_extensions = v3_req
[kubelet_serving]
O = system:nodes
CN = system:node:*.vault.svc.ocp.openstack.lab
```

_Create an openssl extention file `vault.ext` (set `DNS.2` accordingly)_
```
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = *.vault-internal
DNS.2 = *.vault-internal.vault.svc.ocp.openstack.lab
DNS.3 = *.vault
IP.1 = 127.0.0.1
```

_Create the vault private key, get a CSR and signed certificate_
```bash
$ openssl genrsa -out vault.key 4096
$ openssl req -new -key vault.key -out vault.csr -config vault-csr.conf
$ openssl x509 -req -in vault.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out vault.crt -days 365 -sha256 -extfile vault.ext
```

_Expose TLS content in OpenShift_
We now have to let Vault know about the certificate and, if wanted, HA/replicas.
    * Create a project for Vault:
      ```bash
      $ oc new-project vault
      ```
    * Create the secret
      ```bash
      $ oc -n vault create secret generic vault-ha-tls \
            --from-file=vault.key=~/vault-cert/vault.key \
            --from-file=vault.crt=~/vault-cert/vault.crt \
            --from-file=vault.ca=~/vault-cert/ca.crt
      ```

##### Deploy Vault service

_Create vault deployment `overrides.yml`_
We'll instruct Vault to get 3 replicas, and use our TLS chain to encrypt all connections.

You can fetch [our overrides.yml](./overrides.yml) and use it as-is. Refer to
the [official documentation](https://developer.hashicorp.com/vault/docs/platform/k8s/helm/configuration)
for more information about the options and features.
  
_Install Hashicorp Vault_
  * Grant privileged access to the `vault` service:
    ```bash
    $ oc adm policy add-scc-to-user privileged -z vault -n vault
    ```
  * Deploy HashiCorp Vault with Helm, using the `overrides.yml` file:
    ```bash
    $ helm install vault hashicorp/vault --namespace=vault -f overrides.yml
    ```

##### Post installation tasks
We now have to initialize Vault, and aggregate the replicas.

You must wait for all pods to be running:
```bash
$ oc -n vault get pods
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          38s
vault-1                                 1/1     Running   0          37s
vault-2                                 1/1     Running   0          37s
vault-agent-injector-84dd9666df-xmwwb   1/1     Running   0          38s
```

_Initialize Vault_
Warning: this is a one-time action!
```bash
$ oc exec -n vault vault-0 -- vault operator init \
    -key-shares=1 \
    -key-threshold=1 \
    -format=json > ~/vault-cert/cluster-keys.json
```

Note: `cluster-keys.json` is to be stored securerly, since it contains access credentials
to Vault.

_Unseal Vault on vault-0_
```bash
$ export VAULT_UNSEAL_KEY=$(jq -r ".unseal_keys_b64[]" ~/vault-cert/cluster-keys.json)
$ oc exec -n vault vault-0 -- vault operator unseal $VAULT_UNSEAL_KEY
```

_Get vault-1 in_
```bash
$ cat << 'EOF' | oc exec -n vault -it vault-1 -- /bin/sh
vault operator raft join -address=https://vault-1.vault-internal:8200 -leader-ca-cert="$(cat /vault/userconfig/vault-ha-tls/vault.ca)" -leader-client-cert="$(cat /vault/userconfig/vault-ha-tls/vault.crt)" -leader-client-key="$(cat /vault/userconfig/vault-ha-tls/vault.key)" https://vault-0.vault-internal:8200
EOF
$ oc exec -n vault vault-1 -- vault operator unseal $VAULT_UNSEAL_KEY
```

_Get vault-2 in_
```bash
$ cat << 'EOF' | oc exec -n vault -it vault-2 -- /bin/sh
vault operator raft join -address=https://vault-2.vault-internal:8200 -leader-ca-cert="$(cat /vault/userconfig/vault-ha-tls/vault.ca)" -leader-client-cert="$(cat /vault/userconfig/vault-ha-tls/vault.crt)" -leader-client-key="$(cat /vault/userconfig/vault-ha-tls/vault.key)" https://vault-0.vault-internal:8200
EOF
$ oc exec -n vault vault-2 -- vault operator unseal $VAULT_UNSEAL_KEY
```

_Get Vault service status_
```bash
$ oc -n vault exec vault-0 -- vault status
Key                     Value
---                     -----
Seal Type               shamir
Initialized             true
Sealed                  false
Total Shares            1
Threshold               1
Version                 1.18.1
Build Date              2024-10-29T14:21:31Z
Storage Type            raft
Cluster Name            vault-integrated-storage
Cluster ID              16c48f5e-9c24-7f14-48e1-49b6a3d832b3
HA Enabled              true
HA Cluster              https://vault-0.vault-internal:8201
HA Mode                 active
Active Since            2024-11-13T09:45:25.636615131Z
Raft Committed Index    65
Raft Applied Index      65
```

_Ensure Vault is working_
You can try to authenticate against Vault, inject a secret, and fetch it from the CLI:
```bash
$ export CLUSTER_ROOT_TOKEN=$(jq -r ".root_token" ~/vault-cert/cluster-keys.json)
$ oc exec -n vault vault-0 -- vault login $CLUSTER_ROOT_TOKEN
$ oc exec -n vault vault-0 -- vault secrets enable -path=secret kv-v2
$ oc exec -n vault vault-0 -- vault put secret/tls/apitest username="apiuser" password="supersecret
$ oc exec -n vault vault-0 -- vault get secret/tls/apitest
```

If you want to check the HTTPS API right now, you'll need to expose the service, and use the custom CA
in cURL:

In a different terminal (or use `tmux`):
```bash
$ kubectl -n vault port-forward service/vault 8200:8200
```
Then in the terminal where you extracted `$CLUSTER_ROOT_TOKEN`:
```bash
$ curl --cacert ~/vault-cert/vault.ca \
        --header "X-Vault-Token: $CLUSTER_ROOT_TOKEN" \
        https://127.0.0.1:8200/v1/secret/data/tls/apitest | jq .data.data

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
  $ oc create --save-config -k base/vault-secrets-operator
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
