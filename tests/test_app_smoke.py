from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1]/'app.py')

@pytest.fixture
def app(tmp_path,monkeypatch):
    monkeypatch.setenv('PROCUREGUARD_DB_PATH',str(tmp_path/'ui.sqlite'))
    return AppTest.from_file(APP,default_timeout=30).run()

def test_dashboard_audit_and_reset(app):
    assert not app.exception
    next(b for b in app.button if b.label=='Audit loaded invoices').click().run()
    assert not app.exception and app.metric[0].value=='43'
    next(b for b in app.button if b.label=='Restore demo records').click().run()
    assert app.metric[0].value=='0'

def test_compound_case_resolution_visible(app):
    app.sidebar.radio[0].set_value('Investigate a case').run()
    next(b for b in app.button if b.label=='Run investigation').click().run()
    assert not app.exception
    result=app.session_state.results['PG103']
    assert len(result['steps'])==2 and result['final']['recommendation']=='READY_FOR_HUMAN_APPROVAL'

def test_delayed_evidence_can_resume(app):
    app.sidebar.radio[0].set_value('Investigate a case').run()
    app.selectbox[0].set_value('PG104').run()
    next(b for b in app.button if b.label=='Run investigation').click().run()
    assert app.session_state.results['PG104']['final']['recommendation']=='INSUFFICIENT_DATA'
    app.checkbox[0].check().run()
    next(b for b in app.button if b.label=='Run investigation').click().run()
    assert not app.exception
    assert app.session_state.results['PG104']['final']['recommendation']=='READY_FOR_HUMAN_APPROVAL'

def test_poisoned_evidence_blocked(app):
    app.sidebar.radio[0].set_value('Investigate a case').run()
    app.selectbox[0].set_value('PG106').run()
    next(b for b in app.button if b.label=='Run investigation').click().run()
    assert not app.exception and not app.session_state.results['PG106']['final']['verified']

def test_incomplete_upload_rejected(app):
    next(b for b in app.button if b.label=='Validate and load bundle').click().run()
    assert not app.exception and 'four' in app.error[0].value

@pytest.mark.parametrize('page',['Evidence & controls','Validation lab'])
def test_support_pages_render(app,page):
    app.sidebar.radio[0].set_value(page).run()
    assert not app.exception
