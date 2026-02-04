"""
Test Supabase database connectivity.
Run: python test_db_connection.py
Uses DATABASE_URL from .env
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()

def test():
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        print("Error: DATABASE_URL not set in .env")
        sys.exit(1)
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    # Mask password for display
    display = url
    if '@' in url and ':' in url:
        try:
            parts = url.split('@', 1)
            user_part = parts[0]
            if ':' in user_part:
                user = user_part.rsplit(':', 1)[0]
                display = f"{user}:****@{parts[1]}"
        except Exception:
            pass

    print(f"Testing: {display}\n")

    try:
        import psycopg2
        conn = psycopg2.connect(url, connect_timeout=10, sslmode='require')
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        print("SUCCESS: Database connection works!")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == '__main__':
    ok = test()
    sys.exit(0 if ok else 1)
