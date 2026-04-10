# Contributing

This document describes how to contribute to this repository. It applies to human contributors and to AI assistants or agent tooling; some sections are written specifically for automated assistants.

## Branching and pull request rules

When contributing changes:

- Perform changes on a **dedicated branch** per logical change set.
- The branch used for a pull request must be **up to date with `main`**:
  - If `main` has advanced, rebase before considering the PR ready.
- Group related changes into one PR; avoid mixing unrelated refactors, new features, and fixes.

For large or risky changes, prefer smaller, incremental PRs that are easier to review and roll back.

## Commit message conventions and AI attribution

We use **Conventional Commits** for all commits in this repository.

### Conventional commit format

Commit messages must follow:

- `type(scope): short description`

Where:

- `type` is one of the standard types used in this organization (for example: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`).
- `scope` is optional but recommended, and should reflect the affected area (for example: `charts`, `components`, `example`, or a more specific identifier).
- The short description is concise, in lowercase, and completes the sentence: “This commit will …”.

Use commit bodies to explain **why** the change was made and any important context or trade‑offs.

Breaking changes must be clearly indicated according to the Conventional Commits specification.

### AI tool and model footer

For any commit where an AI assistant or agent contributed significantly to the change (code, YAML, templates, or docs), add a footer to the commit message indicating the AI tool and model used.

Use a **git trailer‑style footer**. For example:

- `AI-Tool: <tool name>`
- `AI-Model: <model name and version>`

Examples of valid footer tokens:

- `AI-Tool: Claude Workbench`
- `AI-Model: Claude 3.7 Sonnet (2025-08-15)`

If multiple tools or models were used, you may list multiple `AI-Tool` and `AI-Model` lines.

When preparing commit messages, agents must:

- Ensure the main line and any body follow Conventional Commits rules.
- Add the AI attribution footers when relevant.
- Keep the final message consistent and readable for human reviewers.

## AI assistants and agent tooling

AI agents must **not** create pull requests on their own initiative.

Workflow requirements:

- Agents may:
  - Propose changes.
  - Modify files in a local working tree or a feature branch.
  - Prepare candidate commit messages and PR descriptions as text.
- Agents must **not**:
  - Open pull requests in this repository without an explicit human request.
  - Push branches to the remote without an explicit human request.

Human control and review:

- All changes produced by agents must be reviewed by a human contributor before:
  - commits are pushed
  - a pull request is opened

Agents should treat “create PR” as an action that always requires an explicit human instruction (for example, a user explicitly confirming that the changes are ready to be proposed).

## Expectations for AI-generated changes

When making changes, AI agents must:

- Preserve existing behavior unless the change is explicitly intended to alter it.
- Prefer minimal diffs that address the requested change without broad refactors.
- Keep component and chart names, labels, and annotations consistent with existing patterns in this repo.
- Avoid introducing organization‑specific secrets, credentials, or sensitive data into the repository.

Whenever there is ambiguity about the correct pattern (for example, multiple existing styles in the same directory), agents should align with the most recent and most widely used pattern in that area of the repo.
