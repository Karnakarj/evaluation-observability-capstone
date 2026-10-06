# Brief Reflection Evaluation and Observability Capstone 

**Name:** Uma Maheshwara Chary Jonnalagadda
**Date:** 2026-09-24

> Ground every answer in your own run. When a question asks for a number, file name, or line, paste
> it from artifacts your a reviewer should be able to find it. Answers that are correct in the 
> abstract but cite nothing do not meet the bar. Keep it short and specific.

---

## 0. Environment

| Field | Value |
|---|---|
| OS & version | Debian GNU/Linux 12 (bookworm) — Udacity workspace (`environment.txt`) |
| Python version | Python 3.13.0 (`environment.txt`) |
| Date run | 2026-09-24 |
| Ran any system live? (which) | Yes — System 1 `policy-extractor pipeline` ran live via the Vocareum proxy (see `environment.txt`). Systems 2 and 3 ran offline (`--mode replay`, `--offline`). |

---

## 1. Validated, routed pipeline

| Evidence | Value |
|---|---|
| Passing test count | 45 passed, 3 skipped (`01-policy-pipeline/tests.txt`) |
| Routing output file | `01-policy-pipeline/routing_decisions.json` (9 records; terminal capture `pipeline-run.txt`). Offline routing test also captured: `pipeline-run-offline-routing.txt` (9 passed) |
| auto_approve / human_review / spot_check counts | 0 / 9 / 0, plus `"escalations": 1` (POL-2025-009, `endorsements_absent`, `missing_source`) — `pipeline-run.txt` |

**1a. Retry boundary.** From your perturbation run (a required field removed), paste the escalation
record. How many API calls did the system make, and why is retrying a futile case worse than
escalating it?

> From `01-policy-pipeline/perturbation-run.txt`, case C (I set the required field `endorsements` to null):
> `RetryFutileEscalation(policy_id='POL-2025-001', field='endorsements', category='missing_source', detected_pattern='endorsements_absent', ...)` with the reason ending in `Retry is futile; escalate to human review.`
> It made only **1 API call** (`API calls : 1`), even though I queued 4 responses and `max_retries=3`. Compare case B, where I made the premium negative (a `format` error): it took 2 calls and fixed itself (`retry_count=1`).
> Retrying only helps when the answer is in the document and the model misread it. Here the document just doesn't have endorsements, so asking again would give the same null and waste calls and time. Worse, if you keep telling the model "this field is required", it might make something up just to pass the check. Sending it to a person after one call is cheaper and safer.

**1b. Reading the router.** Pick one `human_review` record from your routing output. Which of the
three signals (confidence, reviewer, integration) sent it to a human? If you had trusted the model's
confidence alone, what would have happened?

> From `01-policy-pipeline/routing_decisions.json`: **POL-2025-006** (umbrella) got `"decision": "human_review"` with `"fields_below_threshold": []`, `"integration_failures": []` and `"reviewer_disagreements": ["deductible"]`.
> So the **reviewer** was the signal that sent it to a human. Its confidence scores were all 0.95 or 1.0, which is above the threshold (`DEFAULT_CONFIDENCE_THRESHOLD = 0.90` in `policy_extractor/routing.py`).
> If I had only trusted confidence, this policy would have been auto-approved even though a second model disagreed about the deductible. It wasn't just this one: POL-2025-002, -004, -005, -007 and -008 were also caught only by the reviewer, so 6 of my 9 human_review records would have slipped through. And umbrella is the same policy type that looks bad in the calibration report (1c).

**1c. Where the aggregate lies.** Run the calibration snippet. Quote the one cell whose accuracy lags
its confidence, plus the overall figure. What does slicing by `policy_type × field` catch that a
single number hides?

> From `01-policy-pipeline/calibration-report.txt`: `umbrella  exclusions      n=2 conf=0.93 acc=0.00 brier=0.865` and `OVERALL brier=0.291`.
> The auto and home rows are fine (`acc=1.00`), but umbrella exclusions was wrong both times while the model said it was 93% sure. The overall 0.291 doesn't look too bad, so if I only looked at that one number I'd never notice that one slice is completely broken. Splitting by policy type and field shows exactly where the problem is, so I can send just that slice to review instead of distrusting everything.

---

## 2. Schema-enforced two-pass extraction

| Evidence | Value |
|---|---|
| Passing test count | 25 passed (`02-mortgage-extraction/tests.txt`) |
| Document run | `income_sum_mismatch.txt` (`discrepancy-run.txt`); `appraisal_informal_sqft.txt`, `income_missing_bonus.txt` (`extract-run.txt`) |
| Classified type | `income_verification` (sum-mismatch and missing-bonus paystubs), appraisal (`appraisal` from the `classify:` log line, e.g. `classify: model=claude-haiku-4-5 in=1612 out=96 type=income_verification` |) 

