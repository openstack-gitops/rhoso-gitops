# External Secrets Operator

Subscribe to External Secrets Operator on OpenShift via Operator Lifecycle Manager (OLM).

## Layout

- **`community/`** — default install: a single `Subscription` in `openshift-operators` from the **community-operators** catalog (`spec.channel: stable`). This is split into a `community` kustomization so the **`redhat/`** overlay can include it without tripping kustomize path or cycle restrictions (you cannot reference a parent directory that contains the overlay, or files outside the overlay path, from `redhat/`).
- **`redhat/`** — overlay that includes `community`, adds Namespace `external-secrets-operator` and an `OperatorGroup`, and applies a **JSON6902** patch to the community `Subscription` so it targets the Red Hat catalog (`openshift-external-secrets-operator`, `redhat-operators`, `stable-v1`), including `metadata.name` / `metadata.namespace` and stripping `metadata.labels`. Strategic merge does not reliably change Subscription identity fields; use RFC6902 for those edits.

## Choose one catalog

Do **not** install both the community OperatorHub package and the Red Hat External Secrets Operator on the same cluster. If you switch from one to the other, uninstall the existing operator first (see [Red Hat documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/security_and_compliance/external-secrets-operator-for-red-hat-openshift)).

## Apply

**Community (default):**

```shell
oc apply -k resources/external-secrets-operator
```

**Red Hat** (requires OpenShift 4.20+ and the `redhat-operators` catalog):

```shell
oc apply -k resources/external-secrets-operator/redhat
```

## Argo CD

Point `spec.source.path` at:

- `resources/external-secrets-operator` for the default (community) manifest, or
- `resources/external-secrets-operator/redhat` for the Red Hat operator.

You can mirror [applications/vault-secrets-operator.yaml](https://github.com/openstack-k8s-operators/gitops/blob/main/applications/vault-secrets-operator.yaml) (sync-wave, repo URL, kustomize components) and set `path` accordingly.

## Links

- [External Secrets Operator for Red Hat OpenShift](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/security_and_compliance/external-secrets-operator-for-red-hat-openshift) (Red Hat)
- [external-secrets.io](https://external-secrets.io/) (upstream)
