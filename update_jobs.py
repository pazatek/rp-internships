#!/usr/bin/env python3
"""
Simple script that checks the Research Park job board and posts updates.
Runs on GitHub Actions to notify people when new jobs get posted.
"""

import json
import ssl
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import feedparser
from bs4 import BeautifulSoup
import re

RSS_FEED_URL = "https://researchpark.illinois.edu/?feed=job_feed"
JOBS_FILE = "jobs.json"
README_FILE = "README.md"

README_TEMPLATE = """# UIUC Research Park Jobs

Auto-updated job listings from the [University of Illinois Research Park](https://researchpark.illinois.edu).

**Updated:** {last_updated} | **Total:** {total_positions}

---

| Logo | Company | Position | Posted | Link |
| :---: | ------- | -------- | ------ | ---- |
{job_table}

{posting_stats}

---

## About This Project

This repository automatically monitors the Research Park job feed and updates every hour.

- **Source:** [Research Park Job Board](https://researchpark.illinois.edu/work-here/careers/)

### How It Works

1. Python script fetches the RSS feed hourly
2. Compares against cached job listings
3. GitHub automatically commits and pushes any changes to this README

### Get Notifications

**Watch this repository** to get notified when new jobs are added:

- Click "Watch" at the top of this repo
- Select "Custom" → Check "Commits"
- You'll get a notification every time new jobs are posted!

---

_Built with Python • Automated with GitHub Actions_
"""

def load_existing_jobs():
    """Load jobs we already know about from the cache file."""
    if not Path(JOBS_FILE).exists():
        return []
    with open(JOBS_FILE, 'r') as f:
        return json.load(f)

def save_jobs(jobs):
    """Save the current job list to a file so we remember them next time."""
    with open(JOBS_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)

def fetch_rss_page(page=1):
    """Grab one page of jobs from the RSS feed."""
    url = f"{RSS_FEED_URL}&paged={page}" if page > 1 else RSS_FEED_URL
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    for use_ssl_verification in [True, False]:
        try:
            context = ssl.create_default_context() if use_ssl_verification else ssl._create_unverified_context()
            with urllib.request.urlopen(req, context=context) as response:
                return feedparser.parse(response.read())
        except Exception as e:
            if not use_ssl_verification:
                print(f"Error fetching RSS page {page}: {e}")
                return None
    return None

def parse_job_board():
    """Go through all the pages of the job board and collect all the jobs."""
    jobs = []
    page = 1
    max_pages = 20  # Safety limit
    
    while page <= max_pages:
        feed = fetch_rss_page(page)
        if not feed or not feed.entries:
            break
        
        page_jobs = []
        for entry in feed.entries:
            company = entry.get('job_listing_company', 'N/A')
            job_id = entry.get('guid', entry.link)

            # Fetch logo for this job
            logo_url = fetch_logo_for_job(entry.link, company)

            job = {
                "id": job_id,
                "company": company,
                "position": entry.title,
                "link": entry.link,
                "posted_date": entry.get('published', ''),
                "published_parsed": entry.get('published_parsed'),
                "logo_url": logo_url
            }
            page_jobs.append(job)
        
        if not page_jobs:
            break
        
        jobs.extend(page_jobs)
        print(f"  Page {page}: found {len(page_jobs)} jobs (total: {len(jobs)})")
        
        # Check if there are more pages by looking for next page indicator
        if len(page_jobs) < 10:  # Typically 10 jobs per page
            break
        
        page += 1
    
    return jobs

def find_new_jobs(current_jobs, existing_jobs):
    """Figure out which jobs are new since last time we checked."""
    seen_ids = {job['id'] for job in existing_jobs}
    return [job for job in current_jobs if job['id'] not in seen_ids]

def get_company_logo(job):
    """Try to fetch company logo from job page, or return placeholder."""
    logo_url = job.get('logo_url', '')
    if logo_url:
        return f"<img src=\"{logo_url}\" alt=\"{job['company']}\" width=\"50\">"
    return "???"

