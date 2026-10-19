# Viva guide: both members should answer these

**Why this domain?** Invoice review combines distributed evidence, repeatable numerical checks and clear escalation owners. We can demonstrate a business workflow without real financial data.

**What is agentic here?** The controller observes unresolved findings, selects an eligible evidence tool, executes it, incorporates verified observations, changes the next action and stops safely. PG103 demonstrates two different lookups selected from successive states. A free-text chatbot is not the interface.

**Is there AI if no model is installed?** Default mode is explicitly a deterministic mock planning model, which the brief permits. Optional Ollama provides local language-model action selection through the same constrained contract. We do not claim learned intelligence or live-model results for mock execution.

**What does the LLM control?** Only selection among currently eligible evidence lookups and a brief action summary. It cannot change invoices, calculate authoritative results, bypass the critic, add arbitrary tools or execute payments.

**Why multiple roles?** They separate evidence retrieval, accounting computation, independent verification and handoff contracts. We can corrupt a matching tool and show that the critic catches it. This is educational and maintainable separation, not proof that six components beat one well-designed service.

**What is innovative?** Within this PoC, the differentiator is resolving exceptions with scoped authoritative evidence and showing exactly why the recommendation changed. We do not claim three-way matching or invoice automation is new to industry.

**Why does the critic matter?** It independently recomputes comparisons, so omitted or altered findings cannot silently pass. It shares schema, policy and source data, so a consistently wrong policy or falsified trusted source can still fool both.

**Can the same receipt support two invoices?** Submitted/recorded commitments are grouped by vendor, PO and item. Identical duplicate copies count as one obligation; conflicting duplicates block confidence. Rejected, cancelled, duplicate and superseded submissions are excluded. Active quantities must fit both PO and GRN capacity. Credit notes and settlement accounting remain future scope.

**How did you fix tolerance accumulation?** A tolerated unit-price difference also has an INR 1.00 line-exposure guard. The one-million-unit example is now held despite a unit difference of only INR 0.01. These are illustrative policy assumptions.

**Are hashes digital signatures?** No. The local manifest is a trusted demo boundary. A hash mismatch detects changed content against it; source role/date/scope checks validate the simulated authority contract. Real deployments need authenticated signed upstream sources and external audit anchoring.

**What happens on conflicting amendments?** Neither is applied. The evidence gate marks verification unresolved and produces a hold for human resolution.

**Can document text inject instructions?** Only structured allowlisted fields are used; the model receives finding codes and tool goals, not raw documents. Free-text notes are inert. Tests include an instruction-bearing note and invalid model actions. This is a limited defense for this interface, not a universal prompt-injection immunity claim.

**How does a recheck work?** A reviewer records request_recheck with a rationale and expected revision. When new evidence becomes available, a new investigation reruns from original records and saves a later revision. It does not resume a hidden model thought process or automatically contact a supplier.

**What if two tabs save?** BEGIN IMMEDIATE serialises SQLite writes; an expected revision check rejects stale state. Idempotency keys reject a reused request with different content. Reviews also advance revisions.

**Are demo roles real authentication?** No. Reviewer and observer permissions are checked in code, but identities are selectable. Production identity needs SSO or another authenticated service.

**What do the results prove?** The known synthetic scenarios follow their declared outcomes; accounting and evidence controls pass automated tests. A baseline without evidence cannot resolve the same cases. We have not measured field accuracy, real reviewer time saved or LLM superiority.

**What is the most important limitation?** Trusted sources and identities are simulated, and records are single-line INR without tax/credit-note lifecycle. This is an executable PoC using industry engineering patterns, not a production-certified finance system.

**What would you deploy next?** Read-only authenticated ERP/warehouse adapters, signed upstream approval checks, a real invoice settlement lifecycle, durable externally anchored audit storage, production identity, and independently authored field evaluation before any operational use.

**Did you actually run a language model?** Yes. The installed qwen2.5-coder:7b model completed four known synthetic cases, making five tool selections with no fallback. The real requests, responses and model metadata are in reports/live_planner_run.json. This demonstrates execution, not superiority.

**What happens after refreshing the browser?** The UI retrieves the saved packet and current case revision from SQLite when its source hash matches the current records. It preserves the run ID and does not rerun evidence tools.

**What if another tab changes the lifecycle?** The app refreshes the persisted lifecycle overlay on every render. A changed snapshot clears cached recommendations and requires a new audit. Stale classification and review actions are rejected.

**Does recorded mean paid?** No. It means that the invoice is an active procurement commitment for capacity accounting. Recommendation, procurement lifecycle and payment authorisation are separate concepts. No payment function exists.

**How can a rejected invoice become active again?** A simulated reviewer explicitly resubmits it with a rationale. The change is logged and invalidates earlier recommendations. There is no silent reactivation.

**Why require a replacement for duplicate/superseded status?** Otherwise an operator could remove capacity without identifying the obligation that remains active. The replacement must be a different active invoice for the same supplier, PO and item; duplicate classification also requires the same invoice number.

**What does the frozen challenge prove?** It checks additional fixed scenarios whose labels were frozen before v3 changes. It was authored by the same assistant, so it is a development challenge, not independently held-out or field data.

**Why are two challenge cases deliberately corrupted?** They omit amount-tool findings. The historical producer baseline can incorrectly return ready, while the critic recomputes from originals and blocks it. Four interventions mean two verification attempts for each of two faults.

**What does an incorrect-ready count mean?** A case expected to require review or missing evidence instead receives a ready recommendation. The frozen comparison separately reports these misses and false holds/gaps. It does not measure actual payment losses.

**Can changing local metadata evade integrity checks?** Isolated changes to case status, run content or lifecycle rows are detected against logged hashes and events. A sufficiently privileged person could rewrite the entire local trusted boundary. External signatures and retention controls are future work.
