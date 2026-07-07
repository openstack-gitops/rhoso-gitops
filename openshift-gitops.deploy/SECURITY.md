# Security Hardening for OpenShift GitOps Deployment

> **⚠️ WARNING**: The default configuration provided in this repository is designed for development and testing environments. It is **NOT hardened for production use** and requires security configuration before deploying to production clusters.

## Overview

This directory deploys Red Hat OpenShift GitOps (ArgoCD) with a permissive configuration to enable rapid onboarding and testing. Production deployments require additional hardening steps to establish proper security boundaries and follow the principle of least privilege.

## Key Security Considerations

The default configuration has the following security implications:

1. **Unrestricted AppProject**: Applications use the `default` AppProject which permits:
   - Any source Git repository
   - Any destination cluster and namespace
   - All cluster-scoped resources
   
2. **Floating Git References**: Applications use `targetRevision: HEAD` with automated sync, meaning any commit merged to the upstream repository is immediately applied to your cluster without review.

3. **Broad RBAC Permissions**: The `gitops-openstack` ClusterRole grants wildcard (`*`) permissions on multiple resources including Secrets, Pods, and PersistentVolumeClaims cluster-wide.

4. **Automated Synchronization**: `syncPolicy.automated` is enabled, removing manual approval gates for changes.

## Production Hardening Checklist

Before deploying to production, complete these hardening steps:

### 1. Create a Restricted AppProject

Replace the `default` AppProject with a custom project that enforces security boundaries:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: rhoso-production
  namespace: openshift-gitops
spec:
  # Restrict source repositories to your fork/mirror
  sourceRepos:
    - 'https://github.com/your-org/gitops.git'
  
  # Limit destinations to specific namespaces
  destinations:
    - namespace: 'openstack'
      server: 'https://kubernetes.default.svc'
    - namespace: 'openstack-operators'
      server: 'https://kubernetes.default.svc'
  
  # Whitelist only required cluster-scoped resources
  clusterResourceWhitelist:
    - group: 'metal3.io'
      kind: 'BareMetalHost'
    - group: 'operators.coreos.com'
      kind: 'Subscription'
    # Add only the specific resources your deployment requires
  
  # Deny access to sensitive resources
  namespaceResourceBlacklist:
    - group: ''
      kind: Secret
```

Update all Application manifests to reference this project:
```yaml
spec:
  project: rhoso-production  # Instead of 'default'
```

### 2. Pin Git References to Commit SHAs

Replace `targetRevision: HEAD` with specific commit SHAs:

```yaml
# ❌ Insecure
spec:
  source:
    targetRevision: HEAD

# ✅ Secure
spec:
  source:
    targetRevision: 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0'  # Full 40-char SHA
```

This ensures changes are explicitly approved before deployment.

### 3. Disable Automated Sync for Production

Remove or disable `syncPolicy.automated` to require manual approval:

```yaml
# ❌ Auto-applies all changes
spec:
  syncPolicy:
    automated: {}

# ✅ Requires manual sync
spec:
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

Sync applications manually via the ArgoCD UI or CLI after review.

### 4. Review and Restrict RBAC Permissions

The default `clusterrole.yaml` grants broad permissions. For production:

- **Audit the ClusterRole**: Review `enable/clusterrole.yaml` and remove unnecessary wildcard (`*`) permissions
- **Use Namespace-Scoped Roles**: Where possible, replace the ClusterRole with namespace-specific Roles
- **Principle of Least Privilege**: Grant only the minimum verbs and resources required for your deployment
- **Separate ServiceAccounts**: Use different ServiceAccounts for different workloads instead of sharing the ArgoCD controller's SA

Example of restricting permissions:
```yaml
# Instead of:
verbs: ['*']

# Use explicit verbs:
verbs: ['get', 'list', 'watch', 'create', 'update', 'patch']
# Explicitly exclude 'delete', 'deletecollection', 'impersonate', 'escalate', 'bind'
```

### 5. Enable ArgoCD RBAC Policies

Configure ArgoCD's built-in RBAC to control who can sync/modify applications:

```yaml
apiVersion: argoproj.io/v1beta1
kind: ArgoCD
metadata:
  name: openshift-gitops
spec:
  rbac:
    policy: |
      p, role:readonly, applications, get, */*, allow
      p, role:readonly, applications, list, */*, allow
      p, role:deployer, applications, sync, production/*, allow
      g, production-deployers, role:deployer
    scopes: '[groups]'
```

### 6. Additional Hardening Steps

- **Enable Audit Logging**: Configure ArgoCD and OpenShift audit logs to track all changes
- **Use SSO/OAuth**: Ensure proper authentication is configured (OpenShift OAuth is configured by default)
- **Network Policies**: Restrict network access to ArgoCD components
- **Webhook Validation**: Use ArgoCD's webhook validation to verify changes before sync
- **Secrets Management**: Ensure External Secrets Operator or Vault Secrets Operator is properly configured
- **Regular Updates**: Keep ArgoCD and OpenShift GitOps Operator up to date with security patches

## Official Documentation

For comprehensive security guidance, refer to these official resources:

### ArgoCD Security Documentation
- **[ArgoCD Security Overview](https://argo-cd.readthedocs.io/en/stable/operator-manual/security/)** - Main security documentation
- **[ArgoCD End User Threat Model](https://github.com/argoproj/argoproj/blob/main/docs/end_user_threat_model.pdf)** - Threat model and security considerations
- **[ArgoCD Projects (AppProjects)](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/#projects)** - Detailed AppProject configuration
- **[ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)** - Production deployment best practices
- **[ArgoCD RBAC Configuration](https://argo-cd.readthedocs.io/en/stable/operator-manual/rbac/)** - Configuring ArgoCD's internal RBAC

### Red Hat Documentation
- **[OpenShift GitOps Security](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/cicd/gitops)** - Red Hat OpenShift GitOps documentation
- **[OpenShift Security Best Practices](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/security_and_compliance/index)** - General OpenShift security guidance

## Support and Questions

If you have questions about securing your ArgoCD deployment:
1. Review the official documentation linked above
2. Consult your organization's security team
3. Open an issue in the upstream ArgoCD repository for ArgoCD-specific questions
4. Refer to Red Hat support if you have an active subscription

## Summary

**Do not deploy the default configuration to production without hardening.** The permissive defaults are intentional for ease of testing but create security risks in production environments. Follow this guide and the official ArgoCD security documentation to establish appropriate security boundaries for your deployment.
