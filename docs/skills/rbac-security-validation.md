# RBAC Security Validation

This skill helps contributors identify and fix dangerous RBAC wildcard patterns that violate the repository's security policy.

## Purpose

Validates RBAC manifests (ClusterRole and Role) to prevent dangerous wildcard permissions from being merged. This protects against privilege escalation vulnerabilities (CVSS 9.1 HIGH severity) where wildcard RBAC can enable cluster-admin equivalent access.

## When to Use

Use this skill when:

- Adding or modifying ClusterRole or Role manifests
- CI fails with "RBAC security violations detected"
- Reviewing RBAC changes in pull requests
- Uncertain whether specific RBAC permissions are safe

## Prerequisites

- Python 3 with PyYAML installed (`pip install pyyaml`)
- Understanding of Kubernetes RBAC verbs and resources

## Running the Validation

### Local Validation

Before committing RBAC changes, run:

```bash
python3 .github/scripts/check-rbac-wildcards.py
```

**Expected output if passing:**
```
✅ RBAC validation passed
```

**Expected output if failing:**
```
❌ RBAC Security Validation FAILED
Critical Violations Found: ...
```

### CI Integration

The validation runs automatically in `.github/workflows/yamllint.yml` as the `rbac-security-check` job. It executes on every pull request that modifies YAML files.

## What Gets Validated

### Critical Violations (Fail CI)

These patterns are **never allowed**:

#### 1. Wildcard verbs on core API resources

**Blocked pattern:**
```yaml
- apiGroups: [""]
  resources:
    - secrets        # ❌ CRITICAL
    - pods           # ❌ CRITICAL
    - persistentvolumeclaims
    - serviceaccounts
    - nodes
    - namespaces
  verbs:
    - '*'            # ❌ Grants dangerous implicit permissions
```

**Why dangerous:** Wildcard verbs include `impersonate`, `escalate`, and `bind` - privilege escalation primitives that enable cluster-admin access.

#### 2. Wildcard resources in any API group

**Blocked pattern:**
```yaml
- apiGroups:
    - metal3.io
    - lvm.topolvm.io
    - multicluster.openshift.io
    - rbac.authorization.k8s.io  # ❌ Especially dangerous
  resources:
    - '*'            # ❌ CRITICAL - grants access to ALL resources
  verbs:
    - get
    - list
```

**Why dangerous:** Prevents least-privilege enforcement and grants access to future resources that may be sensitive.

### Warnings (Report Only)

#### Wildcard verbs on OpenStack CRDs

**Warned pattern:**
```yaml
- apiGroups:
    - core.openstack.org
    - dataplane.openstack.org
    - operator.openstack.org
  resources:
    - openstackcontrolplanes
  verbs:
    - '*'            # ⚠️ WARNING - consider making explicit
```

**Why a warning:** OpenStack CRDs don't provide cluster-admin escalation paths, but explicit verbs are still preferred.

## How to Fix Violations

### Fixing Wildcard Verbs on Core API

**Before (❌ fails CI):**
```yaml
- apiGroups:
    - ""
  resources:
    - secrets
    - pods
  verbs:
    - '*'
```

**After (✅ passes CI):**
```yaml
# Secrets - if you need full CRUD
- apiGroups:
    - ""
  resources:
    - secrets
  verbs:
    - get
    - list
    - watch
    - create
    - patch
    - delete

# Pods - read-only if you only need status checking
- apiGroups:
    - ""
  resources:
    - pods
  verbs:
    - get
    - list
    - watch
```

**Decision matrix for verbs:**
- Need to read? → `[get, list, watch]`
- Need to create/update? → Add `[create, patch]` or `[create, update, patch]`
- Need to delete? → Add `[delete]`
- **Never use:** `['*']`, `impersonate`, `escalate`, `bind`

### Fixing Wildcard Resources

**Before (❌ fails CI):**
```yaml
- apiGroups:
    - metal3.io
  resources:
    - '*'          # Grants access to ALL metal3.io resources
  verbs:
    - get
    - create
```

**After (✅ passes CI):**
```yaml
- apiGroups:
    - metal3.io
  resources:
    - baremetalhosts      # Only what you actually use
    - provisionings
  verbs:
    - get
    - list
    - watch
    - create
    - update
    - patch
    - delete
```

**How to find the right resources:**

1. Look at what resources you actually create in your manifests
2. Check the API documentation for the operator you're using
3. Scan the repository:
   ```bash
   # Find all kinds referencing metal3.io
   grep -r "apiVersion.*metal3.io" . | grep "kind:" | sort -u
   ```

## Troubleshooting

### "CI Failed: RBAC security violations detected"

1. Read the CI output - it shows the exact file, line, and permission that's problematic
2. Follow the "How to Fix Violations" section above
3. Test locally with `python3 .github/scripts/check-rbac-wildcards.py`
4. Commit the fix and push

### "False positive - I need this wildcard"

If you believe the validator incorrectly flagged a legitimate use case:

1. **Double-check:** Are you sure you need the wildcard? Can explicit permissions work?
2. **Document:** Add a comment in the YAML explaining why the wildcard is necessary
3. **Open an issue:** Request an allowlist exception with full justification
4. **Temporary override:** Requires maintainer approval and should be rare

### Script Errors

If the validation script crashes or produces unexpected output:

1. Check that your YAML is valid: `yamllint -c .yamllint.yml <file>`
2. Ensure the file has `kind: ClusterRole` or `kind: Role`
3. Report the issue at https://github.com/openstack-k8s-operators/gitops/issues

## Exceptions and Allowlisting

Currently, there is no allowlist mechanism. If you have a legitimate use case for wildcard permissions:

1. Open an issue explaining:
   - What resource/verb needs the wildcard
   - Why explicit permissions cannot work
   - What security controls mitigate the risk

2. The security team will review and may implement an allowlist file (`.github/rbac-allowlist.yaml`) if appropriate.

## Reference Example

See the [security audit finding FIND-001](../../gitops-findings/gitops/gitops-security-audit.md) for the original vulnerability that prompted this validation.

## Related Documentation

- [CI and validation](../agents/ci-and-validation.md)
- [RBAC security context for agents](../agents/rbac-security.md)
- [Kubernetes RBAC documentation](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [OWASP Kubernetes Top 10](https://owasp.org/www-project-kubernetes-top-ten/) - K02: Overly Permissive RBAC
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes) - 5.1.3: Minimize wildcard use in Roles and ClusterRoles

## Notes for AI Agents

- Always run the validation script before committing RBAC changes
- Prefer explicit verbs and resources over wildcards
- Do not assume wildcards are acceptable without checking the validation rules
- If the validator fails, fix the violations before opening a pull request
- Follow Conventional Commits with `AI-Tool` / `AI-Model` footers when fixing RBAC issues
