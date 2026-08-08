# SQL Studio — Main Branch Protection

## Target branch

`main`

## Required settings

The first tagged release should be followed by protection of `main` with these controls:

- require changes to arrive through a pull request before merge;
- required approving reviews: `0` (solo-maintainer workflow; CI remains the technical gate);
- require resolution of review conversations before merge;
- require status checks before merge;
- required status check: `test` from the `CI` workflow;
- require the branch to be up to date before merge;
- block force pushes;
- block branch deletion;
- do not allow bypasses by default except repository-administration recovery.

## Rationale

SQL Studio already uses branch + PR + CI + squash-merge as its development path. Protection should enforce that established path without introducing an artificial second-person approval dependency for a solo-maintainer repository.

The `test` job is the authoritative technical gate because it covers compilation, imports, the complete unit suite, repository CLI smoke paths, distribution build, installed-wheel execution and artifact generation.

## Verification

After configuration, GitHub branch metadata for `main` must report protection enabled. A direct destructive update or merge with a failing required check must be rejected by GitHub.

## Administration boundary

Branch protection is a GitHub repository-administration setting, not source-controlled application behavior. The policy is documented here so the exact desired configuration is reproducible even when the active automation connector does not expose administration writes.
