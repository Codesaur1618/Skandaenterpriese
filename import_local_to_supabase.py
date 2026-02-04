"""
Import local backup into new Supabase project.
Run: python import_local_to_supabase.py [backup_file]

Requires: DATABASE_URL in .env pointing to NEW Supabase project.
- If no backup_file given, uses latest backups/supabase_backup_*.sql
- Creates schema first (from migrations/001_initial_schema.sql), then runs backup SQL.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()


def main():
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        print('Error: DATABASE_URL not set in .env')
        print('Update .env with your NEW Supabase project connection string.')
        sys.exit(1)
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    try:
        import psycopg2
    except ImportError:
        print('Error: psycopg2 required. Run: pip install psycopg2-binary')
        sys.exit(1)

    # Find backup file
    backup_dir = Path('backups')
    if len(sys.argv) > 1:
        backup_path = Path(sys.argv[1])
        if not backup_path.exists():
            print(f'Error: Backup file not found: {backup_path}')
            sys.exit(1)
    else:
        backups = sorted(backup_dir.glob('supabase_backup_*.sql'), reverse=True)
        if not backups:
            print('Error: No backup file found in backups/')
            print('Run export_supabase_to_local.py first (with working connection).')
            sys.exit(1)
        backup_path = backups[0]
        print(f'Using backup: {backup_path}')

    schema_path = Path('migrations/001_initial_schema.sql')
    if not schema_path.exists():
        print(f'Error: Schema file not found: {schema_path}')
        sys.exit(1)

    print('Connecting to new Supabase...')
    try:
        conn = psycopg2.connect(url, connect_timeout=15, sslmode='require')
        conn.autocommit = False
    except Exception as e:
        print(f'Connection failed: {e}')
        sys.exit(1)

    tables = [
        'audit_logs', 'ocr_jobs', 'delivery_orders', 'credit_entries',
        'proxy_bill_items', 'proxy_bills', 'bill_items', 'bills', 'vendors',
        'role_permissions', 'permissions', 'users', 'tenants'
    ]

    try:
        with conn.cursor() as cur:
            print('Creating schema...')
            schema_sql = schema_path.read_text(encoding='utf-8')
            cur.execute(schema_sql)
            conn.commit()
            print('  Schema created.')

            print('Truncating existing data (if any)...')
            cur.execute(
                "TRUNCATE TABLE " + ", ".join(tables) + " CASCADE"
            )
            conn.commit()
            print('  Done.')

            print('Importing data...')
            backup_sql = backup_path.read_text(encoding='utf-8')
            cur.execute(backup_sql)
            conn.commit()
            print('  Data imported.')

        print('\nDone! Run python app.py to start.')
    except Exception as e:
        conn.rollback()
        print(f'Error: {e}')
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
