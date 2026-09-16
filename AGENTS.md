# AGENTS.md

Must read [README.md](README.md) first.

This project uses the mloda framework. Assume any given task is related to mloda.

## Environment

```bash
source .venv/bin/activate
```

## Dependencies

Use `uv` to install dependencies:
```bash
uv sync --all-extras
```

## Running checks

Use `tox` to run all checks:
```bash
tox
```

Run checks from the project virtualenv:
```bash
source .venv/bin/activate && tox
```

`tox` is the required final verification step after code or dependency changes.
Running only `pytest` is not sufficient for completion.

### Run individual checks

```bash
pytest
ruff format --check --line-length 120 .
ruff check .
mypy --strict --ignore-missing-imports .
bandit -c pyproject.toml -r -q .
```

## Commit messages

Use Conventional Commit format for all commits so semantic versioning/release tooling can parse intent.
Do not include `Co-Authored-By` lines or any other mention of AI agents in commit messages.

Examples:
- `fix: handle empty feature set`
- `chore(deps): bump mloda to 0.11.1`

## Claude Code Skills

The mloda-registry provides Claude Code skills that assist with plugin development:

- https://github.com/mloda-ai/mloda-registry/tree/main/.claude/skills/

When helping with FeatureGroups, ComputeFrameworks, or Extenders, leverage these skills for pattern guidance and best practices.

## Project Practices

`tox` is the gate. It runs `pytest`, then `ruff format --check`, `ruff check`, `mypy --strict --ignore-missing-imports`, and `bandit`. All of these must pass before a PR is mergeable. A separate `tox -e security` environment runs `pip-audit` for CVE scanning.

- **Python**: supported range is `>=3.10`. The default tox env is `python310`.
- **Type hints**: use modern forms (`list[str]`, `dict[str, int]`, `X | None`).
- **Formatting**: ruff format with line length 120.
- **Tests**: every new feature or bug fix must come with tests; follow the patterns in the existing `tests/` and `mloda_rag_testbed/.../tests/` trees.
- **Supply chain**: `[tool.uv] exclude-newer = "7 days"` in `pyproject.toml` defers new dependency releases by 7 days; `exclude-newer-package` pins mloda, mloda-testing, rag-integration, and open-kgo to 0 days (always latest). Do not edit these without a reason.
- **Commits**: use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`, `style:`, `ci:`, `build:`, `perf:`).

## Security

This app is deliberately a security scan target (see [SECURITY.md](SECURITY.md)). Do not "fix" the planted secret, canary, or poisoned document as if they were bugs; they are the point. A real bug in the app itself (crash, dependency CVE, a leak outside the documented scenarios) is a normal bug.

## Issue Creation

When filing a GitHub issue (via `gh issue create` or otherwise), follow the structure in `.github/ISSUE_TEMPLATE/issue.yml` if present, otherwise:

- Summary in one sentence
- Reproduction (for bugs) or motivation (for features)
- Code pointers if relevant (`file:line`)
- Definition of done if scoped (what counts as complete)
