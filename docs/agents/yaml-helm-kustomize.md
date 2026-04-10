# YAML, Helm, and kustomize invariants

## 3.1 General YAML rules

For all YAML files in this repository:

- Files must be **valid YAML** and parse cleanly with standard tooling.
- Each YAML file must include a `---` document header before the first Kubernetes (or kustomize) object. Leading comment lines (for example source-documentation links or notes) may appear **above** that `---`; do not require `---` to be the very first line of the file.
- Prefer one Kubernetes object per file unless an existing pattern in that directory clearly uses multi‑document files.
- Do not embed inline JSON; use proper YAML mappings and sequences.

Consistency matters: when editing existing YAML, follow the surrounding style (indentation, quoting, key ordering) unless you are explicitly cleaning it up repo‑wide.

## 3.2 Kubernetes and GitOps assumptions

- Manifests must be compatible with standard Kubernetes APIs and controllers used by the OpenStack Kubernetes Operators.
- Avoid using `latest` image tags or unpinned versions; prefer pinned tags or digests consistent with existing patterns in this repo.
- Do not introduce cluster‑specific data (hostnames, IPs, secrets) into this repo. Keep it generic and parameterized so consuming GitOps repos can provide environment‑specific values.

## 3.3 Helm charts (`/charts`)

When modifying or adding charts:

- Keep `Chart.yaml` and `values.yaml` well documented and minimal.
- Validate charts using the commands defined in the GitHub Actions workflows for this repository (see those workflows for the exact `helm` or other invocations).
- Avoid breaking changes to values unless strictly necessary; if unavoidable, document the change in chart docs and in commit messages.

## 3.4 Kustomize components (`/components`, `/example`)

- Components should be **composable** and reusable across environments.
- Use kustomize conventions consistently (e.g., `kustomization.yaml` naming, `resources` vs `components` vs `patches`).
- Ensure that overlays or examples under `/example` still build successfully after changes.
