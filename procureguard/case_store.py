"""Transactional local case history. Identity selection in the demo is not authentication."""
import hashlib
import json
import sqlite3
from copy import deepcopy
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ACTORS = {'ap_reviewer': 'reviewer', 'faculty_observer': 'observer'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def checksum(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class VersionConflict(ValueError):
    pass


class CaseStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS cases(case_id TEXT PRIMARY KEY, version INTEGER NOT NULL, status TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS runs(case_id TEXT NOT NULL, version INTEGER NOT NULL, request_key TEXT UNIQUE NOT NULL,
                    content TEXT NOT NULL, content_hash TEXT NOT NULL, PRIMARY KEY(case_id,version));
                CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL, version INTEGER NOT NULL,
                    payload TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS lifecycle(namespace TEXT NOT NULL, invoice_id TEXT NOT NULL, status TEXT NOT NULL,
                    replacement TEXT, PRIMARY KEY(namespace,invoice_id));
            ''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=10000')
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _event(self, db, case_id, version, action, **details):
        last = db.execute('SELECT event_hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        previous = last['event_hash'] if last else '0'*64
        payload = {'timestamp': datetime.now(timezone.utc).isoformat(), 'case_id': case_id,
                   'version': version, 'action': action, **details}
        encoded = canonical(payload)
        hashed = hashlib.sha256((previous+encoded).encode()).hexdigest()
        db.execute('INSERT INTO events(case_id,version,payload,previous_hash,event_hash) VALUES(?,?,?,?,?)',
                   (case_id,version,encoded,previous,hashed))

    def current(self, case_id):
        with self.connection() as db:
            row = db.execute('SELECT * FROM cases WHERE case_id=?',(case_id,)).fetchone()
            return dict(row) if row else {'case_id': case_id, 'version': 0, 'status': 'NEW'}

    def save(self, result, *, expected_version, request_key):
        if not request_key or len(request_key) > 200:
            raise ValueError('A bounded idempotency key is required')
        value = result.to_dict() if hasattr(result, 'to_dict') else result
        case_id = value['invoice_id']
        hashed = checksum(value)
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT case_id,version,content_hash FROM runs WHERE request_key=?',(request_key,)).fetchone()
            if old:
                if old['case_id'] != case_id or old['content_hash'] != hashed:
                    raise ValueError('Idempotency key reused with different content')
                return old['version']
            row = db.execute('SELECT version FROM cases WHERE case_id=?',(case_id,)).fetchone()
            current = row['version'] if row else 0
            if current != expected_version:
                raise VersionConflict('The case changed; reload its current version before saving')
            version = current+1
            decision = value['final']['recommendation']
            status = 'READY_FOR_REVIEW' if decision == 'READY_FOR_HUMAN_APPROVAL' else 'WAITING_FOR_EVIDENCE' if value['next_actions'] else 'HELD'
            if not value['final']['verified']:
                status = 'VERIFICATION_FAILED'
            db.execute('INSERT INTO runs VALUES(?,?,?,?,?)',(case_id,version,request_key,canonical(value),hashed))
            db.execute('INSERT INTO cases VALUES(?,?,?) ON CONFLICT(case_id) DO UPDATE SET version=excluded.version,status=excluded.status',
                       (case_id,version,status))
            self._event(db,case_id,version,'investigation_saved',content_hash=hashed,status=status)
            return version

    def review(self, case_id, *, expected_version, actor, action, rationale):
        if ACTORS.get(actor) != 'reviewer':
            raise PermissionError('The observer role cannot record a review')
        if action not in ('confirm_recommendation','request_recheck') or not isinstance(rationale,str) or not 1 <= len(rationale.strip()) <= 1000:
            raise ValueError('A supported review action and a 1–1,000 character rationale are required')
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT version FROM cases WHERE case_id=?',(case_id,)).fetchone()
            if row is None or row['version'] != expected_version:
                raise VersionConflict('Review is stale; reload the case')
            status = 'REVIEW_CONFIRMED' if action == 'confirm_recommendation' else 'RECHECK_REQUESTED'
            version = expected_version+1
            db.execute('UPDATE cases SET status=?,version=? WHERE case_id=?',(status,version,case_id))
            self._event(db,case_id,version,action,actor=actor,role='reviewer',rationale=rationale.strip(),simulation=True,payment_executed=False,status=status)
            return version

    def recover(self, case_id, source_hash):
        """Atomically reopen a packet and the current review revision, without rerunning tools."""
        with self.connection() as db:
            row = db.execute('''SELECT r.content,r.content_hash,r.version AS run_version,c.version,c.status
                FROM runs r JOIN cases c ON c.case_id=r.case_id
                WHERE r.case_id=? ORDER BY r.version DESC LIMIT 1''',(case_id,)).fetchone()
            if row is None:
                return None
            value = json.loads(row['content'])
            if checksum(value) != row['content_hash']:
                raise ValueError('Stored investigation content failed its integrity check')
            if value.get('source_snapshot_hash') != source_hash:
                return None
            return {'result':value,'version':row['version'],'run_version':row['run_version'],'status':row['status']}

    def revisions(self, case_id):
        with self.connection() as db:
            return [row['version'] for row in db.execute('SELECT version FROM runs WHERE case_id=? ORDER BY version DESC',(case_id,))]

    def effective_data(self, data, namespace):
        result = deepcopy(data)
        with self.connection() as db:
            for row in db.execute('SELECT invoice_id,status FROM lifecycle WHERE namespace=?',(namespace,)):
                if row['invoice_id'] in result.invoices:
                    result.invoices[row['invoice_id']]['lifecycle_status'] = row['status']
        return result

    def set_lifecycle(self, data, invoice_id, new_status, *, expected_status, actor, rationale, replacement=None):
        """Record a simulated reviewer classification and invalidate recommendations by source hash."""
        from .lifecycle import dataset_namespace, validate_transition
        if ACTORS.get(actor) != 'reviewer':
            raise PermissionError('Only a demo reviewer can classify invoice lifecycle')
        if not isinstance(rationale,str) or not 1 <= len(rationale.strip()) <= 1000:
            raise ValueError('A 1-1,000 character rationale is required')
        namespace = dataset_namespace(data)
        effective = self.effective_data(data,namespace)
        if effective.invoices.get(invoice_id,{}).get('lifecycle_status','submitted') != expected_status:
            raise VersionConflict('Lifecycle changed; reload before applying the classification')
        old = validate_transition(effective,invoice_id,new_status,replacement)
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT status FROM lifecycle WHERE namespace=? AND invoice_id=?',(namespace,invoice_id)).fetchone()
            actual = row['status'] if row else data.invoices[invoice_id].get('lifecycle_status','submitted')
            if actual != expected_status or old != expected_status:
                raise VersionConflict('Lifecycle changed; reload before applying the classification')
            current = db.execute('SELECT version FROM cases WHERE case_id=?',(invoice_id,)).fetchone()
            version = (current['version'] if current else 0)+1
            db.execute('INSERT INTO lifecycle VALUES(?,?,?,?) ON CONFLICT(namespace,invoice_id) DO UPDATE SET status=excluded.status,replacement=excluded.replacement',
                       (namespace,invoice_id,new_status,replacement))
            db.execute('INSERT INTO cases VALUES(?,?,?) ON CONFLICT(case_id) DO UPDATE SET version=excluded.version,status=excluded.status',
                       (invoice_id,version,'RECHECK_REQUIRED'))
            self._event(db,invoice_id,version,'lifecycle_changed',namespace=namespace,old_lifecycle=old,new_lifecycle=new_status,
                        replacement=replacement,actor=actor,rationale=rationale.strip(),status='RECHECK_REQUIRED',simulation=True,payment_executed=False)
            return version

    def history(self, case_id):
        with self.connection() as db:
            return [json.loads(r['payload']) for r in db.execute('SELECT payload FROM events WHERE case_id=? ORDER BY seq',(case_id,))]

    def load(self, case_id, version=None):
        with self.connection() as db:
            if version is None:
                row = db.execute('SELECT content,content_hash FROM runs WHERE case_id=? ORDER BY version DESC LIMIT 1',(case_id,)).fetchone()
            else:
                row = db.execute('SELECT content,content_hash FROM runs WHERE case_id=? AND version=?',(case_id,version)).fetchone()
            if row is None:
                return None
            value = json.loads(row['content'])
            if checksum(value) != row['content_hash']:
                raise ValueError('Stored investigation content failed its integrity check')
            return value

    def verify_integrity(self):
        with self.connection() as db:
            previous, count, latest, expected_lifecycle = '0'*64, 0, {}, {}
            for row in db.execute('SELECT * FROM events ORDER BY seq'):
                if row['previous_hash'] != previous or hashlib.sha256((previous+row['payload']).encode()).hexdigest() != row['event_hash']:
                    return {'valid': False, 'events': count, 'reason': 'Event hash chain mismatch'}
                payload = json.loads(row['payload'])
                latest[row['case_id']] = (row['version'],payload.get('status'))
                if payload['action']=='lifecycle_changed':
                    expected_lifecycle[(payload['namespace'],row['case_id'])]=(payload['new_lifecycle'],payload['replacement'])
                if payload['action'] == 'investigation_saved':
                    run = db.execute('SELECT content,content_hash FROM runs WHERE case_id=? AND version=?',(row['case_id'],row['version'])).fetchone()
                    if run is None or checksum(json.loads(run['content'])) != run['content_hash'] or run['content_hash'] != payload['content_hash']:
                        return {'valid': False, 'events': count, 'reason': 'Stored snapshot digest mismatch'}
                previous, count = row['event_hash'], count+1
            current_cases = {row['case_id']:row for row in db.execute('SELECT * FROM cases')}
            for identity,(version,status) in latest.items():
                current = current_cases.get(identity)
                if current is None or current['version'] != version or status is not None and current['status'] != status:
                    return {'valid':False,'events':count,'reason':'Case metadata differs from its latest event'}
            if set(current_cases) != set(latest):
                return {'valid':False,'events':count,'reason':'Unlogged case metadata'}
            actual_lifecycle={(row['namespace'],row['invoice_id']):(row['status'],row['replacement']) for row in db.execute('SELECT * FROM lifecycle')}
            if actual_lifecycle != expected_lifecycle:
                return {'valid':False,'events':count,'reason':'Lifecycle metadata differs from its event'}
            return {'valid': True, 'events': count, 'head_hash': previous}
