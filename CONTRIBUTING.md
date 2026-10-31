# Contribution Guidelines

Thank you for considering contributing to our project! Please take a moment to review these guidelines to ensure a smooth collaboration.

## Development Conventions

### Variable Naming Standards

We use the following standardized variable naming conventions:

| Variable        | Description |
|-----------------|-------------|
| `int_cddr`      | Integer calendar days redemption period (funding to delivery) |
| `int_wddr`      | Integer working days redemption period (funding to delivery) |
| `int_cddt`      | Integer calendar days total investment period (funding to maturity) |
| `int_wddt`      | Integer working days total investment period (funding to maturity) |
| `int_cddm`      | Integer calendar days per month (convention: 30) |
| `int_wddm`      | Integer working days per month (convention: 22) |
| `int_cddy`      | Integer calendar days per year (convention: 365) |
| `int_wddy`      | Integer working days per year (convention: 252) |
| `int_cd_bef`    | Integer calendar days before (convention: 1) |
| `int_wd_bef`    | Integer working days before (convention: 1) |
| `int_cd_aft`    | Integer calendar days after (convention: 1) |
| `int_wd_aft`    | Integer working days after (convention: 1) |
| `int_cd_cap`    | Integer calendar days capitalization |
| `int_wd_cap`    | Integer working days capitalization |
| `int_nper_cd`   | Integer number of periods (calendar days) |
| `int_nper_wd`   | Integer number of periods (working days) |
| `float_pv`      | Present value of instrument notional (negative for purchasing, positive for selling) |
| `float_fv`      | Future value of instrument notional (negative for purchasing, positive for selling) |
| `float_notional`| Priced value from contract in absolute terms |
| `float_position_value`| Accounting current market value, for taxing purposes |
| `float_acquisition_basis`| Accounting cost basis, for taxing purposes |
| `float_size`    | Size of instrument contract |
| `float_xcg`     | Exchange value for instrument pricing |
| `float_qty`     | Quantity of instruments (positive for purchasing, negative for selling) |
| `date_ref`        | Reference date |
| `date_xpt`        | Maturity date |
| `date_rdm`        | Redemption date |
| `date_start`        | Start date |
| `date_end`        | End date |
| `date_current` | Current date, for iteration puroposes|
| `int_n_smp`     | Number of samples |
| `int_max_retries` | Maximum number of retries |

## Branching Strategy

**`main` is protected — direct commits and pushes are blocked** (`no-commit-to-branch` locally,
server-side branch protection on GitHub). All changes land via a branch → Pull Request → merge
(online), or `make new_branch` → `make git_merge_to_main` (offline).

### Branch Naming Convention

All branches must follow the pattern: `<purpose>/<branch-task>`

**Available purposes:**

| Purpose         | Format                      | When to Use |
|-----------------|-----------------------------|-------------|
| Feature         | `feature/<name>` or `feat/<name>` | New functionality |
| Bugfix          | `bugfix/<description>` or `fix/<description>` | Bug resolution |
| Hotfix          | `hotfix/<description>` | Critical production fixes |
| Release         | `release/<version>` | Version preparation |
| Documentation   | `docs/<description>` | Documentation updates |
| Refactor        | `refactor/<description>` | Code improvements |
| Chore           | `chore/<description>` | Project maintenance tasks |

**Examples:**
- `feat/user-authentication`
- `fix/login-validation-issue`
- `docs/update-api-reference`

## Commit Message Standards

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification: `<type>/<scope>`

**Available types:**

| Type       | Purpose |
|------------|---------|
| `build`    | Build system or dependency changes |
| `ci`       | CI configuration changes |
| `docs`     | Documentation updates |
| `feat`     | New features |
| `fix`      | Bug fixes |
| `perf`     | Performance improvements |
| `refactor` | Code restructuring |
| `style`    | Formatting changes |
| `test`     | Test additions/modifications |
| `chore`    | Maintenance tasks |
| `revert`   | Reverting changes |
| `bump`     | Version updates |

**Examples:**
- `feat(auth): implement OAuth2 integration`
- `fix(calculations): correct rounding errors in tax computation`
- `docs(readme): add installation instructions`

## Development Setup

