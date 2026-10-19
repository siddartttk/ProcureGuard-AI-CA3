# Executed validation: ProcureGuard AI 3.0

Executed 2026-10-19T17:13:52.325255+00:00.
**172/172 automated tests passed; 0 failed/errors; 0 skipped.**

## Regression and operational scenarios

44/44 known decisions agreed, including the delayed-evidence case before and after availability. The operational corpus contains 43 fictional invoices.

## Frozen development challenge

Frozen development challenge authored by the same assistant before v3 changes. Two cases deliberately corrupt the matcher. Not independently held-out or field data. Unverified producer baselines are evaluation-only.

Integrity digest: 99ccfae6b901dd804cc1cf5a3074d08fd87dbdf627e1f53ae3b069ff4d553443. Expected answers are separate from operational Dataset input.

| Mode | Exact decisions | Incorrect ready / missed actionable | False holds or gaps | Critic interventions |
|---|---:|---:|---:|---:|
| Single-invoice producer baseline | 19/25 | 6 | 0 | 0 |
| Historical producer baseline | 23/25 | 2 | 0 | 0 |
| Historical audit with critic | 25/25 | 0 | 0 | 4 |

The producer baselines are evaluation-only and make no independent-verification claim. The single-invoice baseline lacks peer history. The second includes history but omits the critic. Two controlled matcher omissions test whether verification prevents an incorrect ready recommendation. Four critic interventions represent two challenges per fault case, not four separate defective invoices.

## Real local model execution

Model qwen2.5-coder:7b, executed 2026-10-19T17:03:02.543642+00:00: 4/4 expected decisions, 5 actual selections, 0 fallbacks.
Cases: PG103, PG106, PG107 and PG109. Complete real requests/responses and packets are in reports/live_planner_run.json. No model was downloaded and no paid service was used. This is a bounded demonstration on known cases, not a model comparison.

## Recovery and lifecycle evidence

PG104 moved from INSUFFICIENT_DATA to READY_FOR_HUMAN_APPROVAL. Its saved revision 3 reopened with the same run ID: True.
After simulated rejection of PG105B, PG105 moved from HOLD_FOR_REVIEW to READY_FOR_HUMAN_APPROVAL. Local log integrity passed: True.
Fresh-session, cross-browser invalidation, lifecycle persistence, stale actions, duplicate grouping and metadata tampering are exercised in tests/test_enhancements.py.

## Reproduction and limits

Run python scripts/validate_v3.py. Raw pytest output and JUnit XML are in reports/. Live inference is intentionally separate; python scripts/run_live_planner.py refreshes that record when the installed model service is available. Engine workload timings in validation_v2.json exclude UI, model generation and human work. Live per-case timings include model calls and are recorded separately.

The same assistant authored code and challenge cases. Synthetic agreement is not field accuracy, financial savings, a calibrated fraud score or a guarantee of safety. Trusted original data, shared policies and shared schema parsing remain common failure modes. Identity and upstream authority are simulated. Single-line INR, no OCR, tax, credit notes, settlement ledger or payments.

Future work: independently authored unseen evaluation, multi-line/credit-note semantics, authenticated upstream sources and externally anchored retention.

## Browser and artifact handoff

Real Chrome interaction completed 2026-10-19T17:16:28.631Z: 10 application captures, 0 Streamlit exceptions and 0 browser page errors. Saved-case recovery and lifecycle-driven revalidation were exercised, including the restored case selector.
All eight rendered slides and the one-page printable problem statement were visually reviewed. The PPTX receipt hash matches the delivered file, which contains eight visible slides and eight note parts. Native PowerPoint rendering was not executed.
A clean extraction of the portable package was exercised with the installed project environment: the offline evidence investigation and Streamlit case selection/investigation passed. The first installation on another computer still needs Python and package installation.
