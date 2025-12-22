# Testing triage workflow (MassGen)

This doc describes how we keep the suite scalable as the project evolves:

- **Unit tests** should pass by default without external services/secrets.
- **Integration tests** are **opt-in** and should be marked accordingly.
- **Known failures** can be tracked via **expiring `xfail` entries** (temporary, auditable).
- Failures are triaged into **clusters** and turned into **task packets** for subagents.

## Canonical commands

- Full suite (uses repo config):

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests
```

- Generate JUnit XML (for clustering):

```bash
mkdir -p .cursor/triage
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests \
  --junitxml .cursor/triage/junit.xml
```

## Marker policy (what runs by default)

Markers are defined in [`pyproject.toml`](../../pyproject.toml) and enforced via [`massgen/tests/conftest.py`](../../massgen/tests/conftest.py).

- **Default behavior**: tests marked `integration`, `docker`, or `expensive` are **skipped** unless explicitly enabled.
- **Enable integration**:

```bash
RUN_INTEGRATION=1 /Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests
```

or

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests --run-integration
```

Similarly:
- `RUN_DOCKER=1` / `--run-docker`
- `RUN_EXPENSIVE=1` / `--run-expensive`

## Expiring xfail registry (temporary known failures)

Registry file: [`massgen/tests/xfail_registry.yml`](../../massgen/tests/xfail_registry.yml)

- Add an entry keyed by **pytest nodeid**.
- Every entry must include a **reason**.
- Strongly recommended: a **link** and an **expires** date (`YYYY-MM-DD`).

Example:

```yaml
massgen/tests/test_some_feature.py::TestThing::test_case:
  reason: "Flaky on macOS due to timing"
  link: "https://github.com/ORG/REPO/issues/123"
  expires: "2026-01-31"
  strict: true
```

Fail the run if any `xfail` entry is past expiry:

```bash
XFAIL_EXPIRED_FAIL=1 /Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests
```

## Failure clustering + task packets

Script: [`scripts/triage_pytest_failures.py`](../../scripts/triage_pytest_failures.py)

Run:

```bash
/Users/admin/src/MassGen/.venv/bin/python scripts/triage_pytest_failures.py \
  --junit-xml .cursor/triage/junit.xml \
  --out-dir .cursor/triage
```

Outputs:
- `.cursor/triage/summary.md`: top clusters by count
- `.cursor/triage/tasks/cluster_<id>.md`: one packet per cluster

## Subagent task packet format (Definition of Done)

Each `cluster_<id>.md` packet contains:
- Cluster signature (exception type + normalized message)
- Affected nodeids
- Minimal repro commands (single test + up to 25 tests)
- Top stack frames + suspect files

Subagent “done” checklist:
1. Confirm whether cluster is **unit** or **integration/docker/expensive**.
2. If integration-style, add the correct marker and ensure it’s skipped by default.
3. If unit, fix code/tests so the cluster passes deterministically.
4. If deferring, add an **expiring** `xfail_registry.yml` entry with reason + link + expiry.
5. Rerun targeted tests and confirm the cluster is resolved (or properly skipped/xfail’ed).

## Subagent task definition workflow (process + inputs/outputs)

This workflow defines how we spawn subagents to fix failing-test clusters in a consistent, scalable way.

### Inputs

- **Cluster task packet**: `.cursor/triage/tasks/cluster_<id>.md`
- **Repo context**:
  - pytest policy: `massgen/tests/conftest.py`
  - xfail registry: `massgen/tests/xfail_registry.yml`
  - current failing JUnit: `.cursor/triage/junit-prepolicy.xml` (or the latest run)
- **Execution environment constraints**:
  - assume no external keys/services unless explicitly enabled
  - treat `integration/docker/expensive` as opt-in (skipped by default)

### Process

1. **Reproduce**
   - Run the “Single failing test” command from the packet.
2. **Classify**
   - Decide: `unit` vs `integration`/`docker`/`expensive`.
3. **Decide strategy**
   - **Integration-style**: add proper marker(s) + a graceful skip if prerequisites are missing.
   - **Unit-style**: fix implementation and/or test to match current behavior and make it deterministic.
   - **Deferred**: add/update an **expiring** entry in `massgen/tests/xfail_registry.yml` (reason + link + expiry).
4. **Implement**
   - Keep changes minimal and localized; avoid broad refactors unless necessary.
5. **Verify**
   - Re-run (a) the single test, then (b) the “Up to 25 tests” cluster repro command.
6. **Update artifacts**
   - If the cluster signature changed (e.g., different exception), re-run triage and refresh packet links if needed.

### Outputs

- **Code changes** (one or more):
  - updated tests and/or production code
  - added/updated markers on tests (integration/docker/expensive)
  - updated `massgen/tests/xfail_registry.yml` (if deferring)
- **Verification evidence**:
  - commands executed and their outcomes (single test + cluster subset)
- **Task handoff note** (short, pasteable):
  - what was fixed, what remains, and any follow-ups (e.g., remove xfail by date)


