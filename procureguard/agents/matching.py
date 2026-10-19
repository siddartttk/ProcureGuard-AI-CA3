from .. import tools


class MatchingAgent:
    """Goal: reconcile source links and all mandatory numerical comparisons."""

    def run(self, state, data, invoice, policy):
        invalid = tools.schema_check(data, invoice, policy)
        state.findings.extend(invalid)
        state.event('Matching', 'schema_validation', 'Validate invoice and linked source values',
                    'Invalid context' if invalid else 'Schema accepted', 'Mandatory', 'Critic' if invalid else 'Matching tools')
        if invalid:
            return
        for name, tool in tools.MATCH_TOOLS.items():
            found = tool(data, invoice, policy)
            state.findings.extend(found)
            state.event('Matching', name, 'Compare original records', ', '.join(f.code for f in found) or 'No discrepancy',
                        'Mandatory', 'Planner routing' if name == 'quantity_comparison' else 'Matching tools')
