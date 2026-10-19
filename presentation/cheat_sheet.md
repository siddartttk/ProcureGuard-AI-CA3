# Demonstration quick reference

Team: Rishi Dwivedi and Siddarth Singh Kushwah. End on slide 8; the exported deck contains exactly eight slides, with no hidden backups.

- PG103: two gaps. The offline planner obtains the amendment then the receipt. Refresh and reopen the case to show the same saved run without repeating tools.
- PG104: receipt unavailable. Record request_recheck, make the delayed fictional receipt available, rerun and compare the revisions.
- PG105 / PG105B: two distinct submissions consume the same capacity. Reject PG105B with a rationale, then investigate PG105 again. Explicitly resubmit PG105B afterward to restore this demo branch.
- PG106: changed source document fails the pinned hash; held.
- PG107: approved prices 120 and 130 conflict; held.
- PG108: a 0.01 unit difference becomes a 10,000 total difference; held.
- PG109: approved vendor-master evidence resolves the bank change without editing the invoice.
- PG110: no receipt exists; the required evidence and next owner remain visible.

Default mode uses a deterministic mock planner and needs no model. Optional local-model mode was genuinely executed on four cases: five model selections, zero fallback. Its sequence can differ; the recorded PG103 run retrieved the receipt before the amendment. Use the saved trace when presenting those measured results.

The final run passed 172 tests and 44 operational checks. The 25 same-author frozen development cases produced 19 / 23 / 25 correct decisions across single-invoice, history and history-plus-critic workflows, with 6 / 2 / 0 incorrect-ready recommendations. Do not call these field accuracy or independent unseen evaluation. Read current reports if rerunning changes the results.

Single-line INR scope; no PDF/OCR ingestion, tax or settlement workflow. No payment is executed. Reviewer roles and source adapters are fictional demonstrations.
