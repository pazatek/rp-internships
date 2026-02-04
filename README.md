# Research Park Jobs

Monitors the [University of Illinois Research Park Job Board](https://researchpark.illinois.edu/work-here/careers/) for new internships and job postings. Provides a web dashboard and email notifications.

## Architecture

- **GitHub Actions** (cron every 15 min) — scrapes RSS feed, detects new jobs, sends email notifications, commits updated `jobs.json`
- **Vercel** (Flask) — job board UI, subscriber management, unsubscribe handling
- **Supabase PostgreSQL** — subscriber table shared by both systems
- **Gmail SMTP** — email delivery for job notifications

## Features

- **Web Dashboard**: View all current job listings at a glance
- **Email Alerts**: Subscribe via the web UI, unsubscribe via link in every email
- **Auto-Updates**: GitHub Actions checks for new jobs every 15 minutes during business hours
- **Company Logos**: Fetched from Research Park tenant directory pages

## Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**
   ```bash
   export DATABASE_URL="postgresql://..."
   export EMAIL_SENDER="your@gmail.com"
   export EMAIL_PASSWORD="your-app-password"
   export APP_URL="https://your-app.vercel.app"
   ```

3. **Run the web app**
   ```bash
   python app.py
   ```
   Open [http://localhost:5001](http://localhost:5001).

## Deployment

1. Create a **Supabase** project (free tier) and get the Session Pooler connection string
2. Deploy to **Vercel** — connect this repo, add `DATABASE_URL` env var
3. Add **GitHub Secrets**: `DATABASE_URL`, `EMAIL_SENDER`, `EMAIL_PASSWORD`, `APP_URL`

## Project Structure

- `app.py` — Flask web application (job board UI, subscribe/unsubscribe)
- `update_jobs.py` — Scraping, detection, and email notification (runs in GitHub Actions)
- `database.py` — Shared PostgreSQL module for subscriber management
- `templates/` — HTML templates
- `vercel.json` — Vercel deployment config
