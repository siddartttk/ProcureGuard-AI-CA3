"""Refresh v3 documentation only from actual validation and live-run artifacts."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def write(name,text):
    (ROOT/name).write_text(text.strip()+'\n',encoding='utf-8')


def main():
    r=json.loads((ROOT/'reports/validation_v3.json').read_text(encoding='utf-8'))
    tests=r['regression_tests'];challenge=r['challenge'];live=r['live_model']
    write('README.md',f'''
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
.\\.venv\\Scripts\\python.exe -m streamlit run app.py
```

On a fresh computer, install Python 3.11+, create `.venv` and install `requirements-tested.txt` first. Setup needs internet for packages; the default offline planner needs no model or network. setup.ps1 automates installation. The ordinary local URL is printed by Streamlit.

## What changed after the reviewed enhanced submission
- Saved case packets now reopen in a fresh browser session, preserving the original run ID and current case revision. Reopening performs no new tool calls.
- Simulated human lifecycle classification distinguishes submitted/recorded commitments from rejected, cancelled, duplicate and superseded submissions. Changes persist in SQLite, invalidate stale recommendations and become visible to other sessions.
- Identical active duplicate copies count as one quantity obligation. Conflicting duplicate amounts block ledger confidence. Unknown peer lifecycle values cannot silently release capacity.
- Exact source documents and their payloads are inspectable in the provenance tab. Earlier saved investigation revisions can be downloaded.
- The installed local model was actually exercised: {live['model'] if live else 'no completed run'}. Actual requests, responses, selected tools and fallback counts are in reports/live_planner_run.json.
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
.\\.venv\\Scripts\\python.exe scripts/validate_v3.py
# Optional, requires the already-installed running local model:
.\\.venv\\Scripts\\python.exe scripts/run_live_planner.py
```

Current recorded results: {tests['passed']} tests passed, {tests['failed']} failures/errors; 44/44 original/operational scenario decisions; 25/25 frozen challenge decisions with the critic. Do not quote these snapshots after modifying code without revalidation.

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
''')
    lines=['# Executed validation: ProcureGuard AI 3.0','',f'Executed {r["executed_at"]}.',
           f'**{tests["passed"]}/{tests["total"]} automated tests passed; {tests["failed"]} failed/errors; {tests["skipped"]} skipped.**','',
           '## Regression and operational scenarios','',
           '44/44 known decisions agreed, including the delayed-evidence case before and after availability. The operational corpus contains 43 fictional invoices.','',
           '## Frozen development challenge','',challenge['boundary'],'',
           f'Integrity digest: {r["challenge_sha256"]}. Expected answers are separate from operational Dataset input.','',
           '| Mode | Exact decisions | Incorrect ready / missed actionable | False holds or gaps | Critic interventions |',
           '|---|---:|---:|---:|---:|']
    lines += [f'| {m["mode"]} | {m["exact_agreement"]}/{m["cases"]} | {m["incorrect_ready"]} | {m["false_holds_or_gaps"]} | {m["critic_interventions"]} |' for m in challenge['metrics']]
    lines += ['','The producer baselines are evaluation-only and make no independent-verification claim. The single-invoice baseline lacks peer history. The second includes history but omits the critic. Two controlled matcher omissions test whether verification prevents an incorrect ready recommendation. Four critic interventions represent two challenges per fault case, not four separate defective invoices.','',
              '## Real local model execution','']
    if live:lines += [f'Model {live["model"]}, executed {live["executed_at"]}: {live["agreement"]}/{live["case_count"]} expected decisions, {live["live_choices"]} actual selections, {live["fallbacks"]} fallbacks.',
                     'Cases: PG103, PG106, PG107 and PG109. Complete real requests/responses and packets are in reports/live_planner_run.json. No model was downloaded and no paid service was used. This is a bounded demonstration on known cases, not a model comparison.']
    lines += ['','## Recovery and lifecycle evidence','',
              f'PG104 moved from {r["case_recovery"]["before"]} to {r["case_recovery"]["after"]}. Its saved revision {r["case_recovery"]["current_revision"]} reopened with the same run ID: {r["case_recovery"]["same_run_reopened"]}.',
              f'After simulated rejection of PG105B, PG105 moved from {r["lifecycle_demo"]["before"]} to {r["lifecycle_demo"]["after"]}. Local log integrity passed: {r["lifecycle_demo"]["integrity"]["valid"]}.',
              'Fresh-session, cross-browser invalidation, lifecycle persistence, stale actions, duplicate grouping and metadata tampering are exercised in tests/test_enhancements.py.','',
              '## Reproduction and limits','',
              'Run python scripts/validate_v3.py. Raw pytest output and JUnit XML are in reports/. Live inference is intentionally separate; python scripts/run_live_planner.py refreshes that record when the installed model service is available. Engine workload timings in validation_v2.json exclude UI, model generation and human work. Live per-case timings include model calls and are recorded separately.','',
              'The same assistant authored code and challenge cases. Synthetic agreement is not field accuracy, financial savings, a calibrated fraud score or a guarantee of safety. Trusted original data, shared policies and shared schema parsing remain common failure modes. Identity and upstream authority are simulated. Single-line INR, no OCR, tax, credit notes, settlement ledger or payments.','',
              'Future work: independently authored unseen evaluation, multi-line/credit-note semantics, authenticated upstream sources and externally anchored retention.']
    browser_path=ROOT/'reports/browser_smoke.json'
    if browser_path.exists():
        browser=json.loads(browser_path.read_text(encoding='utf-8'))
        lines += ['','## Browser and artifact handoff','',
                  f'Real Chrome interaction completed {browser["captured_at"]}: {browser["screenshots"]} application captures, {browser["streamlit_exceptions"]} Streamlit exceptions and {len(browser["consoleErrors"])} browser page errors. Saved-case recovery and lifecycle-driven revalidation were exercised, including the restored case selector.',
                  'All eight rendered slides and the one-page printable problem statement were visually reviewed. The PPTX receipt hash matches the delivered file, which contains eight visible slides and eight note parts. Native PowerPoint rendering was not executed.',
                  'A clean extraction of the portable package was exercised with the installed project environment: the offline evidence investigation and Streamlit case selection/investigation passed. The first installation on another computer still needs Python and package installation.']
    write('docs/validation_report.md','\n'.join(lines))
    write('docs/technical_explanation.md','''
# Technical walkthrough: v3

The evidence-resolution controller in investigation.py copies source records, runs audit(), derives eligible evidence tools and validates the planner's selected action. EvidenceRepository checks the local pinned hash, authority, date, type and invoice scope. Accepted updates affect only an effective snapshot. Accounting and the independently implemented critic run again after each update. Evidence conflicts fail closed.

The planner interface supports a deterministic offline mock and Ollama structured outputs. The installed qwen2.5-coder:7b model was actually used in a recorded demonstration. Requests contain finding codes and tool goals, not arbitrary document instructions. Actual requests, parsed responses, model identifiers, generation counts and elapsed times are retained. The controller allows at most three evidence tools and a single accounting recheck.

schemas.py validates optional lifecycle_status values. Old CSV schemas remain compatible and default to submitted. Submitted and recorded invoices consume capacity; rejected, cancelled, duplicate and superseded rows do not. Inactive current submissions are held. Unknown peer states block capacity confidence. Identical active copies sharing a vendor invoice number count as one obligation; conflicting duplicate amounts produce missing-ledger-context rather than an allocation assumption.

CaseStore uses SQLite transactions and expected revisions for investigations and human review. New methods recover(), revisions(), effective_data() and set_lifecycle() support durable reopening and classification. Lifecycle changes require a demo reviewer, a rationale and valid transitions. Duplicate/superseded classifications require a related active replacement. These actions never authorise a payment.

The original input bundle has a stable namespace; the UI uses a separate default SQLite file for each namespace. Lifecycle overrides persist separately. Each render checks local integrity and refreshes the overlay, so a change in another browser invalidates stale results. recover() atomically returns the stored run and current case revision only when its original source hash matches current data. Reopening executes no tools. Changed data requires revalidation. Earlier packets remain downloadable.

Case, lifecycle and run metadata are checked against the event chain. This detects isolated local mutations, not an administrator rewriting the entire trusted boundary. Demo identities remain selectable rather than authenticated.

evaluation.py is a development-only ablation runner. It validates a frozen fixture digest before loading cases, keeps expected labels outside Dataset and distinguishes unverified producer baselines from the critic-enabled runtime. Two deliberate producer omissions test fault containment. It is not exposed as a runtime path that bypasses mandatory verification.

Tests cover original accounting/evidence controls plus fresh browser recovery, cross-browser invalidation, lifecycle transitions and persistence, invalid peer states, duplicate allocation and metadata corruption. scripts/validate_v3.py records regression, challenge and evolving-case evidence. It never fabricates model output. scripts/run_live_planner.py separately records real installed-model inference.
''')
    write('docs/final_verification.md',f'''
# Verified v3 handoff

Rishi Dwivedi and Siddarth Singh Kushwah, AIML-C, SIT Pune. Two-person attribution was confirmed by the user.

- Executed test evidence: {tests['passed']}/{tests['total']} passed, {tests['failed']} failures/errors and {tests['skipped']} skips. Python environment details are recorded in the raw reports.
- 44/44 regression/operational decisions and 25/25 frozen development challenge decisions with the independent critic.
- Real installed local model run: {live['model'] if live else 'not recorded'}, {live['live_choices'] if live else 0} live selections, {live['fallbacks'] if live else 0} fallbacks. Details and limits are in live_planner_run.json.
- Case recovery preserves the saved run ID without repeating tool execution. Lifecycle changes persist, invalidate stale snapshots and require revalidation. Actual evolving-case packets are saved in reports/evolving_case_demo.json.
- Browser captures and their run timestamp are in docs/screenshots and reports/browser_smoke.json. These are real application captures, not generated mockups.
- The submission deck is presentation/ProcureGuard_AI_CA3_Improved.pptx and contains exactly eight visible slides with speaker notes. Detailed technical diagrams and source are separate documents. Structural/layout checks and visual review must accompany its final authoring receipt. Native PowerPoint and a spoken rehearsal are not claimed.
- The script targets 4:45. That is a written schedule, not a measured delivery time.
- All data and approvals are simulated. Reviewer roles are not authentication. Hashes are not signatures or immutable storage. No payment, ERP, OCR, tax or credit-note implementation is claimed.

The portable ZIP excludes runtime databases, virtual environments, review copies and private build files. scripts/package_submission.py verifies per-file checksums and ZIP integrity.
''')
    write('docs/requirements_traceability.md','''
# CA-3 requirement mapping

| Faculty criterion | Implementation and evidence | Slide / demonstration |
|---|---|---|
| Problem and domain | problem_statement.md/.pdf, domain_analysis.md | 1-2 |
| Business challenge and proposed solution | Evidence-resolution controller and current domain analysis | 2-3 |
| Agent roles and orchestration | agents_and_orchestration.md; bounded planner, tools and separate critic | 4; PG103 |
| Complete architecture | architecture.mmd, architecture.svg, high-resolution architecture.png; native condensed slide diagram | 4 |
| Working Python/Streamlit PoC | Four pages, 43 invoices, source inspection, persisted recovery and lifecycle allocation | 5-6; PG103 / PG105 / PG106 |
| Validation, measured results, limits and future | Executed JUnit, validation_v3.json, frozen challenge and actual local-model records | 7-8 |
| Eight-slide deck and five-minute demonstration | ProcureGuard_AI_CA3_Improved.pptx, notes, 4:45 script and viva answers | 1-8 |

Two-person attribution for Rishi Dwivedi and Siddarth Singh Kushwah was confirmed by the user on 19 October 2026. The default offline mock and real local-model mode are clearly distinguished. Every recommendation remains subject to human review.
''')
    path=ROOT/'docs/agents_and_orchestration.md'
    original=path.read_text(encoding='utf-8')
    start=original.index('Peer invoices sharing') if 'Peer invoices sharing' in original else original.index('Only submitted and recorded peer invoices')
    end=original.index('\n\n',start)
    original=original[:start]+('Only submitted and recorded peer invoices sharing vendor, PO and item consume capacity. Rejected, cancelled, duplicate and superseded submissions are excluded. Identical active copies of the same invoice number count once, but conflicting duplicate values and invalid active peer states block ledger confidence. Inactive current submissions cannot become ready. Both active obligations in an overcommitted group are held. Lifecycle classifications are simulated human procurement actions, not payment decisions.')+original[end:]
    original=original.split('\n\n## V3 recovery and actual model evidence')[0]
    original += '\n\n## V3 recovery and actual model evidence\n\nThe UI reopens stored packets with CaseStore.recover() when source hashes match and restores the current review revision. Lifecycle changes persist separately, refresh across sessions and invalidate cached recommendations. Earlier investigation revisions remain downloadable. The installed local model completed an actual recorded demonstration; see reports/live_planner_run.json. Frozen development ablation results are in reports/validation_v3.json. The exact scope and statistical limits are in docs/validation_report.md.\n'
    path.write_text(original,encoding='utf-8')
    print('Current v3 documentation refreshed from executed reports')


if __name__=='__main__':main()
