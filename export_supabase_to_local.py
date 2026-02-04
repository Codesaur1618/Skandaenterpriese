"""
Export Supabase database to local SQL backup file.
Run: python export_supabase_to_local.py

Requires: DATABASE_URL in .env (must have working connection to Supabase).
Output: backups/supabase_backup_YYYYMMDD_HHMM.sql

If connection fails (DNS/network), try:
- Different network (e.g. mobile hotspot)
- Session mode pooler: postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Tables in FK order for clean import
TABLE_ORDER = [
    'tenants',
    'users',
    'permissions',
    'role_permissions',
    'vendors',
    'bills',
    'bill_items',
    'proxy_bills',
    'proxy_bill_items',
    'credit_entries',
    'delivery_orders',
    'ocr_jobs',
    'audit_logs',
]


def escape_sql(val):
    """Escape value for SQL INSERT"""
    if val is None:
        return 'NULL'
    if isinstance(val, bool):
        return 'TRUE' if val else 'FALSE'
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, (datetime,)):
        return f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'"
    s = str(val)
    return "'" + s.replace("'", "''").replace("\\", "\\\\") + "'"


def export_table(cursor, table, out):
    """Export table data as INSERT statements"""
    cursor.execute(f'SELECT * FROM {table} ORDER BY id')
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    if not rows:
        out.write(f'-- {table}: 0 rows\n')
        return 0
    out.write(f'-- {table}: {len(rows)} rows\n')
    for row in rows:
        vals = [escape_sql(v) for v in row]
        cols_str = ', '.join(f'"{c}"' for c in cols)
        vals_str = ', '.join(vals)
        out.write(f'INSERT INTO {table} ({cols_str}) VALUES ({vals_str});\n')
    out.write('\n')
    return len(rows)


def main():
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        print('Error: DATABASE_URL not set in .env')
        sys.exit(1)
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    try:
        import psycopg2
    except ImportError:
        print('Error: psycopg2 required. Run: pip install psycopg2-binary')
        sys.exit(1)

    Path('backups').mkdir(exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M')
    out_path = Path('backups') / f'supabase_backup_{stamp}.sql'

    print(f'Connecting to Supabase...')
    try:
        conn = psycopg2.connect(url, connect_timeout=15, sslmode='require')
    except Exception as e:
        print(f'Connection failed: {e}')
        print('Tip: Use Session mode pooler (port 5432) with correct region.')
        sys.exit(1)

    print(f'Exporting to {out_path}...')
    total = 0
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write('-- Supabase backup\n')
        out.write(f'-- Exported at {datetime.now().isoformat()}\n')
        out.write('-- Run import_local_to_supabase.py to restore to new project\n\n')
        out.write('BEGIN;\n\n')

        with conn.cursor() as cur:
            for table in TABLE_ORDER:
                try:
                    n = export_table(cur, table, out)
                    total += n
                    print(f'  {table}: {n} rows')
                except Exception as e:
                    print(f'  {table}: ERROR {e}')
                    out.write(f'-- ERROR {table}: {e}\n\n')

        out.write('\n-- Fix sequences\n')
        with conn.cursor() as cur:
            for table in TABLE_ORDER:
                try:
                    cur.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
                    max_id = cur.fetchone()[0]
                    next_val = max(max_id + 1, 1)
                    out.write(f"SELECT setval('{table}_id_seq', {next_val});\n")
                except Exception:
                    pass

        out.write('\nCOMMIT;\n')

    conn.close()
    print(f'\nDone. Exported {total} rows to {out_path}')
    print('Next: Create new Supabase project, update .env, then run: python import_local_to_supabase.py')


if __name__ == '__main__':
    main()
