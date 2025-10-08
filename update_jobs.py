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

# Configuration
RSS_FEED_URL = "https://researchpark.illinois.edu/?feed=job_feed"
JOBS_FILE = "jobs.json"
README_FILE = "README.md"

def load_existing_jobs():
    """Load previously seen jobs from JSON file."""
    if Path(JOBS_FILE).exists():
        with open(JOBS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_jobs(jobs):
    """Save jobs to JSON file."""
    with open(JOBS_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)

def parse_feed():
    """Parse the RSS feed and extract job listings."""
    print(f"Fetching feed from {RSS_FEED_URL}...")
    
    # Fetch feed with a proper user agent
    req = urllib.request.Request(
        RSS_FEED_URL,
        headers={'User-Agent': 'Mozilla/5.0 (Research Park Job Monitor)'}
    )
    
    try:
        # Try with default SSL context first
        ssl_context = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ssl_context) as response:
            feed_data = response.read()
        feed = feedparser.parse(feed_data)
    except urllib.error.URLError as e:
        # Fallback for local Mac SSL certificate issues
        if 'CERTIFICATE_VERIFY_FAILED' in str(e):
            print("SSL certificate verification failed, trying without verification...")
            try:
                ssl_context = ssl._create_unverified_context()
                with urllib.request.urlopen(req, context=ssl_context) as response:
                    feed_data = response.read()
                feed = feedparser.parse(feed_data)
            except Exception as e:
                print(f"Error fetching feed on retry: {e}")
                return []
        else:
            print(f"Error fetching feed: {e}")
            return []
    except Exception as e:
        print(f"Error fetching feed: {e}")
        return []
    
    jobs = []
    for entry in feed.entries:
        # Extract company name from custom namespace
        company = entry.get('job_listing_company', 'N/A')
        
        job = {
            "id": entry.get('guid', entry.link),
            "company": company,
            "position": entry.title,
            "link": entry.link,
            "posted_date": entry.get('published', ''),
            "discovered_date": datetime.now().isoformat()
        }
        jobs.append(job)
    
    print(f"Found {len(jobs)} jobs in feed")
    return jobs

def find_new_jobs(current_jobs, existing_jobs):
    """Compare current jobs with existing jobs to find new ones."""
    existing_ids = {job['id'] for job in existing_jobs}
    new_jobs = [job for job in current_jobs if job['id'] not in existing_ids]
    print(f"Found {len(new_jobs)} new jobs")
    return new_jobs

def update_readme(jobs):
    """Update README.md with current job listings."""
    print("Updating README.md...")
    
    # Sort jobs by discovered date (newest first)
    sorted_jobs = sorted(jobs, key=lambda x: x.get('discovered_date', ''), reverse=True)
    
    readme_content = f"""# UIUC Research Park Job Board

Auto-updated job listings from the [University of Illinois Research Park](https://researchpark.illinois.edu).

**Last Updated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  
**Total Positions:** {len(jobs)}

---

## Current Openings

| Company | Position | Link |
|---------|----------|------|
"""
    
    for job in sorted_jobs:
        company = job['company'].replace('|', '-')
        position = job['position'].replace('|', '-')
        readme_content += f"| {company} | {position} | [Apply]({job['link']}) |\n"
    
    readme_content += f"""
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

*Built with Python • Automated with GitHub Actions*
"""
    
    with open(README_FILE, 'w') as f:
        f.write(readme_content)
    
    print("README.md updated successfully!")

def main():
    """Main execution function."""
    print("=" * 50)
    print("Research Park Job Monitor")
    print("=" * 50)
    
    # Parse current feed
    current_jobs = parse_feed()
    
    # Load existing jobs
    existing_jobs = load_existing_jobs()
    
    # Find new jobs
    new_jobs = find_new_jobs(current_jobs, existing_jobs)
    
    # Print new jobs if found
    if new_jobs:
        print(f"\n🎉 {len(new_jobs)} new job(s) found!")
        for job in new_jobs:
            print(f"  • {job['company']} - {job['position']}")
    else:
        print("\nNo new jobs found.")
    
    # Update README
    update_readme(current_jobs)
    
    # Save all jobs
    save_jobs(current_jobs)
    
    print("\n" + "=" * 50)
    print("Update complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()

