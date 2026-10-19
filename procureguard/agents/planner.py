from .. import tools


class PlannerAgent:
    """Goal: select a complete, invoice-specific investigation and revise its route."""

    def plan(self, state, data, invoice, policy):
        context = f'PO {"available" if invoice.get("po_id") in data.purchase_orders else "missing"}; vendor {"available" if invoice.get("vendor_id") in data.vendors else "missing"}'
        state.plan = [
            {'step': 'Validate and match', 'reason': 'Mandatory for every invoice; ' + context},
            {'step': 'Screen risk categories', 'reason': 'Mandatory duplicate, bank, status and value coverage'},
            {'step': 'Select conditional investigation', 'reason': 'Based on screening and matching evidence'},
            {'step': 'Independent critic', 'reason': 'Recompute from originals; at most one recheck'},
            {'step': 'Decision coordinator', 'reason': 'Recommend a human-review outcome'},
        ]
        state.event('Planner', 'context_inspection', 'Create investigation plan', context,
                    'Invoice selected', 'Matching')

    def route(self, state, data, invoice, policy):
        if any(f.code == 'INVALID_DATA' for f in state.findings):
            state.event('Planner', 'route_selection', 'Stop unsupported comparisons',
                        'Invalid source values prevent financial checks', 'Schema invalid', 'Missing Evidence')
            state.event('Planner', 'missing_evidence', 'Record evidence gap', 'Request corrected input', 'INVALID_DATA', 'Critic')
            return []
        state.risk_observations = tools.screen(data, invoice, policy)
        selected = list(state.risk_observations)
        state.event('Planner', 'mandatory_risk_screen', 'Screen duplicate, bank, status and value',
                    ', '.join(selected) or 'No risk indicators', 'Valid numeric context', 'Route selection')
        if any(f.severity == 'missing' for f in state.findings):
            state.plan.append({'step': 'Missing evidence', 'reason': 'Request absent records; never assume a match'})
            state.event('Planner', 'missing_evidence', 'Record missing procurement evidence',
                        ', '.join(f.code for f in state.findings if f.severity == 'missing'),
                        'Required records absent', 'Risk' if selected else 'Critic')
        if selected or any(f.severity == 'review' for f in state.findings):
            state.plan.append({'step': 'Risk investigation', 'reason': ', '.join(selected) or 'Investigate matching anomalies'})
            state.event('Planner', 'route_selection', 'Select Risk Investigator', ', '.join(selected + ['compound_analysis']),
                        'Risk indicator or matching discrepancy', 'Risk')
            return selected + ['compound_analysis']
        state.event('Planner', 'route_selection', 'Select independent verification', 'Risk agent skipped',
                    'No risk indicators or matching discrepancies', 'Critic')
        return []
