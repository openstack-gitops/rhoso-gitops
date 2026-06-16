# Add Controlplane Service Component

This skill creates a new service component for the OpenStack controlplane.

## Purpose

Scaffolds the directory structure and boilerplate files needed to add a new OpenStack service to the controlplane components catalog.

## Usage

When an AI agent or contributor needs to add a new service component to `/components/rhoso/controlplane/services/`, use this skill to ensure consistency with the repository's patterns.

## Prerequisites

- Service name (kebab-case, e.g., `barbican`, `designate`, `octavia`)
- Understanding of the service's configuration requirements
- Red Hat OpenStack Services on OpenShift documentation link for the service (if available)

## Steps

### 1. Create Service Directory

```bash
SERVICE_NAME="<service-name>"  # e.g., barbican, designate, octavia
mkdir -p components/rhoso/controlplane/services/${SERVICE_NAME}
```

### 2. Create `kustomization.yaml`

Create `components/rhoso/controlplane/services/${SERVICE_NAME}/kustomization.yaml`:

```yaml
---
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component

patches:
  - path: service.yaml
    target:
      kind: OpenStackControlPlane
```

### 3. Create `service.yaml`

Create `components/rhoso/controlplane/services/${SERVICE_NAME}/service.yaml`:

```yaml
---
# https://docs.redhat.com/en/documentation/red_hat_openstack_services_on_openshift/18.0/html-single/...
# TODO: Replace with actual documentation link for this service
apiVersion: core.openstack.org/v1beta1
kind: OpenStackControlPlane
metadata:
  name: openstack-control-plane
spec:
  <service-name>:
    enabled: true
    template:
      # Service-specific configuration goes here
      # Refer to the OpenStackControlPlane CRD and service operator documentation
```

**Important:**
- Replace `<service-name>` with the actual service name in camelCase (e.g., `barbican`, `octavia`, `designate`)
- Replace the documentation URL with the actual Red Hat documentation link
- Add service-specific template configuration based on the service operator's CRD

### 4. Validate the Component

Run kustomize build to ensure the component is valid:

```bash
kustomize build components/rhoso/controlplane/services/${SERVICE_NAME}
```

### 5. Add to Examples (Optional but Recommended)

Consider adding an example that uses this service component in `/example` to demonstrate usage.

### 6. Run CI Validation

Before committing, run the validation commands from `.github/workflows/` to ensure the component passes CI checks:

```bash
# Check the .github/workflows/ directory for exact validation commands
# Typically includes:
# - YAML linting
# - Kustomize build tests
```

## YAML Conventions

Ensure all files follow repository conventions:

- **Document header:** Every YAML file must start with `---` (comments may appear above it)
- **Documentation links:** Include Red Hat documentation URLs in comments
- **Indentation:** Use 2 spaces (consistent with existing files)
- **One object per file:** Unless the pattern clearly uses multi-document files

## Reference Example

See `/components/rhoso/controlplane/services/watcher/` for a complete working example.

## Related Documentation

- [Repository structure](../agents/repository.md)
- [YAML, Helm, and Kustomize conventions](../agents/yaml-helm-kustomize.md)
- [CI and validation](../agents/ci-and-validation.md)
- [OpenStackControlPlane CR reference](https://docs.redhat.com/en/documentation/red_hat_openstack_services_on_openshift/18.0/html/deploying_red_hat_openstack_services_on_openshift/assembly_creating-the-control-plane#ref_example-OpenStackControlPlane-CR_controlplane)

## Notes for AI Agents

- This is a **component catalog**, not a full cluster configuration
- Prefer conservative, backwards-compatible changes
- Do not open PRs without explicit human request
- Follow Conventional Commits with `AI-Tool` / `AI-Model` footers when contributing