**2a. Two guarantees.** Paste your discrepancy-run output. Tool use already forces valid JSON, yet the
validator still catches a bad sum. Why are these two different guarantees? Name one error each cannot
catch.

> From `02-mortgage-extraction/discrepancy-run.txt`: `"consistent": false` with `"field": "total_monthly_income"`, `"calculated": 9642.17`, `"stated": 10892.17`, `"delta": -1250.0`.
> Tool use only makes sure the JSON has the right shape: the right fields with the right types. `10892.17` is a valid number, so the schema has no problem with it. The validator checks something else: do the numbers actually add up? The line items (5416.67 + 2140.00 + 1250.00 + 385.50 + 450.00) come to 9642.17, not 10892.17. It looks like the paystub counted the bonus twice.
> What tool use can't catch: a value that is well-formed but wrong, like this total. What the validator can't catch: mistakes that still add up, or small ones inside its $1 tolerance. In my perturbation a $0.50 difference passed (`{"consistent":true,"discrepancies":[]}`, case C in `perturbation-run.txt`).

**2b. Refusing to fabricate.** Run on a document missing a field. Paste that field's output. Why null
instead of an invented value? Point to the schema choice that allows it.

> From `02-mortgage-extraction/extract-run.txt` (`income_missing_bonus.txt`, classified `type=income_verification`): `"base_monthly": 5673.08`, `"bonus_monthly": null`, `"bonus_ytd": null`.
> This paystub has no bonus line at all, so null is the honest answer. The schema allows it: `mortgage_extractor/schema.py` line 104 has `"bonus_monthly": {"type": ["number", "null"]}`, and bonus isn't in any `required` list. If it were a required plain number, the forced tool call would have to put some number there, and the model would probably guess (like 0 or a typical bonus). And 0 and null don't mean the same thing: 0 means "the paystub says no bonus", null means "the paystub doesn't say". The example in `prompts.py` line 65 also shows `"bonus_monthly": null` for a paystub without a bonus.

**2c. Normalization.** Quote one field where the source text and extracted value differ in format
 `2400`). Why normalize at extraction time rather than downstream?

> `appraisal_informal_sqft.txt` line 37 says `approximately 2,400 sq ft (above-grade finished)`, and `extract-run.txt` has `"gross_living_area_sqft": 2400`.
> At extraction time the model can see the context. It knows this number is the living area and not the ~900 sq ft basement or the 441 sq ft garage listed just below it. Code later on would only get a text string and would need messy parsing for "approx", "~", commas and units. Converting it once to an integer means the validator and comparisons (like the comps 2,365 / 2,310 / 2,512) can just do math on it. The downside is that the word "approximately" gets lost.

---

## 3. Multi-source synthesis

| Evidence | Value |
|---|---|
| Passing test count | 34 passed in 1003.38s (`03-supply-chain/tests.txt`) |
| Briefing file | `03-supply-chain/briefing.md` (full terminal capture: `investigation-run.txt`) |
| Section the conflict landed in | `## Contested` — `### on_time_delivery_rate  _[2 sources, conflicting]_  ⚠ESCALATE` |

**3a. Annotate, don't arbitrate.** Quote one conflicting-metric pair from your briefing — both values,
sources, dates. Give one way a reader is better served by the preserved conflict than by a single
reconciled number.

> From `03-supply-chain/briefing.md`, under `## Contested`: `on_time_delivery_rate` has `95.0 percent` from `supplier_audit (as of 2026-04-10)` and `78.0 percent` from `logistics (as of 2026-04-05)`, with `escalation: high-impact metric is contested across sources`.
> If the system averaged these (about 86.5%) or just picked one, I'd get a number nobody actually reported, and I couldn't tell who is being optimistic. Seeing both, it's clear the supplier's own audit says 95% while our shipping data says 78% (and shows `late_shipment_count` of `11.0 shipments`). That gap is the useful part: it tells me to question the supplier's number. My perturbation backs this up. When I changed the audit to 78, the same metric became `[corroborated across 2 sources]` (`perturbation-run.txt`).

**3b. Source goes dark.** Run with `--simulate-timeout`. Paste the part of the briefing showing the
failed source. How is "unreachable" handled differently from "nothing to report," and why does the run
still finish?

