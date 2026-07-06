#!/usr/bin/env python3
"""
RBAC Wildcard Validator for CI

Scans ClusterRole and Role definitions for dangerous wildcard permissions.
Fails CI if critical patterns are detected.

Security rationale:
- Wildcard verbs ('*') on core API resources like secrets/pods grants implicit
  dangerous permissions: 'impersonate', 'escalate', 'bind'
- Wildcard resources ('*') in any API group prevents least-privilege enforcement
- These patterns were identified as HIGH severity (CVSS 9.1) in security audit

Usage:
    python3 check-rbac-wildcards.py

Exit codes:
    0 - No critical violations found
    1 - Critical violations detected (fails CI)
"""

import sys
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import List, Set, Dict, Any

# ANSI color codes for terminal output
RED = '\033[91m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


@dataclass
class RBACViolation:
    """Represents a detected RBAC security violation"""
    file_path: str
    kind: str
    name: str
    api_groups: List[str]
    resources: List[str]
    verbs: List[str]
    severity: str  # 'critical' or 'warning'
    reason: str


# CRITICAL: Core API resources that should NEVER have wildcard verbs
# Wildcard on these grants dangerous implicit permissions like:
# - impersonate (become any user/group)
# - escalate (grant higher privileges)
# - bind (bind to privileged roles)
CRITICAL_CORE_RESOURCES = {
    'secrets',
    'pods',
    'persistentvolumeclaims',
    'serviceaccounts',
    'nodes',
    'namespaces'
}

# Domain-specific OpenStack CRDs - wildcard verbs are lower risk
# These don't grant cluster-admin escalation paths
OPENSTACK_API_GROUPS = {
    'core.openstack.org',
    'network.openstack.org',
    'dataplane.openstack.org',
    'operator.openstack.org',
    'baremetal.openstack.org',
    'topology.openstack.org'
}


def find_rbac_files() -> List[Path]:
    """
    Find all YAML files containing ClusterRole or Role definitions.

    Returns:
        List of Path objects pointing to files with RBAC resources
    """
    rbac_files = []
    repo_root = Path('.').resolve()

    # Search for YAML files
    for yaml_file in repo_root.glob('**/*.yaml'):
        # Skip git directory and hidden files
        if '.git' in yaml_file.parts or any(part.startswith('.') for part in yaml_file.parts[:-1]):
            continue

        try:
            with open(yaml_file, 'r') as f:
                # Quick check: does file contain ClusterRole or Role?
                content = f.read()
                if 'kind: ClusterRole' in content or 'kind: Role' in content:
                    rbac_files.append(yaml_file)
        except (IOError, UnicodeDecodeError):
            # Skip files that can't be read
            continue

    return rbac_files


