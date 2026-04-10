# CI, validation, and when in doubt

## Source of truth: GitHub workflows

The **GitHub Actions workflows** in `.github/workflows/` are the source of truth for required checks.

Agents must:

1. Inspect the relevant workflow files before making changes.
2. Derive the exact commands to run (including install steps, working directories, environment variables, and scripts) from those workflows, and mirror them locally when possible rather than inferring checks from memory or generic examples.
3. Treat any failure in those commands as a blocker and fix issues before opening a pull request.

Do **not** invent new validation commands unless explicitly requested. Prefer to align with the commands defined in existing workflows.

## Required checks before committing or opening a PR

Before creating a commit or a pull request, agents must:

1. Run all applicable validation steps used in CI for this repo:
   - Read the workflow files under `.github/workflows/` and determine which jobs and steps apply to the paths or areas you changed.
   - Extract and run the same commands those steps invoke (or an equivalent), matching tool versions or invocations where the workflow pins them.
2. Ensure that:
   - All tests pass.
   - All linters and formatters pass.
   - Generated content (if any) is up to date relative to the commands used in this repo (for example, `make generate` or equivalent, if present).

If a required tool is not available in the current environment, clearly note the missing tool and do not assume the checks passed.

## When in doubt

If an agent is unsure about:

- Which command to run for validation,
- How a particular directory is meant to be used,
- Whether a change might be breaking for downstream consumers,

Then it should:

1. Prefer a conservative, minimal change.
2. Add a short comment in the pull request description explaining the uncertainty and the assumptions made.
3. Leave a clear trail in the commit body describing any potentially breaking or controversial choice.

This helps human reviewers quickly understand what the agent did and why.
