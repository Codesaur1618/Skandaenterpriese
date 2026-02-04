# Supabase Migration Guide

Migrate from current Supabase project to a new one (e.g. different region).

## Prerequisites

- Working connection to **current** Supabase (for export)
- New Supabase project created (for import)

If export fails with connection errors, try:
- Mobile hotspot (different network)
- Session mode pooler with correct region in `.env`

---

## Step 1: Export current database to local

```powershell
python export_supabase_to_local.py
```

- Uses `DATABASE_URL` from `.env` (current project)
- Output: `backups/supabase_backup_YYYYMMDD_HHMM.sql`
- Requires working connection (pooler Session mode recommended)

---

## Step 2: Create new Supabase project

1. [Supabase Dashboard](https://supabase.com/dashboard) → **New project**
2. Choose region (e.g. **ap-south-1** if in India)
3. Set database password
4. Wait for provisioning

---

## Step 3: Update .env

1. New project → **Connect** → **Session** (pooler)
2. Copy connection string
3. Replace `DATABASE_URL` in `.env`

---

## Step 4: Import into new project

```powershell
python import_local_to_supabase.py
```

- Uses `DATABASE_URL` from `.env` (new project)
- Creates schema, truncates, imports data
- Uses latest backup in `backups/` (or pass path: `python import_local_to_supabase.py backups/supabase_backup_20250102_1200.sql`)

---

## Step 5: Run app

```powershell
python app.py
```

---

## Files

| File | Purpose |
|------|---------|
| `export_supabase_to_local.py` | Export Supabase → local SQL |
| `import_local_to_supabase.py` | Import local SQL → new Supabase |
| `backups/supabase_backup_*.sql` | Local backup files |
