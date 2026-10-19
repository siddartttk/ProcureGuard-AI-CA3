"""Bounded state-machine execution with real trace events, no generated reasoning."""
from copy import deepcopy
from time import perf_counter
from .policies import Policy
from .state import AuditState, Finding
from .agents.planner import PlannerAgent
from .agents.matching import MatchingAgent
from .agents.risk import RiskAgent
from .agents.critic import CriticAgent
from .agents.decision import DecisionAgent


def audit(data, invoice_id: str, policy: Policy | None = None, *, demo_fault: str = 'none') -> AuditState:
    """Audit one invoice. Fault injection only alters intermediate findings, never originals."""
    if invoice_id not in data.invoices:
        raise ValueError(f'Unknown invoice ID: {invoice_id}')
    if demo_fault not in ('none', 'once', 'persistent'):
        raise ValueError('Unknown fault mode')
    start = perf_counter()
    policy = policy or Policy()
    data = deepcopy(data)  # A stable per-run snapshot for matcher and independent critic.
    invoice = data.invoices[invoice_id]
    state = AuditState(invoice_id=invoice_id, demo_fault=demo_fault)
    planner, matcher, risk, critic, decision = PlannerAgent(), MatchingAgent(), RiskAgent(), CriticAgent(), DecisionAgent()
    planner.plan(state, data, invoice, policy)
    try:
        while True:
            state.findings = []
            matcher.run(state, data, invoice, policy)
            selected = planner.route(state, data, invoice, policy)
            if selected:
                risk.run(state, data, invoice, policy, selected)
            if demo_fault == 'persistent' or demo_fault == 'once' and state.attempts == 0:
                state.findings.append(Finding('DEMO_UNSUPPORTED', 'review', {'message': 'Deliberately injected unsupported finding'}))
                state.event('Demo harness', 'controlled_fault', 'Inject unsupported intermediate finding',
                            'DEMO_UNSUPPORTED', 'Explicit demo/test mode', 'Critic')
            if critic.run(state, data, invoice, policy):
                break
            if state.attempts >= policy.max_rechecks:
                state.event('Planner', 'retry_gate', 'Stop rechecking', 'Retry limit exhausted', 'Critic disagreement', 'Decision')
                break
            state.attempts += 1
            state.plan.append({'step': 'Bounded recheck', 'reason': 'Critic challenged findings; rerun tools from originals'})
            state.event('Planner', 'retry_gate', 'Request bounded recheck', f'Recheck {state.attempts} of {policy.max_rechecks}',
                        'Critic contradiction', 'Matching')
    except (ValueError, ArithmeticError, KeyError, TypeError) as exc:
        state.verified = False
        state.event('Coordinator', 'safe_failure', 'Stop unsupported execution',
                    f'{type(exc).__name__}: {exc}', 'Unexpected source inconsistency', 'Decision')
    decision.run(state)
    state.elapsed_ms = round((perf_counter() - start) * 1000, 4)
    return state
