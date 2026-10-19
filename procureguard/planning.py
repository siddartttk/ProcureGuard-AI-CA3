"""A swappable planning model; accounting decisions are outside its authority."""
import json
import os
from time import perf_counter
from urllib.request import Request, urlopen

TOOLS = {
    'warehouse_lookup': {'codes': {'MISSING_GRN', 'EXCESS_RECEIVED'}, 'owner': 'Receiving team',
                         'need': 'Approved goods receipt for the matching order and item'},
    'amendment_lookup': {'codes': {'PRICE_MISMATCH', 'LINE_EXPOSURE'}, 'owner': 'Procurement manager',
                         'need': 'Approved purchase-order price amendment effective on the invoice date'},
    'bank_verification': {'codes': {'BANK_CHANGE'}, 'owner': 'Finance controller',
                          'need': 'Approved vendor-master bank verification from the trusted source'},
}


def eligible_tools(state, attempted):
    if not state.verified or any(f.code == 'INVALID_DATA' for f in state.findings):
        return []
    codes = {f.code for f in state.findings}
    return [name for name, spec in TOOLS.items() if name not in attempted and codes & spec['codes']]


class MockPlannerModel:
    """Offline deterministic mock of constrained model-driven tool selection."""
    name = 'Offline mock planner'

    def choose(self, state, allowed):
        # Prioritise source integrity, then commercial authority, then delivery evidence.
        for name in ('bank_verification', 'amendment_lookup', 'warehouse_lookup'):
            if name in allowed:
                return {'tool': name, 'summary': f'Resolve {", ".join(sorted(TOOLS[name]["codes"] & {f.code for f in state.findings}))} using an authorised source.'}
        return {'tool': 'stop', 'summary': 'No remaining permitted evidence lookup can resolve these findings.'}


class OllamaPlannerModel:
    name = 'Ollama local planner'

    def __init__(self, model=None):
        self.model = model or os.environ.get('PROCUREGUARD_OLLAMA_MODEL', 'qwen2.5-coder:7b')
        self.last_record = {}

    def choose(self, state, allowed):
        self.last_record = {}
        started = perf_counter()
        # Fixed loopback address, bounded response, structured enum and explicit allowlist.
        schema = {'type': 'object', 'properties': {'tool': {'type': 'string', 'enum': allowed + ['stop']},
                  'summary': {'type': 'string'}}, 'required': ['tool', 'summary'], 'additionalProperties': False}
        context = {'finding_codes': [f.code for f in state.findings], 'allowed_tools': allowed,
                   'tool_goals': {n: TOOLS[n]['need'] for n in allowed}}
        body = {'model': self.model, 'stream': False, 'format': schema,
                'options': {'temperature': 0, 'num_predict': 180, 'num_ctx': 2048},
                'messages': [{'role': 'system', 'content': 'Select one authorised evidence lookup to resolve an invoice exception. Return only the specified JSON. Prefer a lookup over stop while useful tools remain. Never approve payments, change invoices, invent evidence or calculate accounting decisions.'},
                             {'role': 'user', 'content': json.dumps(context)}]}
        request = Request('http://127.0.0.1:11434/api/chat', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
        with urlopen(request, timeout=15) as response:
            raw = response.read(100_001)
        if len(raw) > 100_000:
            raise ValueError('Planner response exceeds limit')
        envelope=json.loads(raw)
        choice = json.loads(envelope['message']['content'])
        validate_choice(choice, allowed)
        self.last_record = {'model':self.model,'endpoint':'http://127.0.0.1:11434/api/chat',
                            'request':body,'response':choice,'elapsed_ms':round((perf_counter()-started)*1000,3),
                            'provider_model':envelope.get('model'),'generated_tokens':envelope.get('eval_count'),
                            'live_inference':True}
        return choice

    @staticmethod
    def available_models():
        with urlopen('http://127.0.0.1:11434/api/tags',timeout=2) as response:
            raw=response.read(100_001)
        if len(raw)>100_000:raise ValueError('Model discovery response exceeds limit')
        result=json.loads(raw)
        return [r['name'] for r in result.get('models',[]) if isinstance(r.get('name'),str)]


def validate_choice(choice, allowed):
    if not isinstance(choice, dict) or set(choice) != {'tool', 'summary'}:
        raise ValueError('Planner output does not match the action contract')
    if choice['tool'] not in allowed + ['stop'] or not isinstance(choice['summary'], str) or len(choice['summary']) > 600:
        raise ValueError('Planner action is outside the permitted tool contract')
    return choice
