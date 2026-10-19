"""Structured contracts shared by agents, UI and downloadable reports."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    evidence: dict[str, str]


@dataclass
class AuditState:
    invoice_id: str
    run_id: str = field(default_factory=lambda: str(uuid4()))
    plan: list[dict[str, str]] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    risk_observations: dict[str, list[Finding]] = field(default_factory=dict)
    trace: list[dict[str, Any]] = field(default_factory=list)
    verifications: list[dict[str, Any]] = field(default_factory=list)
    attempts: int = 0
    verified: bool = False
    recommendation: str | None = None
    explanation: str = ''
    risk_score: int = 0
    elapsed_ms: float = 0
    demo_fault: str = 'none'
    payment_executed: bool = False

    def event(self, agent: str, tool: str, action: str, outcome: str,
              condition: str, next_step: str):
        self.trace.append({'sequence': len(self.trace) + 1,
                           'timestamp': datetime.now(timezone.utc).isoformat(),
                           'agent': agent, 'tool': tool, 'action': action,
                           'input_summary': f'invoice={self.invoice_id}; attempt={self.attempts}',
                           'outcome': outcome, 'condition': condition, 'next_step': next_step})

    def to_dict(self) -> dict:
        return asdict(self)
