import json
from datetime import datetime, timezone
from pathlib import Path


def report_json(state) -> str:
    return json.dumps(state.to_dict(), indent=2, ensure_ascii=False)


def record_review(state, action: str, rationale: str, path: Path) -> dict:
    """Append a simulated human action. The recommendation remains immutable."""
    if state.recommendation is None or action not in ('confirm_recommendation', 'disagree_request_recheck'):
        raise ValueError('A completed investigation and a supported simulated action are required')
    if not rationale.strip() or len(rationale) > 1000:
        raise ValueError('Provide a rationale between 1 and 1,000 characters')
    event = {'timestamp': datetime.now(timezone.utc).isoformat(), 'actor': 'demo_reviewer',
             'run_id': state.run_id, 'invoice_id': state.invoice_id, 'action': action,
             'recommendation': state.recommendation, 'rationale': rationale.strip(),
             'simulation': True, 'payment_executed': False}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(event) + '\n')
    return event
