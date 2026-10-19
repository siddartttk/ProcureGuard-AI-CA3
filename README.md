# ProcureGuard AI 3.0
## Agentic invoice exception resolution with durable case recovery

**Rishi Dwivedi - 24070126152**  
**Siddarth Singh Kushwah - 24070126174**  
AIML-C, SIT Pune. CA3 team submission.

## CA3 submission files

[Private GitHub repository](https://github.com/siddartttk/ProcureGuard-AI-CA3)

- [PowerPoint presentation](presentation/ProcureGuard_AI_CA3_Improved.pptx)
- [Word project report](docs/ProcureGuard_AI_CA3_Report.docx)
- [Application code](procureguard/) and [launch entry point](app.py)
- [Executed validation report](docs/validation_report.md)

This repository is private. Faculty need repository access to review the submitted link.

## Launch
Double-click START_DEMO.cmd, or from this folder:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

On a fresh computer, install Python 3.11+, create `.venv` and install `requirements-tested.txt` first. Setup needs internet for packages; the default offline planner needs no model or network. setup.ps1 automates installation. The ordinary local URL is printed by Streamlit.

## What changed after the reviewed enhanced submission
- Saved case packets now reopen in a fresh browser session, preserving the original run ID and current case revision. Reopening performs no new tool calls.
- Simulated human lifecycle classification distinguishes submitted/recorded commitments from rejected, cancelled, duplicate and superseded submissions. Changes persist in SQLite, invalidate stale recommendations and become visible to other sessions.
- Identical active duplicate copies count as one quantity obligation. Conflicting duplicate amounts block ledger confidence. Unknown peer lifecycle values cannot silently release capacity.
- Exact source documents and their payloads are inspectable in the provenance tab. Earlier saved investigation revisions can be downloaded.
- The installed local model was actually exercised: qwen2.5-coder:7b. Actual requests, responses, selected tools and fallback counts are in reports/live_planner_run.json.
- A frozen 25-case development challenge compares single-invoice checking, historical checking and independent verification. It includes two deliberately corrupted matching-tool cases.

## Five-minute demonstration
1. Audit the 43 fictional invoices in Command center.
2. Investigate PG103. An approved amendment and receipt resolve successive gaps. Inspect the source evidence and actual tool choices.
3. Refresh the browser, reopen Investigate a case and show that PG103 is restored without rerunning tools.
4. PG105 starts held because PG105 and PG105B jointly exceed capacity. Select PG105B, record a justified rejected/cancelled lifecycle classification, then re-investigate PG105. The other commitment can reconcile while the inactive submission remains held.
5. PG106 demonstrates rejection of a changed attachment. Validation lab shows the real tests, frozen challenge and recorded local-model demo.

Restore demo records resets session results but preserves saved case and lifecycle history. To rehearse a different branch, explicitly resubmit an inactive invoice with a rationale. Recording a commitment or confirming a recommendation never approves or executes payment.

## Local language-model mode
Ollama and qwen2.5-coder:7b were already installed on the development computer. No model was downloaded. Start the local Ollama service and choose Ollama local planner in the sidebar. On another computer, a compatible installed model is required. Override the model with PROCUREGUARD_OLLAMA_MODEL before launching. An unavailable model produces a labelled deterministic fallback.

The model chooses only a currently eligible evidence tool. It does not calculate accounting decisions. Maximum three evidence lookups, one accounting recheck, structured outputs, an allowlist and deterministic verification remain mandatory. The real model record describes four known cases, not superiority over a rules implementation.

## Reproduce validation
```powershell
.\.venv\Scripts\python.exe scripts/validate_v3.py
# Optional, requires the already-installed running local model:
.\.venv\Scripts\python.exe scripts/run_live_planner.py
```

Current recorded results: 172 tests passed, 0 failures/errors; 44/44 original/operational scenario decisions; 25/25 frozen challenge decisions with the critic. Do not quote these snapshots after modifying code without revalidation.

## Files for submission
- presentation/ProcureGuard_AI_CA3_Improved.pptx: exactly eight visible slides with notes.
- docs/problem_statement.pdf and academic Markdown documents.
- docs/ProcureGuard_AI_CA3_Report.docx: complete Word project report for CA3.
- docs/architecture.mmd, architecture.svg and architecture.png: editable source and detailed render.
- presentation/5_minute_script.md, cheat_sheet.md and viva_questions.md.
- reports/validation_v3.json, live_planner_run.json, evolving_case_demo.json and pytest-results.xml.
- ProcureGuard_AI_CA3_Improved_Submission.zip: portable source and evidence, excluding local databases and environments.

## Boundaries
All supplier, warehouse, approval and bank records are fictional. Reviewer identity is simulated, not authenticated. Hashes and an event chain detect changes within a trusted local boundary and are not digital signatures or immutable retention. The supported schema remains single-line positive INR records, without tax, PDF/OCR ingestion, credit notes, a settlement ledger or an ERP connection. No payment capability exists.

The 25 challenge cases were frozen before the v3 changes but were authored by the same development assistant. They are development evidence, not an independently held-out or field benchmark. Two cases intentionally corrupt the matcher to demonstrate critic intervention.

## Artifact rebuilds
scripts/build_docs_v3.py refreshes current documentation from executed reports. scripts/build_deck.mjs authors the current deck with the Codex bundled artifact runtime. scripts/render_architecture.mjs renders Mermaid with the locally prepared development renderer. Those artifact tools are not needed to run Streamlit. The original pre-enhancement project is backed up privately under build/backups/.
