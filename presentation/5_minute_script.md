# Team presentation: target 4 minutes 45 seconds

Rishi Dwivedi: 0:00-1:50. Siddarth Singh Kushwah: 1:50-4:45. Keep 15 seconds for navigation. The final deck contains exactly eight visible slides. Detailed architecture and policy documents support questions separately. Rehearse; the written schedule is not a measured delivery time.

| Time | Speaker / slide | Action and speaking point |
|---|---|---|
| 0:00-0:15 | Rishi / 1 | Introduce both names and domain. ProcureGuard retrieves evidence for invoice exceptions and returns a recommendation to a human. |
| 0:15-0:45 | Rishi / 2 | Explain the current process and owners. A mismatch still leaves procurement and receiving with an investigation. Three-way matching is established; our project focuses on the next evidence step. |
| 0:45-1:10 | Rishi / 3 | PG103: ten units billed at 120, PO says 100 and receipt is missing. An approved amendment alone cannot resolve delivery. |
| 1:10-1:50 | Rishi / 4 | Trace mandatory checks, independent critic, planner, evidence validation, snapshot update and reassessment. Three-tool budget. Default mock and optional local model. Arithmetic remains deterministic. Hand over to Siddarth. |
| 1:50-2:30 | Siddarth / 5 and app | Open PG103, Run investigation, Agent trace, then Evidence provenance. Show the different tool choices after new observations. Keep offline mode for predictable pacing; show the recorded real local-model request separately if asked. |
| 2:30-2:45 | Siddarth / app | Refresh, reopen Investigate a case and show the restored packet with the same run ID and no repeated lookups. |
| 2:45-3:10 | Siddarth / app | PG105 is held. Select PG105B and record a rejected/cancelled classification with rationale. Return to PG105 and re-investigate: removing an inactive commitment releases capacity. Rejected PG105B itself stays held. |
| 3:10-3:40 | Siddarth / 6 | Explain lifecycle-aware allocation, tampered-source rejection and conflicting amendments. PG106 is the optional short negative demo. |
| 3:40-4:15 | Siddarth / 7 | Read the actual test count and 25-case challenge comparison. The three modes agreed on 19, 23 and 25 cases. Two deliberate matcher omissions show critic containment. Four real local-model scenarios were also executed. These are development results, not field accuracy. |
| 4:15-4:45 | Siddarth / 8 | State implemented controls, simulated sources/identity and future ERP/signed approval/multi-line work. Close: evidence-backed recommendation, human-owned decision. |

## Before presenting

Run START_DEMO.cmd in advance. Audit the dashboard. Choose Offline mock planner, budget 3, and PG103. Ensure PG105B is submitted before rehearsing its lifecycle branch; explicitly resubmit it with a rationale if a previous rehearsal cancelled/rejected it. Saved history survives UI reset. Keep slide 5 and the app ready to switch. Do not install dependencies or download a model during the presentation.

## Saved-evidence fallback

If the app fails, use slide 5 and docs/screenshots/03_adaptive_plan.png with reports/investigation_packets.json. Say these are recorded outputs of an actual run. Do not describe the screenshot as live. Never claim the optional Ollama path ran unless you have run it yourself and show its mode/fallback trace.
