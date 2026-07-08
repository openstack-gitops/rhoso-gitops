# RBAC Security

This document provides AI agents with context on RBAC security requirements and automated validation in this repository.

## Background

A security audit identified a **HIGH severity vulnerability (CVSS 9.1)** where the ArgoCD ClusterRole granted wildcard permissions on cluster-wide Secrets, Pods, and entire API groups. This created a cluster-admin-equivalent escalation path for anyone who could compromise a git repository tracked by ArgoCD.

To prevent regression, automated CI validation fails pull requests containing dangerous RBAC patterns.

## Security Rationale

### Why Wildcards Are Dangerous

1. **Implicit Permissions**: In Kubernetes RBAC, `verbs: ['*']` doesn't just mean "all current verbs" - it includes future verbs added to the API. This has historically included dangerous permissions like:
   - `impersonate` - Added in Kubernetes 1.5
   - `escalate` and `bind` - Added in Kubernetes 1.8

2. **Cluster-Admin Equivalent**: Wildcard verbs on `secrets` + `pods` in the core API is functionally cluster-admin:
   - Read any Secret → steal ServiceAccount tokens
   - Create Pods → mount any ServiceAccount → escalate privileges
   - Chain these to become cluster-admin

3. **GitOps Attack Surface**: ArgoCD auto-syncs from git repositories. If an attacker can push to a tracked repo, wildcard RBAC turns that into cluster compromise.

### Real-World Example

The vulnerability fixed in this repository (FIND-001) had this pattern:

```yaml
apiGroups: [""]
resources: [secrets, pods]
verbs: ['*']
```

**Attack path:**
1. Attacker pushes malicious Pod manifest to tracked git repo
2. ArgoCD auto-syncs and creates the Pod (has `create` pods permission)
3. Pod mounts privileged ServiceAccount (ArgoCD has `*` on secrets)
4. Pod now has cluster-wide secret read access
5. Attacker reads `kube-system` secrets → cluster-admin

**Defense:** By replacing `'*'` with explicit `[get, list, watch]` on pods, step 2 fails - ArgoCD can no longer create Pods.

## Agent Requirements

When working with RBAC manifests (ClusterRole or Role), agents must:

1. **Never introduce wildcard patterns** that will fail CI validation
2. **Run the validation script** before committing:
   ```bash
   python3 .github/scripts/check-rbac-wildcards.py
   ```
3. **Use explicit verbs and resources** instead of wildcards
4. **Understand the principle of least privilege**: Only grant the minimum permissions needed

## Validation Rules

The validation script (`.github/scripts/check-rbac-wildcards.py`) enforces these rules:

### Critical Resources (Never Allow Wildcard Verbs)

```python
CRITICAL_CORE_RESOURCES = {
    'secrets',
    'pods',
    'persistentvolumeclaims',
    'serviceaccounts',
    'nodes',
    'namespaces'
}
```

When these resources appear in the core API group (`apiGroups: [""]`), wildcard verbs (`verbs: ['*']`) are **forbidden**.

### Wildcard Resources (Never Allow)

Wildcard resources (`resources: ['*']`) are **forbidden** in all API groups, regardless of verbs.

### OpenStack CRDs (Warning Only)

```python
OPENSTACK_API_GROUPS = {
    'core.openstack.org',
    'dataplane.openstack.org',
    'operator.openstack.org',
    'baremetal.openstack.org'
}
```

Wildcard verbs on OpenStack CRDs generate warnings but do not fail CI. However, explicit verbs are still preferred.

## Agent Workflow

When modifying RBAC manifests:

1. **Read existing permissions** to understand the current scope
2. **Identify the minimal verb set needed**:
   - Read-only? → `[get, list, watch]`
   - Create/update? → Add `[create, patch]` or `[create, update, patch]`
   - Delete? → Add `[delete]`
3. **Identify the minimal resource set needed**:
   - Scan the repository for what resources are actually used
   - Check the operator's API documentation
   - Use grep to find resource references:
     ```bash
     grep -r "apiVersion.*<api-group>" . | grep "kind:" | sort -u
     ```
4. **Write explicit permissions** - never use wildcards
5. **Run validation locally**:
   ```bash
   python3 .github/scripts/check-rbac-wildcards.py
   ```
6. **Commit only if validation passes**

## Maintenance Considerations

### Updating Validation Rules

The validation logic is in `.github/scripts/check-rbac-wildcards.py`. Key configuration sets are documented above.

To add new critical resources or API groups:
1. Edit the relevant sets in the script
2. Test thoroughly against existing ClusterRoles
3. Update this documentation

### Upgrading to Stricter Validation

Currently, wildcard verbs on OpenStack CRDs are warnings. To make them critical (fail CI):

1. Remove the OpenStack API groups from the warning exemption
2. Update this documentation and `docs/skills/rbac-security-validation.md`
3. **Test on existing ClusterRoles first** - this will likely break the build
4. Fix all violations before merging
5. Announce the change to contributors

## Error Messages

When CI fails with RBAC violations, agents should:

1. Read the CI output to identify the problematic file, line, and permission
2. Consult the skill documentation at `docs/skills/rbac-security-validation.md`
3. Apply the appropriate fix (explicit verbs/resources)
4. Re-run validation locally before pushing

Never suggest:
- Disabling the validation check
- Using wildcards "temporarily"
- Working around the validation

## Further Reading

- **Security Audit**: `gitops-findings/gitops/gitops-security-audit.md` - Full audit report with FIND-001 details
- **Triage Report**: `gitops-findings/gitops/gitops-triage.md` - Analysis of the high-severity finding
- **Kubernetes RBAC**: https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- **OWASP Kubernetes Top 10**: K02 - Overly Permissive RBAC
- **CIS Kubernetes Benchmark**: 5.1.3 - Minimize wildcard use in Roles and ClusterRoles
