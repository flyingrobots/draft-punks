"""Packaging smoke tests.

Catches regressions like pyproject.toml pointing at a nonexistent readme.
"""
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_readme_path_exists():
    """The readme file declared in pyproject.toml must actually exist."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    readme_conf = data.get("project", {}).get("readme")
    if readme_conf is None:
        return  # no readme declared

    if isinstance(readme_conf, str):
        readme_file = readme_conf
    elif isinstance(readme_conf, dict):
        readme_file = readme_conf.get("file")
    else:
        return

    if readme_file:
        full_path = PROJECT_ROOT / readme_file
        assert full_path.exists(), (
            f"pyproject.toml declares readme = '{readme_file}' "
            f"but {full_path} does not exist"
        )


def test_required_metadata_fields():
    """Core metadata fields must be present and non-empty."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    assert project.get("name"), "project.name is missing"
    assert project.get("version"), "project.version is missing"
    assert project.get("description"), "project.description is missing"


def test_entry_point_module_exists():
    """The CLI entry point module declared in pyproject.toml must exist on disk."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    scripts = data.get("project", {}).get("scripts", {})
    for name, entry in scripts.items():
        # entry is like "doghouse.cli.main:app"
        module_path = entry.split(":")[0]
        # Convert dotted module path to file path under src/
        parts = module_path.split(".")
        # Check that the source file exists
        py_path = PROJECT_ROOT / "src" / Path(*parts).with_suffix(".py")
        pkg_path = PROJECT_ROOT / "src" / Path(*parts) / "__init__.py"
        assert py_path.exists() or pkg_path.exists(), (
            f"Entry point '{name} = {entry}' references module {module_path} "
            f"but neither {py_path} nor {pkg_path} exists"
        )