def fetch_logo_for_job(job_link, company_name):
    """Try to fetch logo URL from job page or tenant directory."""
    # Method 1: Try job page
    logo = fetch_logo_from_page(job_link, company_name)
    if logo:
        return logo

    # Method 2: Try tenant directory page (company name might be in URL format)
    # Convert company name to URL slug (e.g., "RationalCyPhy Inc" -> "rational-cyphy")
    tenant_slug = re.sub(r'[^a-z0-9]+', '-', company_name.lower()).strip('-')
    tenant_url = f"https://researchpark.illinois.edu/tenant-directory/{tenant_slug}/"
    logo = fetch_logo_from_page(tenant_url, company_name)
    if logo:
        return logo

    return None

def fetch_logo_from_page(url, company_name):
    """Fetch logo from a specific page."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context, timeout=5) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            # Method 1: Look for company-logo div with img inside
            company_logo_div = soup.find('div', class_='company-logo')
            if company_logo_div:
                img = company_logo_div.find('img')
                if img and img.get('src'):
                    src = img.get('src')
                    return normalize_logo_url(src)

                # Check for background image in style
                style = company_logo_div.get('style', '')
                if 'background-image' in style:
                    match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                    if match:
                        return normalize_logo_url(match.group(1))

            # Method 2: Look for images in wp-content/uploads directory
            company_normalized = re.sub(r'[^a-z0-9]', '', company_name.lower())
            company_words = [w for w in company_name.lower().split() if len(w) > 2]

            for img in soup.find_all('img'):
                src = img.get('src', '')
                if not src or 'wp-content/uploads' not in src.lower():
                    continue

                filename = src.split('/')[-1].lower()
                filename_clean = re.sub(r'[^a-z0-9]', '', filename)

                # Skip obvious non-logo images
                if any(skip in filename for skip in ['wordmark', 'illinois', 'untitled', 'elementor', 'color-variation']):
                    continue

                # Match if: contains "logo" OR has "150x" (thumbnail size) AND matches company name
                has_logo_keyword = 'logo' in filename
                has_thumbnail_size = '150x' in filename

                # Company name matching - be more strict
                company_match = False
                if company_words:
                    # Check if any significant company word is in filename
                    for word in company_words:
                        if len(word) > 4 and word in filename_clean:
                            company_match = True
                            break
                    # Also check first 6 chars of normalized company name
                    if not company_match and len(company_normalized) > 5:
                        company_match = company_normalized[:6] in filename_clean

                # Only accept if it's clearly a logo (has logo keyword or thumbnail) AND matches company
                is_logo = (has_logo_keyword or has_thumbnail_size) and company_match

                # If no company match but has logo keyword/thumbnail, still accept (might be generic logo)
                if not is_logo and (has_logo_keyword or has_thumbnail_size):
                    is_logo = True

                if is_logo:
                    return normalize_logo_url(src)
    except:
        pass
    return None

def normalize_logo_url(src):
    """Normalize logo URL to full URL."""
    if not src:
        return None
    if src.startswith('/'):
        return f"https://researchpark.illinois.edu{src}"
    elif src.startswith('http'):
        return src
    return None


def format_posted_date(posted_date_str, published_parsed=None):
    """Turn the raw date from RSS into something readable like 'Nov 5, 2025 3:45 PM CST'."""
    if not posted_date_str or posted_date_str == 'N/A':
        return 'N/A'
    
    # Try the parsed date first, it's usually the most reliable
    if published_parsed:
        try:
            dt = datetime(*published_parsed[:6], tzinfo=ZoneInfo('UTC'))
            cst = ZoneInfo('America/Chicago')
            dt_cst = dt.astimezone(cst)
            return dt_cst.strftime('%b %d, %Y %I:%M %p CST')
        except:
            pass
    
    # If that didn't work, try parsing the raw date string
    try:
        # Try RFC 2822 format (common in RSS)
        import email.utils
        timestamp = email.utils.parsedate_tz(posted_date_str)
        if timestamp:
            dt = datetime(*timestamp[:6], tzinfo=ZoneInfo('UTC'))
            cst = ZoneInfo('America/Chicago')
            dt_cst = dt.astimezone(cst)
            return dt_cst.strftime('%b %d, %Y %I:%M %p CST')
    except:
        pass
    
    # Fallback: try ISO format
    try:
        dt_str = posted_date_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo:
            cst = ZoneInfo('America/Chicago')
            dt = dt.astimezone(cst)
        else:
            dt = dt.replace(tzinfo=ZoneInfo('America/Chicago'))
        return dt.strftime('%b %d, %Y %I:%M %p CST')
    except:
        # Last resort: return shortened version
        return posted_date_str[:16] if len(posted_date_str) > 16 else posted_date_str

def generate_posting_insights(jobs):
    """Generate insights about posting times to help users know when to check."""
    posting_hours = []

    for job in jobs:
        published_parsed = job.get('published_parsed')
        if not published_parsed:
            continue

        try:
            # Parse from published_parsed tuple [year, month, day, hour, minute, second, ...]
            dt = datetime(*published_parsed[:6], tzinfo=ZoneInfo('UTC'))
            cst = ZoneInfo('America/Chicago')
            dt_cst = dt.astimezone(cst)
            posting_hours.append(dt_cst.hour)  # Get hour in CST (0-23)
        except:
            continue

    if len(posting_hours) < 3:
        return None  # Not enough data

    # Count jobs per hour
    hour_counts = {}
    for hour in posting_hours:
        hour_counts[hour] = hour_counts.get(hour, 0) + 1

    return posting_hours, hour_counts

def generate_posting_chart(jobs):
    """Generate a Mermaid bar chart showing posting time distribution."""
    result = generate_posting_insights(jobs)
    if not result:
        return None

    posting_hours, hour_counts = result

    # Create data for chart (only hours with at least 1 job)
    labels = []
    data = []
    for hour in range(24):
        count = hour_counts.get(hour, 0)
        if count > 0:  # Only include hours with jobs
            # Format hour labels
            if hour == 0:
                label = "12 AM"
            elif hour < 12:
                label = f"{hour} AM"
            elif hour == 12:
                label = "12 PM"
            else:
                label = f"{hour - 12} PM"
            labels.append(label)
            data.append(count)

    # Create a simple, clean Unicode bar chart
    max_value = max(data) if data else 1
    max_bar_length = 40  # Maximum bar length in characters

    chart_lines = [
        f"## Posting Time Distribution",
        "",
        f"### Job Posting Times (Based on {len(posting_hours)} postings)",
        "",
        "```",
        "Jobs",
        ""
    ]

    # Create bars using Unicode block characters
    for label, count in zip(labels, data):
        bar_length = int((count / max_value) * max_bar_length) if max_value > 0 else 0
        bar = "█" * bar_length
        chart_lines.append(f"{label:>6} │{bar} {count}")

    chart_lines.extend([
        "       └" + "─" * max_bar_length,
        "        0" + " " * (max_bar_length - 1) + str(max_value),
        "```"
    ])

    return "\n".join(chart_lines)

def update_readme(jobs):
    """Update the README file with the latest job listings."""
    # Sort by published_parsed tuple in reverse chronological order (newest first)
    sorted_jobs = sorted(jobs, key=lambda x: x.get('published_parsed') or (0, 0, 0, 0, 0, 0), reverse=True)

    table_rows = []
    for job in sorted_jobs:
        position = job['position'].replace('|', '-')
        company = job['company'].replace('|', '-')
        logo = get_company_logo(job)
        posted = format_posted_date(job.get('posted_date', ''), job.get('published_parsed'))
        link = job['link']
        table_rows.append(f"| {logo} | {company} | {position} | {posted} | [Apply]({link}) |")

    table_rows = '\n'.join(table_rows)

    cst = ZoneInfo('America/Chicago')
    cst_time = datetime.now(cst)
    last_updated = cst_time.strftime('%B %d, %Y at %I:%M %p CST')

    # Generate posting time chart and insights
    chart_url = generate_posting_chart(jobs)
    insights_result = generate_posting_insights(jobs)
    stats_text = ""
    if chart_url and insights_result:
        posting_hours, hour_counts = insights_result
        n = len(posting_hours)

        # Find peak hour
        peak_hour, peak_count = max(hour_counts.items(), key=lambda x: x[1])

        # Format hours
        def format_hour(hour):
            if hour == 0:
                return "12 AM"
            elif hour < 12:
                return f"{hour} AM"
            elif hour == 12:
                return "12 PM"
            else:
                return f"{hour - 12} PM"

        peak_formatted = format_hour(peak_hour)

        # Find time range where most jobs are posted (80% percentile)
        sorted_hours = sorted(posting_hours)
        p10_idx = int(n * 0.1)
        p90_idx = int(n * 0.9)
        start_hour = sorted_hours[p10_idx]
        end_hour = sorted_hours[p90_idx]

        # Count jobs in the main range
        in_range = sum(1 for h in posting_hours if start_hour <= h <= end_hour)
        pct_in_range = (in_range / n) * 100

        # Format insights
        range_text = f"{format_hour(start_hour)} - {format_hour(end_hour)}"
        if start_hour == end_hour:
            range_text = format_hour(start_hour)

        insights_lines = [
            f"**Peak posting time:** {peak_formatted} ({peak_count} of {n} jobs)",
            f"**{pct_in_range:.0f}% of jobs** posted between {range_text} (CST)",
        ]

        insights_text = "\n".join(insights_lines)

        stats_text = f"""
{chart_url}
"""

    readme_content = README_TEMPLATE.format(
        last_updated=last_updated,
        total_positions=len(jobs),
        job_table=table_rows,
        posting_stats=stats_text
    )

    with open(README_FILE, 'w') as f:
        f.write(readme_content)

def main():
    print("=" * 60)
    print("🎓 UIUC Research Park Job Monitor")
    print("=" * 60 + "\n")
    
    print("Fetching all job listings from job board...")
    current_jobs = parse_job_board()
    existing_jobs = load_existing_jobs()
    
    # Add discovered_date and preserve logo_url from existing jobs
    existing_ids = {job['id'] for job in existing_jobs}
    existing_jobs_dict = {job['id']: job for job in existing_jobs}

    for job in current_jobs:
        if job['id'] not in existing_ids:
            job['discovered_date'] = datetime.now().isoformat()
        else:
            # Preserve discovered_date and logo_url from existing job
            existing_job = existing_jobs_dict.get(job['id'])
            if existing_job:
                if 'discovered_date' in existing_job:
                    job['discovered_date'] = existing_job['discovered_date']
                # Keep cached logo if we have one, otherwise use newly fetched
                if existing_job.get('logo_url') and not job.get('logo_url'):
                    job['logo_url'] = existing_job['logo_url']
    
    new_jobs = find_new_jobs(current_jobs, existing_jobs)
    
    if new_jobs:
        print(f"🎉 {len(new_jobs)} new job(s) detected:")
        for job in new_jobs:
            print(f"  • {job['company']} - {job['position']}")
        with open('new_jobs.json', 'w') as f:
            json.dump(new_jobs, f, indent=2)
    else:
        print(f"✓ No new jobs (scanned {len(current_jobs)} listings)")
        Path('new_jobs.json').touch()
    
    update_readme(current_jobs)
    save_jobs(current_jobs)
    print("\n" + "=" * 60)
    print("✅ Update complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

