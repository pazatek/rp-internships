# Email Notification Setup

This guide explains how to set up email notifications for new Research Park job postings.

## Two Ways to Get Notified

### Option 1: GitHub Built-in Notifications (Recommended - No Setup!)

**This already works!** When new jobs are posted:
1. GitHub Action commits the changes
2. GitHub automatically emails watchers (if you have email notifications enabled)
3. No configuration needed!

**To enable:**
- Watch the repo (top right → Watch)
- GitHub → Settings → Notifications → Email
- Check "Commits" notifications

### Option 2: Custom SMTP Email (Optional)

For custom email formatting or to send to a specific address:

When new jobs are detected:
1. Python script creates `new_jobs.json` with job details
2. GitHub Action checks if file exists and has content
3. Email is sent to configured recipient with job details
4. Email includes job titles, companies, and links

## Custom Email Setup (Optional)

> **Note:** GitHub already emails watchers on commits! Only use this if you want custom formatting or a specific recipient.

### 1. Go to Repository Settings

Navigate to: **Settings** → **Secrets and variables** → **Actions**

### 2. Add Required Secrets

Click **"New repository secret"** and add these:

#### SMTP Configuration

**For Gmail:**
- `SMTP_SERVER`: `smtp.gmail.com`
- `SMTP_PORT`: `587`
- `SMTP_USERNAME`: Your Gmail address (e.g., `your-email@gmail.com`)
- `SMTP_PASSWORD`: Gmail App Password ([create here](https://myaccount.google.com/apppasswords))
- `EMAIL_RECIPIENT`: Where to send notifications (e.g., `pzatek2@illinois.edu`)

**For Outlook/Office 365:**
- `SMTP_SERVER`: `smtp-mail.outlook.com`
- `SMTP_PORT`: `587`
- `SMTP_USERNAME`: Your Outlook email
- `SMTP_PASSWORD`: Your Outlook password
- `EMAIL_RECIPIENT`: Where to send notifications

### 3. Test It

1. Manually trigger the workflow: **Actions** → **Update Research Park Jobs** → **Run workflow**
2. Check your email! (May take a minute)

## Email Format

You'll receive an email like:

```
Subject: 🎓 New Research Park Jobs Posted!

🎓 3 new job posting(s) at UIUC Research Park!

• Yahoo! - Software Dev Engineer I
  https://researchpark.illinois.edu/job/software-dev-engineer-i/

• APTech - Marketing Coordinator
  https://researchpark.illinois.edu/job/marketing-coordinator/

• Boston Bioprocess - Software Engineering Intern
  https://researchpark.illinois.edu/job/spring-summer-software-engineering-intern/

View all jobs: https://github.com/pazatek/rp-internships
```

## Troubleshooting

**Not receiving emails?**
- Verify all secrets are set correctly
- Check spam/junk folder
- Ensure SMTP credentials are correct
- Check GitHub Actions logs for errors

**Gmail App Password:**
- Go to Google Account → Security → 2-Step Verification → App passwords
- Generate password for "Mail"
- Use that 16-character password (not your regular password)

## Notes

- Emails only send when **new** jobs are detected
- The `new_jobs.json` file is temporary and not committed to the repo
- Multiple recipients: Add multiple email addresses separated by commas in `EMAIL_RECIPIENT`

