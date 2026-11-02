import json
import re
import sys
import urllib.error
import urllib.request

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version

# We always judge against 3.11, no matter which Python is running this script.
TARGET_PYTHON = Version("3.11")

# Matches "name==1.2.3" and ignores any trailing "; marker" or "# comment".
PIN_PATTERN = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*==\s*([^\s;#]+)")


def read_requirements(path):
    """Return the meaningful lines of the file (no blanks, no comments)."""
    with open(path) as f:
        stripped = (line.strip() for line in f)
        return [line for line in stripped if line and not line.startswith("#")]


def get_release(name, version):
    """Ask PyPI for one release. Returns the JSON, or None if it doesn't exist."""
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return None
        raise  # anything else (500, rate limit...) is a real problem


def lowest_python(requires_python):
    """
    Work out the minimum Python version a specifier asks for.
    E.g. ">=3.8,<3.13" -> 3.8. If there's no lower bound at all, call it 0.
    """
    lower_bounds = [
        Version(part.version.replace(".*", ""))
        for part in SpecifierSet(requires_python)
        if part.operator in (">=", ">", "~=", "==")
    ]
    return max(lower_bounds) if lower_bounds else Version("0")


def main(path):
    lines = read_requirements(path)

    missing = []  # package or pinned version not on PyPI
    incompatible = []  # exists, but doesn't support Python 3.11
    strictest = None  # (minimum python, "name==version") with the highest minimum

    for line in lines:
        match = PIN_PATTERN.match(line)
        if not match:
            # Not a proper pin, so there's nothing we can look up.
            missing.append(line)
            continue

        name, version = match.groups()
        release = get_release(name, version)
        if release is None:
            missing.append(line)
            continue

        requires_python = (release["info"].get("requires_python") or "").strip()
        if not requires_python:
            continue  # no restriction declared -> counts as compatible

        try:
            specifier = SpecifierSet(requires_python)
            works_on_311 = specifier.contains(TARGET_PYTHON, prereleases=True)
            minimum = lowest_python(requires_python)
        except InvalidSpecifier:
            continue  # PyPI metadata is garbage, nothing sensible to compare

        if not works_on_311:
            incompatible.append(line)

        if strictest is None or minimum > strictest[0]:
            strictest = (minimum, f"{name}=={version}")

    print(f"Dependencies checked: {len(lines)}")
    print(f"Not found on PyPI: {len(missing)}")
    print(f"Incompatible with Python 3.11: {len(incompatible)}")
    if strictest:
        print(f"Highest requirement: {strictest[1]} (>={strictest[0]})")
    else:
        print("Highest requirement: none")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "requirements.txt")
