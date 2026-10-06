# Perturbation Log

For each system, make one deliberate change to an input or configuration, predict the outcome, run
it, and record what actually happened. See the starters in the Instructions, or design your own (your
own experiment earns more credit).

---

### System 1 — validated, routed pipeline

- **Change I made (file + what I changed):** No API key was used, so I drove the real `extract_with_retry` offline with recorded model responses (`01-policy-pipeline/perturbation_driver.py`; no system code changed). Same document (`POL-2025-001`) every time; I changed only the model's answer: (B) `premium_amount` = `-1500.0` on the first attempt, then a corrected answer; (C) the required field `endorsements` blanked to `null` (4 identical responses queued, `max_retries=3`).
 `01-policy-pipeline/perturbation-run.txt`. Cross-checked with `pytest tests/test_us01_retry.py -v` → `01-policy-pipeline/perturbation-retry-tests.txt` (`test_ac_01_04_missing_source_halts_immediately PASSED`).
- **What I predicted:** (B) one retry with the error fed back, success on call 2. (C) no retry all at immediate escalation after 1 call, because re-asking cannot create data the document does not contain. 
- **What actually happened (paste the key output line):**
  - A (unperturbed): `result type : PolicyExtraction` · `API calls : 1` · `retry_count=0, final_attempt_index=0, validation_history=[]`
  - B: `API calls : 2` · `retry_count=1` · `ValidationError(field='premium_amount', observed_value='-1500.0', category='format', detected_pattern='negative_premium', ...)`
  - C: `result type : RetryFutileEscalation` · `API calls : 1` · `category='missing_source', reason="Field 'endorsements' returned null  detected_pattern='endorsements_absent', the source document does not contain this information. Retry is futile; escalate to human review."`
- **How this differs from the unperturbed run:** Unperturbed returns a clean `PolicyExtraction` after 1 call with an empty validation history. The recoverable `format` error cost exactly one extra call and self-healed (the history records why). The `missing_source` error spent 1 call and stopped, even though three more responses were available `max_retries=3` and it returned an escalation record for a human instead of a record. 

---

### System 2 — schema-enforced two-pass extraction 

- **Change I made (file + what I changed):** Took the extraction the CLI actually produced for `income_sum_mismatch.txt` (`02-mortgage-extraction/discrepancy-run.txt`) and changed only `income.stated_monthly_total`, then re-ran the real `validate()` at its default $1 tolerance (`02-mortgage-extraction/perturbation_driver.py`; no system code changed). Values: (B) `9642.17` = the line-item sum, (C) `9642.67` = $0.50 off, (D) `9643.67` = $1.50 off.
- **Command I ran:** `.venv/bin/python perturbation_driver.py` from `04-validate-mathematical-consistency/solution` → `02-mortgage-extraction/perturbation-run.txt`
- **What I predicted:** B clean; C clean (inside tolerance — a blind spot by design); D flagged with delta -1.5.
- **What actually happened (paste the key output line):**
  - A (unperturbed): `{"consistent":false,"discrepancies":[{"field":"total_monthly_income","calculated":9642.17,"stated":10892.17,"delta":-1250.0}]}`
  - B: `{"consistent":true,"discrepancies":[]}`
  - C: `{"consistent":true,"discrepancies":[]}`
  - D: `{"consistent":false,"discrepancies":[{"field":"total_monthly_income","calculated":9642.17,"stated":9643.67,"delta":-1.5}]}`
- **How this differs from the unperturbed run:** The real paystub states `TOTAL MONTHLY EARNINGS 10,892.17` while its five line items add to 9,642.17 — off by exactly the 1,250.00 bonus line, i.e. the bonus was counted twice. Unperturbed, the validator flags that. Fixing the stated total makes it pass, so the flag is caused by the arithmetic, not by the document type. The tolerance edge is real: a $0.50 error slips through, $1.50 is caught. As a contrast input, `appraisal_informal_sqft.txt` in `extract-run.txt` shows `"consistent": true` because it has no line-itemised total at all.

---

### System 3 — multi-source synthesis

 "78%" in its statement). Exact change: `03-supply-chain/perturbation-audit.diff`.
 `03-supply-chain/investigation-run.txt` / `briefing.md`.
- **What I predicted:** (1) the run finishes, logistics-only metrics land in Incomplete, and the on-time conflict can no longer be shown. (2) with both sources agreeing, on-time delivery leaves Contested, becomes corroborated, and the ESCALATE disappears flag proving "contested" is driven by the values, not by the metric name. 
- **What actually happened (paste the key output line):**
  - Baseline: `## Contested` → `### on_time_delivery_rate  _[2 sources, ESCALATE` with percent `95.0 supplier_audit (as of 2026-04-10)` and percent `78.0 logistics (as of 2026-04-05)`.  conflicting]_  
  - (1) Timeout: `> Sources unavailable: logistics unavailable (timeout)`; Incomplete gains `### late_shipment_count  _[missing source: timeout reading logistics]_`; `average_lead_time_days` drops from `[corroborated across 2 sources]` to `[single source only]`; and `### on_time_delivery_rate  _[single source only]_` now sits under **Well-Established** showing only supplier's 95.0  the `## Contested` is empty.
  - (2) Edited audit: `### on_time_delivery_rate  _[corroborated across 2 sources]_` under Well-Established, `78.0 percent — supplier_audit (as of 2026-04-10)` / `78.0 percent — logistics (as of 2026-04-05)`; no ESCALATE; `## Contested` empty.
- **How this differs from the unperturbed run:** Unperturbed, the 95 vs 78 disagreement is surfaced, attributed, dated and escalated. With the audit edited to agree, the same metric is corroborated and not escalated, so the classification follows the evidence. The timeout run completes instead of aborting and names the dead source — but it also shows the limit of graceful degradation: when the dissenting source goes dark, the supplier's optimistic 95% is presented as the only value. The only warnings are the `[single source only]` tag and the `Sources unavailable` banner, so a reader who skims section headings would miss that a known conflict was hidden.
