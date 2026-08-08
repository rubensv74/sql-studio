# SQL Studio — Release Policy

## 1. Scope

SQL Studio uses **GitHub Releases only** for the current release model. Publishing to PyPI is explicitly out of scope until a later product decision authorizes it.

## 2. Release identity

- The canonical package version lives in `src/sqlstudio/_version.py`.
- `core/version.txt` is a compatibility mirror and must match the package version exactly.
- Stable release tags use `vMAJOR.MINOR.PATCH`, for example `v0.19.0`.
- The release workflow accepts stable SemVer only (`X.Y.Z`).

## 3. Release gate

A release may be created only from a commit on `main` whose `CI` workflow completed successfully.

`.github/workflows/release.yml` is triggered by successful completion of `CI` and then:

1. checks out the exact commit SHA validated by CI;
2. resolves and validates the package version;
3. verifies the compatibility version mirror;
4. rejects an existing tag if it points to a different commit;
5. builds the sdist and wheel;
6. creates the GitHub tag and Release when no Release exists yet;
7. attaches both distribution artifacts;
8. verifies the resulting GitHub Release.

If the Release already exists for the current version, the workflow is idempotent and does not republish it.

## 4. Tag immutability

Release tags are immutable. A tag such as `v0.19.0` must never be moved to another commit. If the workflow detects that the tag already exists on a different SHA, it fails instead of overwriting history.

## 5. Distribution artifacts

Every GitHub Release must contain:

- `sql_studio-<version>-py3-none-any.whl`
- `sql_studio-<version>.tar.gz`

The same package build contract remains validated independently by the normal `CI` workflow.

## 6. PyPI boundary

The release workflow must not contain PyPI credentials, Trusted Publishing configuration, `twine upload`, or any equivalent publication step.

A future PyPI publication milestone requires a separate explicit decision covering package-name ownership, authentication, release provenance and rollback/recovery procedures.

## 7. First controlled release

The first controlled release under this policy is `v0.19.0`.

## 8. Relationship to branch protection

GitHub Release creation and `main` branch protection are separate controls. Release automation is repository-defined and reproducible. Branch protection must additionally require the `test` CI job before merge and block destructive branch operations as documented in `docs/branch-protection.md`.
