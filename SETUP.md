# Setup Guide

This guide will help you set up the Research Park Job Monitor to automatically track job postings.

## Quick Start

### 1. Initial Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the script manually to test
python update_jobs.py
```

This will create:

- `jobs.json` - Cached job listings
- `README.md` - Auto-generated job board

### 2. GitHub Setup

1. **Create a new GitHub repository**

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/rp-internship-notifier.git
   git push -u origin main
   ```

2. **The GitHub Action will automatically run every hour** once pushed!

### 3. Get Notifications

**Watch your repository** to get notified when new jobs are added:

1. Go to your repo on GitHub
2. Click the **"Watch"** button at the top
3. Select **"Custom"**
4. Check **"Commits"**
5. Done! You'll get a GitHub notification every time new jobs are posted

## How It Works

1. **Scheduled Updates:** GitHub Actions runs the script every hour
2. **RSS Parsing:** Script fetches the Research Park job feed
3. **Change Detection:** Compares against cached jobs to find new postings
4. **README Update:** Automatically updates the README with current listings
5. **Auto-commit:** GitHub Actions commits and pushes changes
6. **Notifications:** GitHub notifies you when the repo is updated (if watching)

## Project Structure

```
rp-internship-notifier/
├── .github/
│   └── workflows/
│       └── update.yml          # GitHub Actions workflow
├── update_jobs.py              # Main Python script
├── requirements.txt            # Python dependencies
├── jobs.json                   # Cached job data (auto-generated)
├── README.md                   # Job board (auto-generated)
└── SETUP.md                    # This file
```

## Manual Updates

To manually trigger an update:

```bash
python update_jobs.py
```

Or trigger the GitHub Action:

- Go to Actions tab → Update Research Park Jobs → Run workflow

## Customization

### Change Update Frequency

Edit `.github/workflows/update.yml`:

```yaml
schedule:
  - cron: "0 */2 * * *" # Every 2 hours
  - cron: "0 9 * * *" # Daily at 9 AM
  - cron: "0 9,17 * * *" # Twice daily at 9 AM and 5 PM
```

## Troubleshooting

**GitHub Action not running?**

- Check Actions tab for errors
- Verify workflow file is in `.github/workflows/`
- Ensure repo is public (or you have GitHub Actions minutes)

**Not receiving notifications?**

- Make sure you're "Watching" the repo with "Commits" enabled
- Check your GitHub notification settings
- Look for the bell icon at the top right of GitHub

**Script errors?**

- Run `python update_jobs.py` locally to see detailed error messages
- Check that Python 3.8+ is installed
- Verify RSS feed is accessible: https://researchpark.illinois.edu/?feed=job_feed

## Notes

- The script only tracks jobs currently in the RSS feed
- If a job is removed from the feed, it remains in `jobs.json` but won't appear in README
- GitHub commits only happen when there are actual changes to the job listings

---

**Questions?** Open an issue or check the main README.
