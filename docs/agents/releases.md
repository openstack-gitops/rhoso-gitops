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

Rules for agents:

- Do not leave `?ref=` values pointing to older tags or branches once a new release tag is intended to be the default example.
- Prefer pinned, explicit tags over branch names like `main`, `master`, or feature branches in all references to this repository.
- When introducing new examples or references that point to this repository, always use the **current** released tag, not a branch name.
- When checking `?ref=`, treat URLs that contain `openstack-k8s-operators/gitops` as references to this repository.

If the repository maintainers follow a specific naming scheme for tags (for example, `vMAJOR.MINOR.PATCH`), preserve that scheme and do not invent new formats.
