# Release process and tag management

This repository uses Git tags to version the catalog. To keep consumers pinned to explicit versions, every time a new tag is created, the tag must be propagated to all relevant references.

When preparing or finalizing a release:

1. After creating a new tag (for example `vX.Y.Z`), perform a follow-up commit that updates all version references to use the new tag.
2. Search the **entire repository** for occurrences of `?ref=` that point to content provided by this repository (for example raw GitHub URLs or module references into `openstack-k8s-operators/gitops`).
3. Update all such references to use the new tag instead of the previous value, **even if the previous value was a branch name** (for example, a feature branch used to make CI pass).

In particular, verify and update any `?ref=` or similar version selectors in:

- `/example` (all example manifests and configuration files)
- `/charts` (chart values, templates, or helper files that reference this repo)
- Any `README.md` or other documentation files in this repo

**Helm chart version management:**

When bumping to a new release tag, also update the Helm chart metadata and values:

1. **Chart version** in `/charts/rhoso-apps/Chart.yaml`:
   - Update the `version` field to match the new tag (e.g., `vX.Y.Z` → `version: X.Y.Z` without the `v` prefix)

2. **Application targetRevisions** in `/charts/rhoso-apps/values.yaml`:
   - Update all `targetRevision` fields under `applications.*` to the new tag (e.g., `targetRevision: vX.Y.Z`)
   - These are NOT `?ref=` patterns but still need updating to match the release

3. **Test expectations** in `/charts/rhoso-apps/tests/application_test.yaml`:
   - Update any assertions that check `spec.source.targetRevision` values
   - Search for the old version string and replace with the new one to prevent test failures

Rules for agents:

- Do not leave `?ref=` values pointing to older tags or branches once a new release tag is intended to be the default example.
- Prefer pinned, explicit tags over branch names like `main`, `master`, or feature branches in all references to this repository.
- When introducing new examples or references that point to this repository, always use the **current** released tag, not a branch name.
- When checking `?ref=`, treat URLs that contain `openstack-k8s-operators/gitops` as references to this repository.
- **For Helm chart releases**: Update Chart.yaml version, all values.yaml targetRevision fields, AND test assertions in the same commit batch.
- **Validation**: After bumping versions, verify that tests still pass by checking what CI runs (see [ci-and-validation.md](ci-and-validation.md)).

If the repository maintainers follow a specific naming scheme for tags (for example, `vMAJOR.MINOR.PATCH`), preserve that scheme and do not invent new formats.

**Complete checklist for version bumps:**

1. Search and replace `?ref=vOLD` → `?ref=vNEW` in:
   - `applications/*.yaml` (component references)
   - `example/*/kustomization.yaml` (component references)
   - `example/*/README.md` (documentation examples)
   - `components/*/README.md` (usage examples)
   - `charts/*/README.md` (documentation examples)

2. Update Helm chart files:
   - `charts/rhoso-apps/Chart.yaml`: `version` field
   - `charts/rhoso-apps/values.yaml`: all `targetRevision` fields
   - `charts/rhoso-apps/tests/application_test.yaml`: assertion values

3. Verify no references were missed:
   ```bash
   # Should return no results if all same-repo refs are updated
   grep -r "ref=vOLD" --include="*.yaml" --include="*.yml" --include="*.md" . | grep "openstack-k8s-operators/gitops"
   ```