def parse_rbac_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse YAML file and extract RBAC resources.

    Args:
        file_path: Path to YAML file

    Returns:
        List of RBAC resource dictionaries (ClusterRole or Role)
    """
    rbac_resources = []

    try:
        with open(file_path, 'r') as f:
            # Handle multi-document YAML files
            for doc in yaml.safe_load_all(f):
                if doc and isinstance(doc, dict):
                    kind = doc.get('kind', '')
                    if kind in ('ClusterRole', 'Role'):
                        rbac_resources.append(doc)
    except yaml.YAMLError as e:
        print(f"{YELLOW}Warning: Could not parse {file_path}: {e}{RESET}")
    except IOError as e:
        print(f"{YELLOW}Warning: Could not read {file_path}: {e}{RESET}")

    return rbac_resources


def validate_rbac_rule(
    rule: Dict[str, Any],
    rbac_kind: str,
    rbac_name: str,
    file_path: str
) -> List[RBACViolation]:
    """
    Validate a single RBAC rule for dangerous patterns.

    Args:
        rule: RBAC rule dictionary with apiGroups, resources, verbs
        rbac_kind: ClusterRole or Role
        rbac_name: Name of the RBAC resource
        file_path: Path to file containing this rule

    Returns:
        List of RBACViolation objects (empty if no violations)
    """
    violations = []

    api_groups = rule.get('apiGroups', [])
    resources = rule.get('resources', [])
    verbs = rule.get('verbs', [])

    # CRITICAL CHECK 1: Wildcard verbs on core API sensitive resources
    if '' in api_groups and '*' in verbs:
        sensitive_resources = set(resources) & CRITICAL_CORE_RESOURCES
        if sensitive_resources:
            violations.append(RBACViolation(
                file_path=file_path,
                kind=rbac_kind,
                name=rbac_name,
                api_groups=api_groups,
                resources=sorted(list(sensitive_resources)),
                verbs=verbs,
                severity='critical',
                reason=(
                    f"Wildcard verbs on core API resources {sorted(list(sensitive_resources))}. "
                    f"This grants dangerous implicit permissions: 'impersonate', 'escalate', 'bind'. "
                    f"Replace with explicit verbs: [get, list, watch, create, update, patch, delete]"
                )
            ))

    # CRITICAL CHECK 2: Wildcard resources in any API group
    # Exception: OpenStack CRDs are domain-specific, lower risk
    if '*' in resources:
        # Check if this is an OpenStack CRD (warning) or critical API group
        if any(group in OPENSTACK_API_GROUPS for group in api_groups):
            # OpenStack CRDs: warning only (can be upgraded to critical later)
            violations.append(RBACViolation(
                file_path=file_path,
                kind=rbac_kind,
                name=rbac_name,
                api_groups=api_groups,
                resources=resources,
                verbs=verbs,
                severity='warning',
                reason=(
                    f"Wildcard resources in OpenStack API group {api_groups}. "
                    f"Consider replacing with explicit resource list for better security."
                )
            ))
        else:
            # Non-OpenStack wildcards: critical violation
            violations.append(RBACViolation(
                file_path=file_path,
                kind=rbac_kind,
                name=rbac_name,
                api_groups=api_groups,
                resources=resources,
                verbs=verbs,
                severity='critical',
                reason=(
                    f"Wildcard resources in API group {api_groups}. "
                    f"Replace with explicit resource list based on actual usage. "
                    f"See docs/skills/rbac-security-validation.md for guidance."
                )
            ))

    # WARNING CHECK: Wildcard verbs on non-core resources
    # Report for visibility, but don't fail CI (domain-specific CRDs)
    if '*' in verbs and '' not in api_groups:
        # Check if it's OpenStack CRD
        if any(group in OPENSTACK_API_GROUPS for group in api_groups):
            violations.append(RBACViolation(
                file_path=file_path,
                kind=rbac_kind,
                name=rbac_name,
                api_groups=api_groups,
                resources=resources,
                verbs=verbs,
                severity='warning',
                reason=(
                    f"Wildcard verbs on OpenStack CRD {api_groups}. "
                    f"This is acceptable for domain-specific resources, but consider explicit verbs for clarity."
                )
            ))

    return violations


def format_violation_report(violations: List[RBACViolation]) -> str:
    """
    Format violations as a readable report with boxes.

    Args:
        violations: List of RBACViolation objects

    Returns:
        Formatted string report
    """
    if not violations:
        return f"{GREEN}✅ No RBAC violations found{RESET}"

    critical = [v for v in violations if v.severity == 'critical']
    warnings = [v for v in violations if v.severity == 'warning']

    report = []

    if critical:
        report.append(f"\n{RED}{BOLD}❌ RBAC Security Validation FAILED{RESET}\n")
        report.append(f"{RED}Critical Violations Found ({len(critical)}):{RESET}\n")

        for i, v in enumerate(critical, 1):
            report.append("┌" + "─" * 78 + "┐")
            report.append(f"│ {BOLD}Violation #{i}{RESET}" + " " * 65 + "│")
            report.append(f"│ File: {v.file_path}" + " " * (77 - len(f"File: {v.file_path}")) + "│")
            report.append(f"│ Kind: {v.kind}" + " " * (77 - len(f"Kind: {v.kind}")) + "│")
            report.append(f"│ Name: {v.name}" + " " * (77 - len(f"Name: {v.name}")) + "│")
            report.append("├" + "─" * 78 + "┤")
            report.append(f"│ API Groups: {v.api_groups}" + " " * (77 - len(f"API Groups: {v.api_groups}")) + "│")
            report.append(f"│ Resources: {v.resources}" + " " * (77 - len(f"Resources: {v.resources}")) + "│")
            report.append(f"│ Verbs: {v.verbs}" + " " * (77 - len(f"Verbs: {v.verbs}")) + "│")
            report.append("├" + "─" * 78 + "┤")
            report.append(f"│ {RED}⚠️  SEVERITY: {v.severity.upper()}{RESET}" + " " * (77 - len(f"⚠️  SEVERITY: {v.severity.upper()}") - 9) + "│")

            # Wrap reason text to fit in box
            reason_lines = []
            words = v.reason.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= 76:
                    current_line += (word + " ")
                else:
                    reason_lines.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                reason_lines.append(current_line.strip())

            for line in reason_lines:
                report.append(f"│ {line}" + " " * (77 - len(line)) + "│")

            report.append("└" + "─" * 78 + "┘\n")

    if warnings:
        report.append(f"\n{YELLOW}Warnings ({len(warnings)}):{RESET}\n")
        for w in warnings:
            report.append(f"  {YELLOW}⚠{RESET}  {w.file_path} ({w.kind} {w.name})")
            report.append(f"     {w.reason}\n")

    if critical:
        report.append(f"\n{BOLD}Remediation:{RESET}")
        report.append("1. Replace verbs: ['*'] with explicit list: [get, list, watch, create, update, patch, delete]")
        report.append("2. Replace resources: ['*'] with explicit resource kinds")
        report.append("3. See docs/skills/rbac-security-validation.md for detailed guidance")
        report.append("4. Refer to security audit: gitops-findings/gitops/gitops-security-audit.md")
        report.append(f"\n{RED}{BOLD}CI FAILED: RBAC security violations detected{RESET}\n")

    return "\n".join(report)


def check_rbac_wildcards() -> int:
    """
    Main function: scan, validate, and report RBAC violations.

    Returns:
        0 if no critical violations, 1 if violations found
    """
    print(f"\n{BLUE}{BOLD}RBAC Wildcard Security Validator{RESET}")
    print(f"{BLUE}Scanning repository for dangerous RBAC patterns...{RESET}\n")

    rbac_files = find_rbac_files()

    if not rbac_files:
        print(f"{YELLOW}No RBAC files (ClusterRole/Role) found in repository{RESET}")
        return 0

    print(f"Found {len(rbac_files)} RBAC file(s) to validate:\n")
    for f in rbac_files:
        print(f"  - {f.relative_to(Path('.').resolve())}")
    print()

    all_violations = []

    for rbac_file in rbac_files:
        rbac_resources = parse_rbac_file(rbac_file)

        for resource in rbac_resources:
            kind = resource.get('kind', 'Unknown')
            name = resource.get('metadata', {}).get('name', 'unnamed')
            rules = resource.get('rules', [])

            for rule in rules:
                violations = validate_rbac_rule(
                    rule=rule,
                    rbac_kind=kind,
                    rbac_name=name,
                    file_path=str(rbac_file.relative_to(Path('.').resolve()))
                )
                all_violations.extend(violations)

    # Generate and print report
    report = format_violation_report(all_violations)
    print(report)

    # Count critical violations
    critical_count = sum(1 for v in all_violations if v.severity == 'critical')
    warning_count = sum(1 for v in all_violations if v.severity == 'warning')

    print(f"\n{BOLD}Summary:{RESET}")
    print(f"  Critical violations: {critical_count}")
    print(f"  Warnings: {warning_count}")
    print()

    if critical_count > 0:
        return 1  # Fail CI
    else:
        print(f"{GREEN}✅ RBAC validation passed{RESET}\n")
        return 0  # Pass CI


if __name__ == '__main__':
    sys.exit(check_rbac_wildcards())
