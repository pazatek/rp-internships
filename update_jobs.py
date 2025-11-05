#!/usr/bin/env python3
"""
Research Park Job Feed Monitor
Automatically updates job listings from UIUC Research Park RSS feed.
"""

import feedparser
import json
import ssl
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

RSS_FEED_URL = "https://researchpark.illinois.edu/?feed=job_feed"
JOBS_FILE = "jobs.json"
README_FILE = "README.md"

README_TEMPLATE = """# UIUC Research Park Job Board

Auto-updated job listings from the [University of Illinois Research Park](https://researchpark.illinois.edu).

**Last Updated:** {last_updated}  
**Total Positions:** {total_positions}

---

## Current Openings

| Company | Position | Link |
| ------- | -------- | ---- |
{job_table}

---

## About This Project

This repository automatically monitors the Research Park job feed and updates every hour.

- **Source:** [Research Park RSS Feed](https://researchpark.illinois.edu/?feed=job_feed)
- **Update Frequency:** Every hour via GitHub Actions
- **Maintained by:** Student project for tracking Research Park opportunities

### How It Works

1. Python script fetches the RSS feed hourly
2. Compares against cached job listings
3. Updates this README with any changes
4. GitHub automatically commits and pushes updates

### Get Notifications

**Watch this repository** to get notified when new jobs are added:

- Click "Watch" at the top of this repo
- Select "Custom" → Check "Commits"
- You'll get a notification every time new jobs are posted!

---

_Built with Python • Automated with GitHub Actions_
"""

def load_existing_jobs():
    """Load previously cached jobs from JSON file."""
    if not Path(JOBS_FILE).exists():
        return []
    with open(JOBS_FILE, 'r') as f:
        return json.load(f)

def save_jobs(jobs):
    """Save current job listings to JSON file."""
    with open(JOBS_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)

def parse_feed():
    """Fetch and parse the Research Park RSS feed."""
    req = urllib.request.Request(RSS_FEED_URL, headers={'User-Agent': 'Mozilla/5.0'})
    
    for use_ssl_verification in [True, False]:
        try:
            context = ssl.create_default_context() if use_ssl_verification else ssl._create_unverified_context()
            with urllib.request.urlopen(req, context=context) as response:
                feed = feedparser.parse(response.read())
                break
        except Exception as e:
            if not use_ssl_verification:
                print(f"Error fetching feed: {e}")
                return []
    
    jobs = [{
        "id": entry.get('guid', entry.link),
        "company": entry.get('job_listing_company', 'N/A'),
        "position": entry.title,
        "link": entry.link,
        "posted_date": entry.get('published', ''),
        "discovered_date": datetime.now().isoformat()
    } for entry in feed.entries]
    
    return jobs

def find_new_jobs(current_jobs, existing_jobs):
    """Compare current jobs with cached jobs to find new postings."""
    seen_ids = {job['id'] for job in existing_jobs}
    return [job for job in current_jobs if job['id'] not in seen_ids]

def update_readme(jobs):
    """Generate and write README.md with current job listings."""
    sorted_jobs = sorted(jobs, key=lambda x: x.get('discovered_date', ''), reverse=True)
    
    table_rows = '\n'.join([
        f"| {job['company'].replace('|', '-')} | {job['position'].replace('|', '-')} | [Apply]({job['link']}) |"
        for job in sorted_jobs
    ])
    
    readme_content = README_TEMPLATE.format(
        last_updated=datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        total_positions=len(jobs),
        job_table=table_rows
    )
    
    with open(README_FILE, 'w') as f:
        f.write(readme_content)

def main():
    print("=" * 60)
    print("🎓 UIUC Research Park Job Monitor")
    print("=" * 60 + "\n")
    
    current_jobs = parse_feed()
    existing_jobs = load_existing_jobs()
    new_jobs = find_new_jobs(current_jobs, existing_jobs)
    
    if new_jobs:
        print(f"🎉 {len(new_jobs)} new job(s) detected:")
        for job in new_jobs:
            print(f"  • {job['company']} - {job['position']}")
        # Write new jobs to file for GitHub Action
        with open('new_jobs.json', 'w') as f:
            json.dump(new_jobs, f, indent=2)
    else:
        print(f"✓ No new jobs (scanned {len(current_jobs)} listings)")
        # Create empty file to indicate no new jobs
        Path('new_jobs.json').touch()
    
    update_readme(current_jobs)
    save_jobs(current_jobs)
    print("\n" + "=" * 60)
    print("✅ Update complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

