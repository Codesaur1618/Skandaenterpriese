# Run Skanda app with .venv and .env (Supabase config)
# Usage: .\run.ps1 [seed|app]
#   seed - Run seed_supabase.py to populate initial data
#   app  - Run Flask app (default)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

# Activate .venv
$VenvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating .venv..." -ForegroundColor Yellow
    python -m venv .venv
}
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    & $ActivateScript
} else {
    Write-Host "Warning: .venv\Scripts\Activate.ps1 not found. Using system Python." -ForegroundColor Yellow
}

# Ensure .env exists
$EnvPath = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $EnvPath)) {
    Write-Host "Error: .env file not found. Create .env with DATABASE_URL, SECRET_KEY, FLASK_ENV for Supabase." -ForegroundColor Red
    exit 1
}

# Install/update dependencies (includes python-dotenv for .env loading)
Write-Host "Ensuring dependencies..." -ForegroundColor Cyan
pip install -q -r requirements.txt

# Run command
$Command = if ($args.Count -gt 0) { $args[0] } else { "app" }
switch ($Command.ToLower()) {
    "seed" {
        Write-Host "Running seed_supabase.py (uses .env for DATABASE_URL)..." -ForegroundColor Green
        python seed_supabase.py
    }
    "app" {
        Write-Host "Starting Flask app (uses .env for DATABASE_URL, SECRET_KEY, FLASK_ENV)..." -ForegroundColor Green
        python app.py
    }
    default {
        Write-Host "Usage: .\run.ps1 [seed|app]" -ForegroundColor Cyan
        Write-Host "  seed - Populate Supabase with initial data" -ForegroundColor Gray
        Write-Host "  app  - Start Flask application (default)" -ForegroundColor Gray
    }
}
