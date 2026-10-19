"""Evidence specialist: verify source authority and apply scoped updates atomically."""
from copy import deepcopy
from ..evidence import apply_evidence


class EvidenceAgent:
    def run(self, data, invoice_id, tool, repository, *, released=False):
        outcome = repository.lookup(tool, data.invoices[invoice_id], released=released)
        candidate = deepcopy(data)
        if outcome.status == 'accepted':
            try:
                apply_evidence(candidate,candidate.invoices[invoice_id],tool,outcome.accepted)
            except (ValueError, KeyError, TypeError) as exc:
                outcome.status = 'conflict'
                outcome.reason = str(exc)
                candidate = deepcopy(data)
        return outcome, candidate
