# AGENTS

This document describes how AI agents should work with this repository. The goal is to keep changes safe, consistent, and aligned with our GitOps usage of this repo.

**Non-negotiables**

- This repository is a **component catalog** (reusable building blocks for OpenStack on Kubernetes), not a full cluster or environment layout.
- **CI workflows** in [`.github/workflows/`](.github/workflows/) are the source of truth for validation commands. Do not invent new checks; mirror what those workflows run.
- **Do not** open pull requests or push to the remote without an explicit human request. A human must review before any push or PR. See [CONTRIBUTING.md#ai-assistants-and-agent-tooling](CONTRIBUTING.md#ai-assistants-and-agent-tooling).
- **Conventional Commits**; add `AI-Tool` / `AI-Model` footers when an AI assistant contributed significantly. See [CONTRIBUTING.md](CONTRIBUTING.md).

**Read next (by task)**

- **Purpose, directories (`/charts`, `/components`, `/example`)** → [docs/agents/repository.md](docs/agents/repository.md)
- **YAML, Helm, Kustomize** → [docs/agents/yaml-helm-kustomize.md](docs/agents/yaml-helm-kustomize.md)
- **What CI runs, required checks, when in doubt** → [docs/agents/ci-and-validation.md](docs/agents/ci-and-validation.md)
- **Releases, tags, and `?ref=`** → [docs/agents/releases.md](docs/agents/releases.md)
- **Branches, PRs, commits, expectations for changes** → [CONTRIBUTING.md](CONTRIBUTING.md)

**Domain context (operators and consumers):** the root [README.md](README.md) documents RHOSO deployment, ArgoCD conventions (e.g. sync-waves, pinned `?ref=`), and how applications are sliced—it does not define repository editing policy. Use the links above for how to change this repository.