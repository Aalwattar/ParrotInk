# Specification: GitHub Actions CI/CD Integration

**Overview**
Implement automated CI/CD using GitHub Actions, tailored for the \uv\ package manager and the project's existing build script. This track will establish a CI gate for all code changes and an automated release process for tagged versions.

**Functional Requirements**

1.  **CI Workflow (\.github/workflows/ci.yml\):**
    *   **Trigger:** \push\ to \main\ branch, \pull_request\ to any branch.
    *   **Environment:** \windows-latest\.
    *   **Steps:**
        *   Checkout repository.
        *   Setup Python 3.12.
        *   Install \uv\.
        *   \uv sync --group dev\ to install dependencies.
        *   \uv run ruff check .\ for linting.
        *   \uv run mypy .\ for type checking.
        *   \uv run pytest -q\ for unit tests.

2.  **Release Workflow (\.github/workflows/release.yml\):**
    *   **Trigger:** \push\ of tags matching \*.*.*\.
    *   **Environment:** \windows-latest\.
    *   **Permissions:** \contents: write\ (for creating releases).
    *   **Steps:**
        *   Checkout repository.
        *   Setup Python 3.12.
        *   Install \uv\.
        *   \uv sync\ to install production dependencies.
        *   **Version Validation (pwsh):**
            \\\powershell
            \$tag = "${\{ github.ref_name \}}".TrimStart("v")
            \$ver = (Get-Content pyproject.toml | Select-String '^version = "(.*)"' | ForEach-Object { \$_.Matches.Groups[1].Value })
            if (\$tag -ne \$ver) { throw "Tag v\$tag does not match app version \$ver" }
            \\\
        *   **Build Execution:** Run \.\scripts\build_onefile.ps1\.
        *   **Asset Preparation:**
            *   Compute SHA256 of \dist/ParrotInk.exe\.
            *   Save hash to \dist/ParrotInk.exe.sha256\.
        *   **GitHub Release:**
            *   Use \softprops/action-gh-release@v2\.
            *   Enable \generate_release_notes\.
            *   Upload \dist/ParrotInk.exe\ and \dist/ParrotInk.exe.sha256\.

**Acceptance Criteria**
- [ ] CI workflow passes on a fresh push to \main\.
- [ ] Release workflow correctly fails if the tag version doesn't match \pyproject.toml\.
- [ ] Release workflow successfully creates a GitHub release with the \.exe\ and \.sha256\ assets when a matching tag is pushed.