1. **Dependency Management**:
   - Use Poetry (version specified in `requirements.txt`)
   - Avoid adding redundant libraries - check `pyproject.toml` first
   - Run `poetry install` to set up the development environment

2. **Pre-commit Hooks**:
   - Install with `make precommit_update`
   - This enables automatic:
     - Code linting
     - Formatting
     - Security vulnerability scanning
     - Large file detection
     - Secret key detection

3. **Testing Framework**:
   - Maintain the standard file structure:
     - Implementation: `src/<feat_name>.py`
     - Tests: `tests/test_<feat_name>.py`
   - Run comprehensive validation with: `make test_feat MODULE=<feat_name>`
        - This command executes:
            - **Ruff**: Linting, formatting, and flagging deprecated Python features
            - **Codespell**: Spelling verification in comments and docstrings
            - **Automated tests**: All test cases matching the project's testing standards
   - Ensure 100% test coverage for critical components
   - Run tests locally before pushing changes

4. **Test-Driven Development**:
   - Write tests before implementation when possible
   - Include normal operations, edge cases, error conditions, type validation, and checks for examples in docstrings
   - Maintain test fixtures for complex scenarios
   - Recommended to use UNIT_TEST_TEMPLATE.md for AI generation of unit tests, in order to implement test-driven development best practices and follow project standards

### Code- and Test-Quality Guards

Each guard runs as a pre-commit hook and as a CI step (`.github/workflows/tests.yaml`):

| Guard | Rule | Escape hatch |
|---|---|---|
| `check_function_length.py` | a function is at most 60 lines, docstring excluded | split it |
| `check_complexity.sh` | cyclomatic complexity: tests 1, src 2, bin 8 (+ nesting depth) | `# complexity-ok: <reason>` on the `def` |
| `check_dead_code.py` | no code vulture proves unreferenced (>=80% confidence) | delete it |
| `check_all_exports.py` | a package `__all__` names every public member of its submodules | export it |
| `check_one_assert.py` | one assertion site per unit test; zero fails anywhere | `# one-assert-ok: <reason>` |
| `check_fixture_scope.py` | a non-function fixture scope needs a written reason | `# fixture-scope-ok: <reason>` |
| `check_assertion_weakening.py` | a PR must not loosen a test silently | `test-change-ok: <reason>` in the PR body |
| `check_gate_integrity.py` | a PR must not weaken a check silently | `gate-change-ok: <reason>` in the PR body |
| `check_coverage_floor.py` | `.coveragerc` `omit` never swallows `ingestion/`/`submission/` code | narrow the glob |
| `check_required_checks_sync.py` | every context in `bin/required-checks.txt` is emitted by a job running on every PR | edit both together |

The first five predate much of this tree, so they run through `bin/quality_ratchet.py` against
a per-file baseline (`bin/quality_baseline.txt`, `<guard> <count> <path>`). A **new** file is
held to the guard in full; an existing file may not go above its count, and when a fix brings it
**below**, the gate fails until you lower the baseline:

```bash
poetry run python bin/quality_ratchet.py <guard> --write-baseline <guard command>
# e.g. poetry run python bin/quality_ratchet.py complexity --write-baseline bash bin/check_complexity.sh
```

`check_dead_code.py` skips when `vulture` is absent locally; CI installs it, so it always runs there.

## Pull Request Process

1. **Create an Issue First**:
   - Check existing issues on this repository's [GitHub Issues](../../issues) page
   - Open a new issue if none exists for your work

2. **Opening a PR**:
   - Fill out the PR template completely
   - Include:
     - Detailed description
     - Changes made
     - Testing performed
     - Documentation updates
     - Any technical debt created

3. **Code Review**:
   - Expect constructive feedback
   - Address all review comments
   - Update documentation as needed
   - Keep commits logically organized

4. **Merge Approval**:
   - Requires at least one approval
   - All tests must pass
   - Code coverage should not decrease
   - Documentation must be updated

## Best Practices

- **Keep branches focused** - one feature/bugfix per branch
- **Make small, frequent commits** - easier to review
- **Write descriptive commit messages** - explain why, not just what
- **Update documentation** - when adding new features
- **Follow existing patterns** - maintain consistency
- **Communicate early** - if you're stuck or need clarification

We appreciate your contributions and look forward to collaborating with you!
