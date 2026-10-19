# Agent responsibilities and orchestration

## Specialist roles

| Role | Implementation | Responsibility and contract |
|---|---|---|
| Planner | agents/planner.py, planning.py, investigation.py | Mandatory audit routing plus observation-driven choice of an eligible evidence tool. Inputs: findings, attempted tools and remaining budget. Output: a validated tool name and a brief action summary. |
| Matching | agents/matching.py, tools.py | Schema, record links, Decimal prices/totals, received quantities and cumulative active commitments. Output: structured findings. |
| Risk assessment | agents/risk.py | Interpret retained mandatory screening evidence and compound severity. Risk tools execute once, not once for screening and again for investigation. |
| Evidence executor/verifier | agents/evidence_agent.py, evidence.py | Fetch a selected synthetic source; validate pinned hash, scope, date, approval and schema; apply scoped updates atomically to a copy. |
| Independent critic | agents/critic.py | Recompute all accounting comparisons separately without calling matching/risk implementations. Shared schema and policy remain common failure modes. |
| Decision coordinator | agents/decision.py, case_store.py | Gate the final recommendation; persist a versioned case and accountable human review. No payment action is present. |

These are six logical specialist roles, not six LLMs or independently deployed services. The planner may use an offline mock or local Ollama. The accounting agents are deterministic.

## Actual control loop

1. Copy the original operational dataset; record its SHA-256 snapshot hash.
2. Run mandatory matching and risk checks and independent critic comparison.
3. Derive the eligible evidence tools from verified findings and the untried-tool set.
4. Ask the planning model for one tool. Validate its JSON contract and allowlist. Invalid/unavailable models use a visible deterministic fallback.
5. The evidence agent queries only that source, checks authority and scope, and produces accepted, not_found, rejected or conflict.
6. Accepted records update a candidate snapshot atomically. Re-run mandatory checks and critic. The next tool depends on the remaining gap.
7. Stop when no useful tool remains, the planner stops, verification fails, evidence conflicts, or the three-lookup budget expires. Each tool is attempted at most once per investigation. Accounting contradictions allow at most one recheck.
8. Generate a recommendation, required evidence and next owner. Save source and effective snapshots, accepted records, tool observations and final findings in a transactional case revision.

## Example PG103

Initial: PO INR 100 per unit; invoice INR 120; no receipt. The planner chooses amendment_lookup, obtains a procurement-approved INR 120 amendment and reassesses. Price is now reconciled but MISSING_GRN remains. It then chooses warehouse_lookup and obtains 10 received units. Independent verification passes and the case is ready for human review. The original invoice and source CSVs are unchanged.

## Trust boundaries

The trusted local manifest pins expected document bytes. Structured documents must match the selected source role, approval status, invoice vendor/order/item and effective date. Free-text notes are inert data. Multiple contradictory commercial/master updates fail closed. Receipt application is idempotent by receipt ID and rejects an ID with conflicting content.

A model cannot change invoices, set numerical outcomes, choose an ineligible tool, exceed the budget or execute a payment. The Ollama call uses a fixed loopback endpoint with a bounded JSON response and timeout. A stopped or failed planner cannot silently clear a case.

## Policy PG-2.0

Inclusive price and arithmetic tolerance: INR 0.01. If a unit difference is tolerated, cumulative line exposure is capped at INR 1.00. Quantities have no tolerance. High-value review begins at INR 100,000. Only submitted and recorded peer invoices sharing vendor, PO and item consume capacity. Rejected, cancelled, duplicate and superseded submissions are excluded. Identical active copies of the same invoice number count once, but conflicting duplicate values and invalid active peer states block ledger confidence. Inactive current submissions cannot become ready. Both active obligations in an overcommitted group are held. Lifecycle classifications are simulated human procurement actions, not payment decisions.

Risk weights are illustrative, additive and capped at 100. They are not probabilities. Unresolved verification and rejected/conflicting evidence produce a hold. Otherwise missing/invalid required evidence takes precedence, then review findings, then ready for human review.

## Storage and review

SQLite BEGIN IMMEDIATE transactions serialise writes. Idempotency keys prevent the same request being stored twice; reusing a key with changed content is rejected. Every investigation or review advances the case revision, so a stale browser cannot overwrite a newer state. Review requires an authorised demo role and rationale. Demo role selection is not authentication. Confirming a recommendation is not payment approval.

The event hash chain and snapshot digests detect modification while the trusted chain boundary remains intact. A local administrator could rewrite the entire database or remove a suffix; independent external anchors, production identity and immutable retention are out of scope.

## Agentic scope

The PoC exhibits bounded tool selection, execution, new observations, changing plans, independent validation and stop/escalation behavior. In offline mode the planning policy is deterministic, not learned intelligence. A simpler rules service could implement the same accounting checks. The baseline comparison demonstrates the value of verified evidence acquisition, not a universal benefit from multi-agent complexity.


## V3 recovery and actual model evidence

The UI reopens stored packets with CaseStore.recover() when source hashes match and restores the current review revision. Lifecycle changes persist separately, refresh across sessions and invalidate cached recommendations. Earlier investigation revisions remain downloadable. The installed local model completed an actual recorded demonstration; see reports/live_planner_run.json. Frozen development ablation results are in reports/validation_v3.json. The exact scope and statistical limits are in docs/validation_report.md.
