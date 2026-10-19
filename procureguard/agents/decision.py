from ..policies import WEIGHTS

READY = 'READY_FOR_HUMAN_APPROVAL'
HOLD = 'HOLD_FOR_REVIEW'
MISSING = 'INSUFFICIENT_DATA'


class DecisionAgent:
    """Goal: fail safely and explain a recommendation. Never authorise payment."""

    def run(self, state):
        if not state.verified:
            state.recommendation = HOLD
            state.explanation = 'Independent verification remains unresolved. Human investigation is required.'
        elif any(f.severity == 'missing' for f in state.findings):
            state.recommendation = MISSING
            state.explanation = 'Required evidence is absent or invalid. Obtain corrected records. Any additional risk flags remain visible.'
        elif state.findings:
            state.recommendation = HOLD
            state.explanation = 'Verified anomalies require human review: ' + ', '.join(f.code for f in state.findings) + '.'
        else:
            state.recommendation = READY
            state.explanation = 'All supported mandatory checks reconcile and the critic agrees. A human must still review the invoice.'
        state.risk_score = min(100, sum(WEIGHTS.get(f.code, 0) for f in state.findings))
        state.event('Decision', 'decision_policy', 'Emit evidence-backed recommendation',
                    state.recommendation, 'Critic passed' if state.verified else 'Retry cap reached or execution failure', 'Human review simulation')
