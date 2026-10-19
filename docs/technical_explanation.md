# Technical walkthrough: v3

The evidence-resolution controller in investigation.py copies source records, runs audit(), derives eligible evidence tools and validates the planner's selected action. EvidenceRepository checks the local pinned hash, authority, date, type and invoice scope. Accepted updates affect only an effective snapshot. Accounting and the independently implemented critic run again after each update. Evidence conflicts fail closed.

The planner interface supports a deterministic offline mock and Ollama structured outputs. The installed qwen2.5-coder:7b model was actually used in a recorded demonstration. Requests contain finding codes and tool goals, not arbitrary document instructions. Actual requests, parsed responses, model identifiers, generation counts and elapsed times are retained. The controller allows at most three evidence tools and a single accounting recheck.

schemas.py validates optional lifecycle_status values. Old CSV schemas remain compatible and default to submitted. Submitted and recorded invoices consume capacity; rejected, cancelled, duplicate and superseded rows do not. Inactive current submissions are held. Unknown peer states block capacity confidence. Identical active copies sharing a vendor invoice number count as one obligation; conflicting duplicate amounts produce missing-ledger-context rather than an allocation assumption.

CaseStore uses SQLite transactions and expected revisions for investigations and human review. New methods recover(), revisions(), effective_data() and set_lifecycle() support durable reopening and classification. Lifecycle changes require a demo reviewer, a rationale and valid transitions. Duplicate/superseded classifications require a related active replacement. These actions never authorise a payment.

The original input bundle has a stable namespace; the UI uses a separate default SQLite file for each namespace. Lifecycle overrides persist separately. Each render checks local integrity and refreshes the overlay, so a change in another browser invalidates stale results. recover() atomically returns the stored run and current case revision only when its original source hash matches current data. Reopening executes no tools. Changed data requires revalidation. Earlier packets remain downloadable.

Case, lifecycle and run metadata are checked against the event chain. This detects isolated local mutations, not an administrator rewriting the entire trusted boundary. Demo identities remain selectable rather than authenticated.

evaluation.py is a development-only ablation runner. It validates a frozen fixture digest before loading cases, keeps expected labels outside Dataset and distinguishes unverified producer baselines from the critic-enabled runtime. Two deliberate producer omissions test fault containment. It is not exposed as a runtime path that bypasses mandatory verification.

Tests cover original accounting/evidence controls plus fresh browser recovery, cross-browser invalidation, lifecycle transitions and persistence, invalid peer states, duplicate allocation and metadata corruption. scripts/validate_v3.py records regression, challenge and evolving-case evidence. It never fabricates model output. scripts/run_live_planner.py separately records real installed-model inference.
