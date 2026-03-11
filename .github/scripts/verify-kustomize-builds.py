#!/usr/bin/env python3
"""Verify that all rhoso-gitops components build successfully with kustomize.

Discovers components dynamically under components/rhoso/ and example/,
runs kustomize build for each, and reports a summary table. Fails only at
the end if any component failed.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


KUSTOMIZATION_FILES = ("kustomization.yaml", "kustomization.yml", "Kustomization")
RHOSO_COMPONENTS_ROOT = Path("components/rhoso")
EXAMPLES_ROOT = Path("example")
BUILD_TEST_DIR = Path(".build-test")


@dataclass
class BuildTestCase:
    """A single component or overlay to test."""

    id: str
    component_paths: list[Path]
    build_dir_name: str
    # If set, build directly from this directory (e.g. examples). Otherwise generate kustomization.
    source_directory: Path | None = None


@dataclass
class BuildResult:
    """Result of running kustomize build on a test case."""

    test_case: BuildTestCase
    success: bool
    error_message: str = ""


def discover_rhoso_components(repo_root: Path) -> list[BuildTestCase]:
    """Discover all buildable components under components/rhoso/."""
    cases: list[BuildTestCase] = []
    rhoso_root = repo_root / RHOSO_COMPONENTS_ROOT

    if not rhoso_root.exists():
        return cases

    for kustomization_path in _find_kustomization_files(rhoso_root):
        rel_path = kustomization_path.relative_to(rhoso_root).parent
        path_parts = rel_path.parts

        # Service pattern: .../services/<name>/ requires parent as base
        if "services" in path_parts:
            services_idx = path_parts.index("services")
            parent_parts = path_parts[:services_idx]
            parent_path = rhoso_root.joinpath(*parent_parts)

            if parent_path.exists() and (parent_path / "kustomization.yaml").exists():
                components = [
                    repo_root / RHOSO_COMPONENTS_ROOT / Path(*parent_parts),
                    repo_root / RHOSO_COMPONENTS_ROOT / rel_path,
                ]
            else:
                components = [repo_root / RHOSO_COMPONENTS_ROOT / rel_path]
        else:
            components = [repo_root / RHOSO_COMPONENTS_ROOT / rel_path]

        id_str = str(rel_path).replace("\\", "/")
        slug = id_str.replace("/", "-")
        cases.append(
            BuildTestCase(
                id=f"rhoso/{id_str}",
                component_paths=components,
                build_dir_name=f"rhoso-{slug}",
            )
        )

    return cases


def discover_examples(repo_root: Path) -> list[BuildTestCase]:
    """Discover all example overlays. No filtering - test every example as committed."""
    cases: list[BuildTestCase] = []
    examples_root = repo_root / EXAMPLES_ROOT

    if not examples_root.exists():
        return cases

    for example_dir in sorted(examples_root.iterdir()):
        if not example_dir.is_dir():
            continue

        if _find_kustomization_in_dir(example_dir) is None:
            continue

        rel_example = example_dir.relative_to(repo_root)
        id_str = str(rel_example).replace("\\", "/")
        slug = id_str.replace("/", "-")
        cases.append(
            BuildTestCase(
                id=id_str,
                component_paths=[],  # Unused: we build directly from source_directory
                build_dir_name=f"example-{slug}",
                source_directory=example_dir,
            )
        )

    return cases


def _find_kustomization_files(root: Path) -> list[Path]:
    """Find all kustomization files under root."""
    results: list[Path] = []
    for f in root.rglob("*"):
        if f.is_file() and f.name in KUSTOMIZATION_FILES:
            results.append(f)
    return sorted(results)


def _find_kustomization_in_dir(directory: Path) -> Path | None:
    """Return the kustomization file in dir, or None."""
    for name in KUSTOMIZATION_FILES:
        path = directory / name
        if path.exists():
            return path
    return None


def generate_kustomization(
    build_dir: Path, component_paths: list[Path], repo_root: Path
) -> None:
    """Write a minimal kustomization.yaml referencing the given components."""
    rel_paths: list[str] = []
    for comp in component_paths:
        resolved = (repo_root / comp).resolve() if not comp.is_absolute() else comp
        rel = Path("..") / ".." / resolved.relative_to(repo_root)
        rel_paths.append(str(rel).replace("\\", "/"))

    kustomization = {
        "apiVersion": "kustomize.config.k8s.io/v1beta1",
        "kind": "Kustomization",
        "components": rel_paths,
    }

    import yaml

    out_path = build_dir / "kustomization.yaml"
    out_path.write_text(
        yaml.dump(kustomization, default_flow_style=False, sort_keys=False)
    )


def run_kustomize_build(build_dir: Path) -> tuple[bool, str]:
    """Run kustomize build in build_dir. Return (success, error_message)."""
    try:
        result = subprocess.run(
            ["kustomize", "build", "."],
            cwd=build_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return True, ""
        return False, result.stderr or result.stdout or f"Exit code {result.returncode}"
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 60s"
    except FileNotFoundError:
        return False, "kustomize not found in PATH"
    except Exception as e:
        return False, str(e)


def build_and_collect(
    test_case: BuildTestCase, repo_root: Path, build_base: Path
) -> BuildResult:
    """Generate kustomization (or use source dir), run build, return result."""
    if test_case.source_directory is not None:
        # Build directly from the example directory (tests refs, patches, etc. as committed)
        build_dir = test_case.source_directory
    else:
        build_dir = build_base / test_case.build_dir_name
        build_dir.mkdir(parents=True, exist_ok=True)
        generate_kustomization(build_dir, test_case.component_paths, repo_root)

    success, error = run_kustomize_build(build_dir)

    return BuildResult(
        test_case=test_case,
        success=success,
        error_message=error[:300] if error else "",
    )


def format_results_table(results: list[BuildResult]) -> str:
    """Format results as a readable table."""
    lines: list[str] = []
    col_width = 45
    status_width = 10

    header = f"| {'Component':<{col_width}} | {'Status':<{status_width}} |"
    separator = f"|{'-' * (col_width + 2)}|{'-' * (status_width + 2)}|"
    lines.append(header)
    lines.append(separator)

    for r in results:
        status = "OK" if r.success else "FAILED"
        id_display = (
            r.test_case.id[:col_width]
            if len(r.test_case.id) <= col_width
            else r.test_case.id[: col_width - 3] + "..."
        )
        lines.append(f"| {id_display:<{col_width}} | {status:<{status_width}} |")

    return "\n".join(lines)


def format_failures_summary(results: list[BuildResult]) -> str:
    """Format detailed failure messages."""
    failed = [r for r in results if not r.success]
    if not failed:
        return ""

    lines: list[str] = ["", "Failed components:", ""]
    for r in failed:
        lines.append(f"  {r.test_case.id}")
        if r.error_message:
            for err_line in r.error_message.strip().split("\n")[:5]:
                lines.append(f"    {err_line}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    """Discover components, run builds, report results. Returns 1 if any failed."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    test_cases: list[BuildTestCase] = []
    test_cases.extend(discover_rhoso_components(repo_root))
    test_cases.extend(discover_examples(repo_root))

    if not test_cases:
        print("No components to test.")
        return 0

    build_base = repo_root / BUILD_TEST_DIR
    build_base.mkdir(exist_ok=True)

    results: list[BuildResult] = []
    for tc in test_cases:
        result = build_and_collect(tc, repo_root, build_base)
        results.append(result)
        status = "OK" if result.success else "FAIL"
        print(f"  [{status}] {tc.id}", flush=True)

    print()
    print(format_results_table(results))
    print(format_failures_summary(results))

    failed_count = sum(1 for r in results if not r.success)
    if failed_count > 0:
        print(f"\n{failed_count} component(s) failed.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