> From `03-supply-chain/timeout-run.txt`: `> Sources unavailable: logistics unavailable (timeout)`, and under `## Incomplete`: `late_shipment_count  _[missing source: timeout reading logistics]_`.
> "Unreachable" is marked as a gap with a reason (a timeout), so I know to try again later. "Nothing to report" looks different: `production_capacity_utilization` says `missing source: no source reported this metric`, which means every source answered but none had that data. The run still finishes because each source is read separately, so one failing source just becomes a note and the other three still build the briefing.
> One thing I noticed: with logistics down, the 95 vs 78 conflict disappears. On-time delivery shows only the supplier's 95% as `[single source only]`, and Contested is empty. So the conflict is hidden, not solved, and the "Sources unavailable" line is the only warning.
 `### late_shipment_count  _[missing source: timeout reading logistics]_` / `- missing source: timeout reading logistics`.
> "Unreachable" is recorded as a named gap with a reason (`timeout reading logistics`) and the source is listed as unavailable at the top. "Nothing to report" looks different: `production_capacity_utilization  _[missing source: no source reported this metric]_` — every source answered, none had the metric. The first means "ask again later"; the second means "this data doesn't exist in our sources". The run finishes because the coordinator treats each reader independently: a timeout on one becomes an annotation, and the other three sources still produce a briefing.
> One caveat I found: with logistics dark, `on_time_delivery_rate` shows only `95.0 percent — supplier_audit` as `[single source only]` under Well-Established, and Contested is empty. The conflict is hidden, not resolved — the banner is the only clue.

**3c. Dates as a guardrail.** Quote two claims about the same supplier with different dates. How does
requiring a date stop a time difference from reading as a contradiction?

> From `briefing.md`: `defect_rate_ppm` has `180.0 ppm` from `supplier_audit (as of 2026-04-10)` and `190.0 ppm` from `internal_quality (as of 2026-04-08)`. The on-time pair is dated too: 95% as of 2026-04-10 and 78% as of 2026-04-05.
> Because every claim has a date, I can check whether two numbers are about the same time before calling it a contradiction. Both on-time numbers cover Q1 2026 and are only 5 days apart, so this is a real disagreement. If one had been from last year, the difference might just mean things changed. Without dates you can't tell "it changed" apart from "they disagree".

---

## 4. Synthesis

**4a. One principle.** Name the single moment in your runs (system + artifact) where *evaluate the
output, don't trust the model's word* most clearly caught something a trusting design would have
shipped.

> System 2, `02-mortgage-extraction/discrepancy-run.txt`. The model did everything right: valid JSON, the correct document type (`type=income_verification`), and it copied `"stated_monthly_total": 10892.17` exactly from the paystub. If I had trusted that output, $10,892.17 a month would have gone straight to underwriting. Only the separate math check caught that the items add up to 9642.17 (`"delta": -1250.0`). The model wasn't wrong, the document was, and only a check outside the model could catch that.

**4b. Confidence and correctness.** Pick the system where this mattered most, and explain why using confidence evidence.
something you observed.

> System 1. In `calibration-report.txt`, `umbrella exclusions` shows `conf=0.93 acc=0.00`: very confident and wrong every time. In my live run, 6 of the 9 human_review records (like POL-2025-006 in `routing_decisions.json`) had every field above the 0.90 confidence threshold and were caught only because the reviewer disagreed. A simple rule like "auto-approve if confidence is above 0.90" would have let all of them through. Confidence is something to measure, not something to trust.

**4c. Apply it.** Describe a real workflow where an LLM pulls structured results from messy input. Which validated retry with escalation, independent review with deterministic routing, or provenance-preserving annotation conflict would you reach for first, and what would you instrument 
to know when it broke?

> I'm interested in Indian mutual funds, and I track fund holdings (stock, sector, % of NAV, AUM) from monthly AMC factsheets and fund websites in a comparison spreadsheet. An LLM would help here because every AMC formats its factsheet differently.
> I'd start with **validated retry with escalation**: nullable fields so a missing value stays empty instead of being guessed, plus math checks like the mortgage system. For example, holdings plus cash should add up to about 100%, and weight x AUM should roughly match market value. Format errors get retried; if a factsheet just doesn't have a field, it gets escalated after one try. After that I'd add **conflict annotation** for when the factsheet and a fund website disagree, keeping both values with their source and date.
> To know when it breaks, I'd track: how often each AMC gets retried or escalated (a sudden jump probably means they changed their layout), validator failures split by AMC and field (so one bad AMC doesn't hide in an average), and how old each source's data is, so an old source can't quietly win the way the supplier's 95% did in the timeout run.
