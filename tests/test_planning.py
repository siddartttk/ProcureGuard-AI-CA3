import json
import pytest
from procureguard.planning import OllamaPlannerModel,validate_choice
from procureguard.state import AuditState


def test_ollama_protocol_uses_loopback_and_constrained_actions(monkeypatch):
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,limit):return json.dumps({'message':{'content':json.dumps({'tool':'warehouse_lookup','summary':'Retrieve approved delivery evidence'})}}).encode()
    def open_request(request,timeout):
        assert request.full_url=='http://127.0.0.1:11434/api/chat' and timeout==15
        body=json.loads(request.data)
        assert body['format']['properties']['tool']['enum']==['warehouse_lookup','stop']
        assert body['stream'] is False
        return Response()
    monkeypatch.setattr('procureguard.planning.urlopen',open_request)
    choice=OllamaPlannerModel('test-model').choose(AuditState('test'),['warehouse_lookup'])
    assert choice['tool']=='warehouse_lookup'


@pytest.mark.parametrize('choice',[
    {'tool':'execute_payment','summary':'Pay'}, {'tool':'warehouse_lookup'},
    {'tool':'warehouse_lookup','summary':'ok','extra':True},
    {'tool':'warehouse_lookup','summary':42}, {'tool':'warehouse_lookup','summary':'x'*601},
])
def test_invalid_model_action_rejected(choice):
    with pytest.raises(ValueError):validate_choice(choice,['warehouse_lookup'])
