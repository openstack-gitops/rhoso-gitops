# Security Policy

## Reporting a Vulnerability

The openstack-k8s-operators project welcomes responsible disclosure of security vulnerabilities. Security is a top priority for this project and the Red Hat OpenStack Services on OpenShift (RHOSO) ecosystem.

### How to Report

**For Red Hat customers and partners:**
- Report security vulnerabilities to Red Hat Product Security: https://access.redhat.com/security/team/contact/
- Red Hat Product Security Incident Response Team (PSIRT) will coordinate with the project maintainers

**For community contributors:**
- **Do not** open public GitHub issues for security vulnerabilities
- Email security concerns to: secalert@redhat.com
- Include detailed steps to reproduce, impact assessment, and any proof-of-concept code if available

### What to Expect

- **Acknowledgment:** We will acknowledge receipt of your vulnerability report within 3 business days
- **Investigation:** Our security team will investigate and validate the report
- **Timeline:** We aim to provide an initial assessment within 7 business days
- **Resolution:** Critical vulnerabilities will be prioritized for immediate patching
- **Disclosure:** We follow coordinated disclosure practices and will work with you on an appropriate disclosure timeline

### Security Considerations for This Repository

This repository contains GitOps configuration manifests for deploying Red Hat OpenStack Services on OpenShift using ArgoCD. It does not ship application source code but manages:

- ArgoCD/OpenShift-GitOps bootstrap configurations (primarily for dev/lab/testing environments)
- Kustomize overlays for RHOSO control-plane and data-plane
- Helm charts (rhoso-apps)
- Kubernetes RBAC policies
- ArgoCD hook Jobs and utility manifests

**Key Security Concerns:**
- Overly permissive RBAC configurations
- Insecure container image references or workload configurations
- Supply-chain vulnerabilities in GitHub Actions, container images, or dependencies
- GitOps trust boundary violations (AppProjects, targetRevision, syncPolicy)
- Secrets handling and External Secrets Operator configurations

See our [ArgoCD Deployment Security Hardening Guide](openshift-gitops.deploy/SECURITY.md) for deployment-specific security controls and best practices.

## Supported Versions

We provide security updates for:

| Version/Branch | Supported          |
| -------------- | ------------------ |
| main (latest)  | :white_check_mark: |
| Tagged releases| :x: (no backports) |
| Feature branches| :x: (use at own risk) |

Security patches are applied to the `main` branch only. We do not backport security fixes to older tagged releases. Users should use the latest available tag and update to newer tags as they are released to receive security fixes.

## Security Update Policy

- **Critical vulnerabilities** (CVSS >= 9.0): Patched within 48 hours of validation
- **High severity** (CVSS 7.0-8.9): Patched within 7 days
- **Medium severity** (CVSS 4.0-6.9): Patched in next regular release cycle
- **Low severity** (CVSS < 4.0): Addressed in scheduled maintenance updates

## Supply-Chain Security

This repository implements automated supply-chain security controls:

- **Dependabot:** Automated dependency updates for GitHub Actions, Python packages, and container images
- **OpenSSF Scorecard:** Automated security scoring and best-practice validation
- **SBOM Generation:** Software Bill of Materials for Helm charts in SPDX format
- **SHA-pinned Actions:** GitHub Actions pinned to commit SHAs for integrity
- **Image Digest Pinning:** Container images pinned to SHA256 digests where possible

See our OpenSSF Scorecard results: https://securityscorecards.dev/viewer/?uri=github.com/openstack-k8s-operators/gitops

## Additional Resources

- [Red Hat Product Security Center](https://access.redhat.com/security/)
- [OpenStack Security Advisories](https://security.openstack.org/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [ArgoCD Security Hardening](https://argo-cd.readthedocs.io/en/stable/operator-manual/security/)

## Acknowledgments

We appreciate security researchers and the community for responsible disclosure. Contributors who report valid security vulnerabilities will be acknowledged in our security advisories (unless they prefer to remain anonymous).

---

**Last Updated:** 2026-07-08
