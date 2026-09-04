# Deployment Guide

## Production Deployment on Render

### Prerequisites
- GitHub repository connected to Render
- PostgreSQL database (Render provides free tier)
- Redis instance (optional, for caching)
- Sentry account for error tracking (optional)

### Frontend Deployment (Vercel)

1. **Push to GitHub**
```bash
git push origin main
```

2. **Connect to Vercel**
   - Go to https://vercel.com/new
   - Select "Next.js" framework
   - Import your GitHub repository
   - Add environment variables

3. **Environment Variables (Vercel)**
```
NEXT_PUBLIC_API_URL=https://your-api.onrender.com/api
```

4. **Deploy**
   - Vercel will automatically deploy on push to main
   - Check deployment status in Vercel dashboard

### Backend Deployment (Render)

1. **Push to GitHub**
```bash
git push origin main
```

2. **Connect to Render**
   - Go to https://dashboard.render.com
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub repository
   - Select branch: `main`

3. **Configure Service**
   - **Name**: `plasticprecious-api`
   - **Runtime**: `Python 3.12`
   - **Build Command**: `bash -o pipefail -c 'pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput'`
   - **Start Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3`

4. **Environment Variables (Render)**
```
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-api.onrender.com,yourdomain.com
DATABASE_URL=postgres://user:password@host:5432/dbname
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
REDIS_URL=redis://your-redis-url:6379/0
SENTRY_DSN=your-sentry-dsn
```

5. **Create PostgreSQL Database**
   - In Render dashboard, create a PostgreSQL database
   - Copy connection string to `DATABASE_URL`

6. **Deploy**
   - Render will automatically deploy on push to main
   - Monitor logs in Render dashboard

### Post-Deployment Steps

#### 1. Create Admin User
```bash
# SSH into Render container or local development
python manage.py createsuperuser
```

#### 2. Initialize Database Content
```bash
# Create initial CMS content
python manage.py shell
```

#### 3. Set Up Email
- Configure SMTP credentials in environment variables
- Test email sending

#### 4. Set Up Monitoring
- Add Sentry DSN for error tracking
- Configure health check: `https://your-api.onrender.com/api/health/`

#### 6. SSL Certificate
- Render automatically provides free SSL via Let's Encrypt
- HTTPS is automatically enforced in production settings

### Security Checklist

- [ ] `DEBUG` is set to `False`
- [ ] `SECRET_KEY` is unique and strong
- [ ] `ALLOWED_HOSTS` includes your domain
- [ ] `CORS_ALLOWED_ORIGINS` includes only trusted domains
- [ ] SSL/HTTPS is enforced
- [ ] All credentials are environment variables
- [ ] Database backups are enabled
- [ ] Error tracking (Sentry) is configured
- [ ] Rate limiting is enabled
- [ ] Security headers are set

### Monitoring & Maintenance

#### Logs
- View logs in Render dashboard
- Check for errors and warnings

#### Database
- Monitor database size in Render
- Regular backups are recommended

#### Performance
- Monitor response times
- Use Sentry for error tracking
- Check API rate limits

#### Updates
- Keep dependencies updated
- Test updates in staging first
- Use `pip list --outdated` to check updates

### Scaling Up

If your application needs scaling:

1. **Upgrade Database Plan** (Render)
   - Increase resources as needed
   - Monitor performance

2. **Add Redis for Caching**
   - Improves API response times
   - Better for high traffic

3. **Increase Worker Processes**
   - Modify `--workers` in gunicorn command
   - Monitor memory usage

4. **Use CDN for Frontend**
   - Vercel provides built-in CDN
   - Significantly improves load times

### Troubleshooting

#### Database Connection Issues
```bash
# Check DATABASE_URL format
# Should be: postgres://user:password@host:port/dbname
```

#### Static Files Not Loading
```bash
python manage.py collectstatic --noinput
```

#### 502 Bad Gateway
- Check application logs
- Verify all environment variables are set
- Restart the service

#### CORS Errors
- Verify frontend domain is in `CORS_ALLOWED_ORIGINS`
- Check that frontend URL includes protocol (https://)

### Rollback Procedure

If you need to rollback:

1. In Render dashboard, select your service
2. Go to "Deployments" tab
3. Find the previous working deployment
4. Click "Redeploy"

### Support

- **Render Docs**: https://render.com/docs
- **Django Docs**: https://docs.djangoproject.com
- **Vercel Docs**: https://vercel.com/docs
- **Next.js Docs**: https://nextjs.org/docs
