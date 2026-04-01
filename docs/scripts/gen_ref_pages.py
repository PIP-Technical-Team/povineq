"""Generate API reference pages for mkdocstrings.

This script is consumed by the mkdocs-gen-files plugin at build time.
It creates one Markdown file per public module under docs/reference/.
Public modules are written to reference/<name>.md; internal modules that
export public types are written to reference/internal/<name>.md.
"""

import warnings
from pathlib import Path

import mkdocs_gen_files

PACKAGE_NAME = "povineq"

nav = mkdocs_gen_files.Nav()
mod_root = Path("src", PACKAGE_NAME)

# Public modules to document at reference/<name>.md
public_modules = [
    "__init__",
    "stats",
    "country_profiles",
    "auxiliary",
    "info",
]

# Internal modules that export public types — documented at reference/internal/<name>.md
internal_public = [
    "_errors",
    "_response",
    "_cache",
]

# Public-named modules intentionally excluded from docs (internal utilities)
_excluded_from_docs = {"utils"}


def _module_metadata(mod_name: str) -> tuple[str, str, str]:
    """Return (doc_name, identifier, title) for a given module name."""
    if mod_name == "__init__":
        return "index", PACKAGE_NAME, f"{PACKAGE_NAME} (top-level)"
    if mod_name.startswith("_"):
        doc_name = mod_name.removeprefix("_")
        return doc_name, f"{PACKAGE_NAME}.{mod_name}", doc_name.replace("_", " ").title()
    return mod_name, f"{PACKAGE_NAME}.{mod_name}", mod_name.replace("_", " ").title()


for mod_name in public_modules:
    py_path = mod_root / f"{mod_name}.py"
    if not py_path.exists():
        warnings.warn(
            f"Listed module {py_path} not found — no reference page generated.",
            stacklevel=1,
        )
        continue

    doc_name, identifier, title = _module_metadata(mod_name)
    full_doc_path = Path("reference", f"{doc_name}.md")

    with mkdocs_gen_files.open(full_doc_path, "w") as md_file:
        md_file.write(f"# {title}\n\n::: {identifier}\n")

    mkdocs_gen_files.set_edit_path(full_doc_path, py_path)
    nav[doc_name] = f"{doc_name}.md"

for mod_name in internal_public:
    py_path = mod_root / f"{mod_name}.py"
    if not py_path.exists():
        warnings.warn(
            f"Listed module {py_path} not found — no reference page generated.",
            stacklevel=1,
        )
        continue

    doc_name, identifier, title = _module_metadata(mod_name)
    full_doc_path = Path("reference", "internal", f"{doc_name}.md")

    with mkdocs_gen_files.open(full_doc_path, "w") as md_file:
        md_file.write(f"# {title}\n\n::: {identifier}\n")

    mkdocs_gen_files.set_edit_path(full_doc_path, py_path)
    nav["internal", doc_name] = f"internal/{doc_name}.md"

# Assert no newly added public modules are silently omitted from docs
existing_public = {p.stem for p in mod_root.glob("[a-z]*.py")}
documented = set(public_modules)
undocumented = existing_public - documented - _excluded_from_docs
if undocumented:
    raise ValueError(
        f"Public modules not in gen_ref_pages.py: {undocumented}. "
        "Add them to public_modules or _excluded_from_docs."
    )

# Write SUMMARY.md for literate-nav
with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
