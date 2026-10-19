"""Observe, choose an evidence tool, verify, reassess and stop within a strict budget."""
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from time import perf_counter
from .orchestrator import audit
from .state import Finding
from .agents.decision import DecisionAgent, READY
from .planning import MockPlannerModel, TOOLS, eligible_tools, validate_choice
from .agents.evidence_agent import EvidenceAgent


@dataclass
class Investigation:
    invoice_id: str
    initial: dict
    final: dict
    steps: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    next_actions: list = field(default_factory=list)
    planner_mode: str = ''
    elapsed_ms: float = 0
    policy_version: str = 'PG-2.0'
    source_snapshot_hash: str = ''
    effective_snapshot_hash: str = ''
    budget: int = 3
    source_snapshot: dict = field(default_factory=dict)
    effective_snapshot: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def snapshot(data):
    return {name: getattr(data, name) for name in ('vendors', 'purchase_orders', 'goods_receipts', 'invoices')}


def snapshot_hash(data):
    import hashlib, json
    return hashlib.sha256(json.dumps(snapshot(data),sort_keys=True,separators=(',', ':')).encode()).hexdigest()


def investigate(data, invoice_id, repository, *, model=None, released=False, budget=3):
    if type(budget) is not int or not 0 <= budget <= 3:
        raise ValueError('Evidence tool budget must be 0 to 3')
    started = perf_counter()
    working = deepcopy(data)
    invoice = working.invoices[invoice_id]
    original_hash = snapshot_hash(data)
    state = audit(working, invoice_id)
    model = model or MockPlannerModel()
    result = Investigation(invoice_id, state.to_dict(), state.to_dict(), planner_mode=model.name,
                           source_snapshot_hash=original_hash, budget=budget, source_snapshot=deepcopy(snapshot(data)))
    attempted = set()
    for index in range(budget):
        allowed = eligible_tools(state, attempted)
        if not allowed or state.recommendation == READY:
            break
        fallback = ''
        try:
            choice = validate_choice(model.choose(state, allowed), allowed)
        except Exception as exc:
            # A model failure cannot bypass checking; fallback is visible in the trace.
            fallback = f'{type(exc).__name__}: planner unavailable or invalid; offline planner used'
            choice = MockPlannerModel().choose(state, allowed)
        tool = choice['tool']
        if tool == 'stop':
            result.steps.append({'step': index+1, 'tool': 'stop', 'summary': choice['summary'],
                                 'status': 'stopped', 'fallback': fallback,
                                 'planner_record':deepcopy(getattr(model,'last_record',{}))})
            break
        attempted.add(tool)
        found, candidate = EvidenceAgent().run(working,invoice_id,tool,repository,released=released)
        step = {'step': index+1, 'tool': tool, 'summary': choice['summary'], 'status': found.status,
                'reason': found.reason, 'fallback': fallback, 'before': state.recommendation,
                'before_codes': [f.code for f in state.findings], 'rejected': found.rejected,
                'evidence_ids': [d['evidence_id'] for d in found.accepted]}
        step['planner_record']=deepcopy(getattr(model,'last_record',{}))
        if found.status == 'accepted':
            try:
                candidate_state = audit(candidate, invoice_id)
                working, invoice = candidate, candidate.invoices[invoice_id]
                result.evidence.extend(found.accepted)
                state = candidate_state
            except (ValueError, KeyError, TypeError) as exc:
                found.status = step['status'] = 'conflict'
                step['reason'] = str(exc)
        if found.status in ('conflict', 'rejected'):
            state.findings.append(Finding('EVIDENCE_CONFLICT', 'review', {'tool': tool, 'reason': step['reason']}))
            # The deterministic critic covers accounting. Evidence rejection is a separate gate.
            state.verified = False
            DecisionAgent().run(state)
        step.update(after=state.recommendation, after_codes=[f.code for f in state.findings])
        result.steps.append(step)
        if found.status in ('conflict', 'rejected'):
            break
    for tool, spec in TOOLS.items():
        codes = sorted(spec['codes'] & {f.code for f in state.findings})
        if codes:
            result.next_actions.append({'owner': spec['owner'], 'required_evidence': spec['need'],
                                        'blocking_codes': codes, 'action': 'Request authoritative evidence; resume the versioned case'})
    other = sorted({f.code for f in state.findings} - set().union(*(s['codes'] for s in TOOLS.values())) - {'COMPOUND_RISK'})
    if other:
        result.next_actions.append({'owner': 'Accounts payable reviewer', 'required_evidence': ', '.join(other),
                                    'blocking_codes': other, 'action': 'Investigate source records; no automatic override'})
    result.final = state.to_dict()
    result.effective_snapshot_hash = snapshot_hash(working)
    result.effective_snapshot = deepcopy(snapshot(working))
    result.elapsed_ms = round((perf_counter()-started)*1000, 3)
    if snapshot_hash(data) != original_hash:
        raise AssertionError('Source records changed during investigation')
    return result
