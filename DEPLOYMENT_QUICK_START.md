# Quick Deployment Checklist

## Pre-Deployment

- [ ] Code committed to GitHub
- [ ] PWA icons generated (`python generate_pwa_icons.py logo.png`)
- [ ] Icons committed to repository
- [ ] All tests passing locally

## Render Setup (5 minutes)

1. **Create PostgreSQL Database**
   - Render Dashboard → New + → PostgreSQL
   - Name: `skanda-db`
   - Plan: Free
   - Copy Internal Database URL

2. **Create Web Service**
   - Render Dashboard → New + → Web Service
   - Connect GitHub repo
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120`

3. **Set Environment Variables**
   ```
   FLASK_ENV=production
   SECRET_KEY=<generate-with: python -c "import secrets; print(secrets.token_hex(32))">
   DATABASE_URL=<paste-internal-database-url>
   ```

4. **Deploy** → Wait for build to complete

## Post-Deployment (2 minutes)

1. **Initialize Database**
   - Render Shell → Run:
     ```bash
     python init_db.py
     python seed.py
     ```

2. **Verify**
   - Visit app URL
   - Login with default credentials
   - Test PWA installation

## PWA Icons (If Missing)

If you don't have icons yet, create simple placeholders:

1. Use online tool: https://realfavicongenerator.net/
2. Or create 512x512 PNG with your logo
3. Run: `python generate_pwa_icons.py your-icon.png`
4. Commit icons to repository

## Troubleshooting

**App won't start?**
- Check environment variables
- Verify DATABASE_URL format (postgresql:// not postgres://)
- Check Render logs

**Database errors?**
- Use Internal Database URL (not External)
- Verify database is running
- Check credentials

**PWA not working?**
- Verify HTTPS (required)
- Check manifest.json loads
- Verify service worker registers (browser console)
- Ensure all icons exist

## Quick Commands

```bash
# Generate secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Generate PWA icons
python generate_pwa_icons.py logo.png

# Test locally with production config
export FLASK_ENV=production
export DATABASE_URL=postgresql://...
python app.py
```

---

**Full guide**: See `DEPLOYMENT.md` for detailed instructions.

