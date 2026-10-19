from .. import tools
from ..policies import WEIGHTS


class RiskAgent:
    """Goal: investigate selected indicators and explain compound severity."""

    def run(self, state, data, invoice, policy, selected):
        for name in selected:
            found = tools.compound(state.findings) if name == 'compound_analysis' else state.risk_observations[name]
            state.findings.extend(found)
            state.event('Risk', name, 'Assess retained screening evidence', ', '.join(f.code for f in found) or 'No compound anomaly',
                        'Planner selected tool from evidence', 'Critic' if name == 'compound_analysis' else 'Risk tools')
        state.risk_score = min(100, sum(WEIGHTS.get(f.code, 0) for f in state.findings))
