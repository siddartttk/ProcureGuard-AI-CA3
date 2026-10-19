"""Load only operational tables. The agent data loader cannot read the answer key."""
import csv
import io
from dataclasses import dataclass
from pathlib import Path
from .schemas import SCHEMAS, PRIMARY_KEYS, row_errors


@dataclass
class Dataset:
    vendors: dict[str, dict[str, str]]
    purchase_orders: dict[str, dict[str, str]]
    goods_receipts: dict[str, dict[str, str]]
    invoices: dict[str, dict[str, str]]
    errors: dict[str, list[str]]


def parse_csv(text: str, table: str) -> list[dict[str, str]]:
    if len(text) > 2_000_000:
        raise ValueError('Each CSV must be at most 2 MB')
    try:
        reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')), strict=True)
        allowed_headers = [SCHEMAS[table]]
        if table == 'invoices':
            allowed_headers.append(SCHEMAS[table] + ['lifecycle_status'])
        if reader.fieldnames not in allowed_headers:
            raise ValueError(f'{table}: expected columns in this order: {", ".join(SCHEMAS[table])}')
        rows = list(reader)
        if len(rows) > 5000:
            raise ValueError('At most 5,000 records per table')
        if any(None in r or any(v is None for v in r.values()) for r in rows):
            raise ValueError(f'{table}: inconsistent column count')
        return [{k: v.strip() for k, v in r.items()} for r in rows]
    except csv.Error as exc:
        raise ValueError(f'{table}: malformed CSV: {exc}') from exc


def from_tables(tables: dict[str, list[dict[str, str]]]) -> Dataset:
    maps, errors = {}, {}
    for table in SCHEMAS:
        rows = tables[table]
        key = PRIMARY_KEYS[table]
        indexed = {}
        for row in rows:
            identity = row.get(key, '')
            if not identity or identity in indexed:
                raise ValueError(f'{table}: missing or duplicate primary key {identity!r}')
            problems = row_errors(table, row)
            if problems:
                errors[f'{table}:{identity}'] = problems
            indexed[identity] = dict(row)
        maps[table] = indexed
    if not maps['invoices']:
        raise ValueError('At least one invoice is required')
    return Dataset(**maps, errors=errors)


def load_dataset(directory: Path) -> Dataset:
    return from_tables({name: parse_csv((directory / f'{name}.csv').read_text(encoding='utf-8-sig'), name)
                        for name in SCHEMAS})
