# Domain and business process

The selected domain is procurement and accounts-payable operations. Stakeholders are accounts payable (case owner), procurement (commercial authority), receiving (delivery evidence), a finance controller (vendor-master changes) and a finance reviewer (final follow-up). This is a meaningful domain because facts are distributed across owners while decisions require consistent numerical and evidence checks.

## Existing and proposed process

Existing illustrative process: receive invoice, locate PO and receipt, compare values, identify a discrepancy, contact the appropriate owner, obtain evidence, repeat checks and document the decision. Three-way matching is established functionality; this project does not claim to invent it.

Proposed process: mandatory audit, independently verify findings, choose a permitted evidence lookup, validate its authority and scope, apply the source update to a snapshot, reassess the remaining gap, then produce a versioned recommendation and next action. A human owns the review. Missing or conflicting sources cannot be assumed correct.

## Baseline and value

The baseline runs the same accounting checker on the original records. The evidence workflow can resolve a case only when a trusted simulated source supplies a valid record. This isolates access to evidence as the difference. Known synthetic outcomes demonstrate working exception resolution but do not establish superiority over an integrated ERP, LLM planning quality, production fraud detection, or time saved by a real reviewer.

## Limits

Submitted and recorded invoices consume capacity. Rejected, cancelled, duplicate and superseded submissions do not; changing a classification requires a rationale and invalidates existing recommendations. Identical active copies consume one obligation, while conflicting copies block a ready recommendation. This is an invoice-submission lifecycle, not a payment or settlement ledger. Single-line INR records, whole positive quantities and simple illustrative tolerances are supported. Sources, approval metadata and selected demo identities are fictional.

Source: [Microsoft Learn: Accounts payable invoice matching](https://learn.microsoft.com/en-us/dynamics365/finance/accounts-payable/accounts-payable-invoice-matching).
