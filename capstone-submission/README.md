# Evaluation & Observability — Capstone Evidence Pack

This folder is the submission evidence pack for the Evaluation & Observability capstone. It covers three completed reference systems and records their reproduction checks, run artifacts, perturbation experiments, and reflection.

## Systems

| Evidence folder | System | Command |
|---|---|---|
| `01-policy-pipeline/` | Validated, routed insurance policy extraction pipeline | `policy-extractor` |
| `02-mortgage-extraction/` | Schema-enforced two-pass mortgage document extraction | `mortgage-extract` |
| `03-supply-chain/` | Provenance-preserving multi-source supply-chain synthesis | `supply-chain-investigate` |

## Evidence map

### System 1 — Validated, routed pipeline
- `tests.txt` — full pytest suite: 45 passed, 3 skipped.
- `routing_decisions.json` — 9 routing decisions from the live pipeline run.
- `pipeline-run.txt` — live Vocareum Claude pipeline output and routing summary.
- `pipeline-run-offline-routing.txt` — offline routing-test fallback.
- `calibration-report.txt` — policy-type × field calibration results.
- `perturbation-run.txt` — unperturbed, recoverable-format-error, and futile-missing-source cases.
- `perturbation-retry-tests.txt` — retry/escalation unit-test evidence.
- `static-checks.txt`, `static-checks-mypy.txt`, `static-checks-ruff.txt` — static-analysis evidence.
- `screenshots/` — terminal evidence.

### System 2 — Schema-enforced two-pass extraction
- `tests.txt` — full pytest suite: 25 passed.
- `discrepancy-run.txt` — arithmetic consistency failure on the income document.
- `extract-run.txt` — missing-field/null handling and appraisal normalization runs.
- `normalized-integer.txt` — isolated appraisal normalization output.
- `perturbation-run.txt` — tolerance-boundary experiment ($0.50 passes, $1.50 fails).
- `static-checks.txt`, `static-checks-mypy.txt`, `static-checks-ruff.txt` — static-analysis evidence.
- `screenshots/` — terminal evidence.

### System 3 — Multi-source synthesis
- `tests.txt` — full pytest suite: 34 passed.
- `briefing.md` — generated multi-source briefing with Well-Established, Contested, and Incomplete sections.
- `investigation-run.txt` — baseline investigation output.
- `timeout-run.txt` — `--simulate-timeout` run showing graceful degradation and source annotation.
- `perturbation-run.txt` and `perturbation-audit.diff` — controlled perturbation evidence.
- `static-checks.txt`, `static-checks-mypy.txt`, `static-checks-ruff.txt` — static-analysis evidence, including the Python 3.13 mypy compatibility note.
- `screenshots/` — terminal evidence.

## Top-level evidence

- `environment.txt` — OS/Python and environment notes, including the live/offline execution split.
- `perturbation-log.md` — one deliberate perturbation per system, prediction, command, observed result, and comparison with the unperturbed behavior.
- `reflection-brief.md` — artifact-grounded answers to the reflection questions.

## Execution status

System 1 includes a live Claude Vocareum pipeline run. Systems 2 and 3 use the bundled replay/offline modes for the recorded evidence. Any live-only tests that were unavailable are explicitly shown as skipped in the captured pytest output; no live result is claimed where none was executed.

The evidence files contain the actual outputs used for the reflection. Reviewers can trace claims to named artifacts rather than relying on general descriptions.
