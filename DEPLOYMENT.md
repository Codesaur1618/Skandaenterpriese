# Deployment Guide - Skanda Credit & Billing System

This guide provides step-by-step instructions for deploying the Skanda Credit & Billing System as a **Progressive Web App (PWA)** using **Render for backend** and **Vercel for static assets** (optional optimization).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Backend Deployment on Render](#backend-deployment-on-render)
4. [Frontend Optimization with Vercel (Optional)](#frontend-optimization-with-vercel-optional)
5. [PWA Configuration](#pwa-configuration)
6. [PostgreSQL Database Setup](#postgresql-database-setup)
7. [Environment Variables](#environment-variables)
8. [Post-Deployment Steps](#post-deployment-steps)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance & Updates](#maintenance--updates)

---

## Prerequisites

Before deploying, ensure you have:

- ✅ A **GitHub account** (for code hosting)
- ✅ **Git** installed on your local machine
- ✅ Your code committed to a Git repository
- ✅ Python 3.11+ installed locally (for testing)
- ✅ A **Render account** (free tier available)
- ✅ A **Vercel account** (free tier available, optional)

---

## Architecture Overview

### Recommended Setup

```
┌─────────────────┐
│   Users/Browsers│
└────────┬────────┘
         │
         │ HTTPS
         │
┌────────▼─────────────────────────────────┐
│         Render (Backend)                  │
│  ┌────────────────────────────────────┐  │
│  │  Flask Application (Gunicorn)      │  │
│  │  - API Routes                      │  │
│  │  - Templates                       │  │
│  │  - Static Files                    │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  PostgreSQL Database              │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

**Note**: For simplicity, you can deploy everything on Render. Vercel is optional for serving static assets via CDN.

---

## Backend Deployment on Render

### Step 1: Prepare Your Code

Your code is already prepared with:
- ✅ `Procfile` - Gunicorn configuration
- ✅ `requirements.txt` - All dependencies including `gunicorn` and `psycopg2-binary`
- ✅ `runtime.txt` - Python 3.11.0
- ✅ `config.py` - PostgreSQL support
- ✅ PWA files (manifest.json, service-worker.js)

### Step 2: Push to GitHub

1. **Initialize Git repository** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit with PWA support"
   ```

2. **Create a new repository on GitHub**: https://github.com/new

3. **Push your code**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

### Step 3: Create PostgreSQL Database on Render

1. **Sign up/Login** to Render: https://render.com

2. **Create PostgreSQL Database**:
   - Click "New +" → "PostgreSQL"
   - **Name**: `skanda-db`
   - **Database**: `skanda` (or leave default)
   - **User**: `skanda_user` (or leave default)
   - **Region**: Choose closest to your users
   - **Plan**: Free (90 days retention, 1 GB storage)
   - Click "Create Database"

3. **Copy Database URL**:
   - Once created, go to the database dashboard
   - Copy the **Internal Database URL** (format: `postgresql://user:password@host:port/dbname`)
   - **Important**: Render provides both "Internal" and "External" URLs. Use **Internal** for services on Render.

### Step 4: Deploy Web Service on Render

1. **Create a New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository

2. **Configure the Service**:
   - **Name**: `skanda-billing-system` (or your preferred name)
   - **Environment**: `Python 3`
   - **Region**: Same as database (for lower latency)
   - **Branch**: `main`
   - **Root Directory**: `.` (root)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120`
   - **Plan**: Free (750 hours/month)

3. **Environment Variables** (Add these in Render dashboard):
   ```
   FLASK_ENV=production
   SECRET_KEY=<generate-strong-secret-key>
   DATABASE_URL=<paste-internal-database-url-from-step-3>
   PORT=10000
   ```
   
   **Generate SECRET_KEY**:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

4. **Deploy**:
   - Click "Create Web Service"
   - Render will automatically build and deploy your app
   - Your app will be available at: `https://your-app-name.onrender.com`

### Step 5: Initialize Database

1. **Access Render Shell**:
   - Go to your web service → "Shell" tab
   - Or use Render's SSH feature

2. **Run database initialization**:
   ```bash
   python init_db.py
   python seed.py
   ```

3. **Verify**:
   - Visit your app URL
   - Login with default credentials (check `seed.py` for defaults)
   - Verify all features work

---

## Frontend Optimization with Vercel (Optional)

**Note**: This is optional. The Flask app on Render already serves all static files. Vercel can be used to:
- Serve static assets via global CDN
- Improve load times for users far from Render's servers
- Reduce load on Render backend

### Option A: Deploy Static Assets to Vercel

1. **Create `vercel.json`** in project root:
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "static/**",
         "use": "@vercel/static"
       }
     ],
     "routes": [
       {
         "src": "/static/(.*)",
         "dest": "/static/$1"
       }
     ]
   }
   ```

2. **Deploy to Vercel**:
   ```bash
   npm i -g vercel
   vercel login
   vercel --prod
   ```

3. **Update `config.py`** to use Vercel CDN for static files (optional):
   ```python
   STATIC_URL = os.environ.get('STATIC_URL', '')  # e.g., https://your-app.vercel.app
   ```

### Option B: Keep Everything on Render (Recommended for Simplicity)

For low-intensity applications, keeping everything on Render is simpler and sufficient. Skip Vercel deployment.

---

## PWA Configuration

### Step 1: Generate PWA Icons

1. **Prepare a logo image** (512x512 pixels minimum, square, PNG format)

2. **Generate icons**:
   ```bash
   python generate_pwa_icons.py your-logo.png
   ```

3. **Verify icons** are in `static/icons/` directory:
   - icon-72x72.png
   - icon-96x96.png
   - icon-128x128.png
   - icon-144x144.png
   - icon-152x152.png
   - icon-192x192.png
   - icon-384x384.png
   - icon-512x512.png

### Step 2: Verify PWA Files

Ensure these files exist and are committed:
- ✅ `static/manifest.json` - Web app manifest
- ✅ `static/js/service-worker.js` - Service worker for offline support
- ✅ `templates/base.html` - Includes PWA meta tags
- ✅ `static/js/main.js` - Includes service worker registration

### Step 3: Test PWA Features

1. **Deploy to Render** (as per steps above)

2. **Test in Browser**:
   - Open Chrome DevTools → Application → Manifest
   - Verify manifest loads correctly
   - Check Service Worker registration in Console
   - Test offline mode (DevTools → Network → Offline)

3. **Install PWA**:
   - On desktop: Look for install icon in address bar
   - On mobile: Use browser's "Add to Home Screen" option
   - Verify app opens in standalone mode

---

## PostgreSQL Database Setup

### Database Configuration

Your `config.py` is already configured to use PostgreSQL in production:

```python
class ProductionConfig(Config):
    DEBUG = False
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
```

### Database Migrations

After deployment, run migrations if you have any:

```bash
# In Render Shell
python migrate_db_vendor_fields.py  # If you added vendor fields
python migrate_db_ocr_fields.py     # If you added OCR fields
```

### Database Backups

**Render Free Tier**: Automatic backups (90 days retention)

**Manual Backup** (via Render Shell):
```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

---

## Environment Variables

### Required Variables (Set in Render Dashboard)

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `production` |
| `SECRET_KEY` | Flask secret key | `generated-64-char-hex-string` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:port/db` |
| `PORT` | Server port (auto-set by Render) | `10000` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STATIC_URL` | CDN URL for static assets (if using Vercel) | Empty (uses relative paths) |
| `MAX_CONTENT_LENGTH` | Max upload size (bytes) | `16777216` (16MB) |

### Generating SECRET_KEY

```bash
# Python
python -c "import secrets; print(secrets.token_hex(32))"

# Or use online generator (not recommended for production)
```

---

## Post-Deployment Steps

### 1. Verify Deployment

- [ ] App loads at Render URL
- [ ] Can login with default credentials
- [ ] All routes accessible
- [ ] Static files (CSS, JS, images) load correctly
- [ ] Database operations work (create, read, update, delete)

### 2. Test PWA Features

- [ ] Manifest loads (`/static/manifest.json`)
- [ ] Service worker registers (check browser console)
- [ ] Offline mode works (test with DevTools → Network → Offline)
- [ ] App can be installed (desktop/mobile)
- [ ] App opens in standalone mode when installed

### 3. Security Checklist

- [ ] Changed default admin password
- [ ] Strong `SECRET_KEY` set
- [ ] HTTPS enabled (automatic on Render)
- [ ] Database credentials secure (not in code)
- [ ] Environment variables set correctly
- [ ] File upload limits configured
- [ ] CORS settings reviewed (if needed)

### 4. Performance Optimization

- [ ] Enable Gunicorn workers (already in Procfile)
- [ ] Static files cached (service worker handles this)
- [ ] Database queries optimized
- [ ] Large file uploads handled (consider cloud storage for production)

---

## Troubleshooting

### Issue: App crashes on startup

**Check**:
1. All environment variables are set in Render dashboard
2. Database URL is correct (use Internal URL)
3. Dependencies installed correctly (check build logs)
4. Check logs in Render dashboard → Logs tab

**Common fixes**:
- Ensure `DATABASE_URL` uses `postgresql://` not `postgres://`
- Verify `SECRET_KEY` is set
- Check Python version matches `runtime.txt`

### Issue: Database connection fails

**Solutions**:
- Use **Internal Database URL** (not External) for services on Render
- Verify database is running (Render dashboard)
- Check database credentials in environment variables
- Ensure database and web service are in same region

### Issue: Static files not loading

**Solutions**:
- Verify `static/` folder is in repository
- Check static file paths in templates use `url_for('static', ...)`
- Clear browser cache
- Check Render logs for 404 errors

### Issue: Service Worker not registering

**Check**:
1. Service worker file exists at `/service-worker.js`
2. App is served over HTTPS (required for service workers)
3. Browser console for errors
4. Service worker route in `app.py` is correct

**Fix**:
- Ensure `app.py` has route: `@app.route('/service-worker.js')`
- Verify service worker file is in `static/js/service-worker.js`
- Check browser supports service workers (all modern browsers do)

### Issue: PWA install prompt not showing

**Reasons**:
- App already installed
- Browser doesn't support PWA (use Chrome, Edge, or Safari)
- Manifest has errors (check DevTools → Application → Manifest)
- Service worker not registered
- Not served over HTTPS

**Fix**:
- Check manifest.json is valid
- Verify all required icons exist
- Test in Chrome/Edge (best PWA support)

### Issue: OCR not working

**Solutions**:
- EasyOCR requires significant resources
- On free tier, OCR might timeout
- Consider making OCR optional or using a lighter alternative
- Handle OCR errors gracefully in code

### Issue: File uploads failing

**Solutions**:
- Check `MAX_CONTENT_LENGTH` setting
- Verify upload folder permissions
- For production, consider cloud storage (AWS S3, Cloudinary)
- Check Render logs for errors

---

## Maintenance & Updates

### Regular Tasks

1. **Update Dependencies** (monthly):
   ```bash
   pip install --upgrade -r requirements.txt
   pip freeze > requirements.txt
   git add requirements.txt
   git commit -m "Update dependencies"
   git push
   ```

2. **Database Backups**:
   - Render free tier: Automatic (90 days)
   - Manual: Use Render Shell to run `pg_dump`

3. **Monitor Logs**:
   - Check Render dashboard → Logs regularly
   - Set up error alerts if available
   - Monitor database usage

4. **Security Updates**:
   - Keep dependencies updated
   - Review and rotate `SECRET_KEY` periodically
   - Monitor for security advisories

### Updating the Application

1. **Make changes locally**
2. **Test thoroughly**
3. **Commit and push to GitHub**:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```
4. **Render auto-deploys** on push to main branch
5. **Verify deployment** after build completes

### Scaling Considerations

**Free Tier Limits**:
- Render: 750 hours/month, spins down after 15 min inactivity
- PostgreSQL: 1 GB storage, 90 days retention

**When to Upgrade**:
- Consistent traffic (no spin-downs)
- Larger database (>1 GB)
- Need longer backup retention
- Require dedicated resources

---

## Cost Comparison

| Service | Free Tier | Database | Best For |
|---------|-----------|----------|----------|
| **Render** | 750 hrs/month | PostgreSQL (90 days) | **Recommended** - Production ready |
| **Vercel** | Unlimited (static) | N/A | Static assets/CDN (optional) |

**Total Cost**: $0/month (free tier sufficient for low-intensity apps)

---

## Support & Resources

### Platform Documentation

- **Render**: https://render.com/docs
- **Vercel**: https://vercel.com/docs
- **PostgreSQL**: https://www.postgresql.org/docs/

### PWA Resources

- **MDN PWA Guide**: https://developer.mozilla.org/en-US/docs/Web/Progressive_Web_Apps
- **Web.dev PWA**: https://web.dev/progressive-web-apps/
- **PWA Builder**: https://www.pwabuilder.com/

### Application Issues

- Check logs in Render dashboard
- Review error messages in browser console
- Verify environment variables
- Test locally with production config

---

## Quick Start Checklist

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] PostgreSQL database created on Render
- [ ] Web service deployed on Render
- [ ] Environment variables configured
- [ ] Database initialized (`init_db.py`, `seed.py`)
- [ ] PWA icons generated and committed
- [ ] App tested and working
- [ ] PWA features verified (manifest, service worker, install)
- [ ] Default passwords changed
- [ ] Security checklist completed

---

## Next Steps

1. ✅ Deploy backend to Render
2. ✅ Set up PostgreSQL database
3. ✅ Configure environment variables
4. ✅ Initialize database
5. ✅ Generate and add PWA icons
6. ✅ Test PWA installation
7. ✅ Share deployment URL with team
8. ✅ Set up monitoring and alerts (optional)

---

**Congratulations!** Your Skanda Credit & Billing System is now deployed as a production-ready Progressive Web App! 🎉
