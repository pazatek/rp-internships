"""Flask web app for the UIUC Research Park Job Board."""

import logging
import re
import time

import requests
from flask import Flask, jsonify, render_template, request

from database import add_subscriber, init_db, remove_subscriber

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

AVATAR_COLORS = [
    "#E84A27", "#13294b", "#0F9D58", "#4285F4", "#DB4437",
    "#F4B400", "#7B1FA2", "#00897B", "#C2185B", "#1565C0",
]


def avatar_color(company_name: str) -> str:
    """Deterministic color from company name hash."""
    h = sum(ord(c) for c in company_name)
    return AVATAR_COLORS[h % len(AVATAR_COLORS)]


app.jinja_env.filters["avatar_color"] = avatar_color

JOBS_JSON_URL = (
    "https://raw.githubusercontent.com/pazatek/rp-internships/main/jobs.json"
)
CACHE_TTL = 300  # 5 minutes

_jobs_cache: dict = {"data": None, "fetched_at": 0.0}


def fetch_jobs() -> list[dict]:
    """Fetch jobs.json from GitHub raw URL with in-memory TTL cache."""
    now = time.time()
    if _jobs_cache["data"] is not None and now - _jobs_cache["fetched_at"] < CACHE_TTL:
        return _jobs_cache["data"]

    try:
        resp = requests.get(JOBS_JSON_URL, timeout=10)
        resp.raise_for_status()
        jobs = resp.json()
        _jobs_cache["data"] = jobs
        _jobs_cache["fetched_at"] = now
        return jobs
    except Exception as e:
        logger.error("Failed to fetch jobs.json: %s", e)
        # Return stale cache if available
        if _jobs_cache["data"] is not None:
            return _jobs_cache["data"]
        return []


def format_posted_date(posted_date_str: str, published_parsed=None) -> str:
    """Format date for display. Lightweight version for the web app."""
    if not posted_date_str or posted_date_str == "N/A":
        return "N/A"
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        if published_parsed:
            dt = datetime(*published_parsed[:6], tzinfo=ZoneInfo("UTC"))
            cst = ZoneInfo("America/Chicago")
            dt_cst = dt.astimezone(cst)
            return dt_cst.strftime("%b %d, %Y %I:%M %p CST")

        import email.utils

        timestamp = email.utils.parsedate_tz(posted_date_str)
        if timestamp:
            dt = datetime(*timestamp[:6], tzinfo=ZoneInfo("UTC"))
            cst = ZoneInfo("America/Chicago")
            dt_cst = dt.astimezone(cst)
            return dt_cst.strftime("%b %d, %Y %I:%M %p CST")
    except Exception:
        pass

    return posted_date_str[:16] if len(posted_date_str) > 16 else posted_date_str


@app.route("/")
def index():
    jobs = [dict(j) for j in fetch_jobs()]
    jobs.sort(key=lambda x: x.get("published_parsed") or [0] * 9, reverse=True)

    for job in jobs:
        job["formatted_date"] = format_posted_date(
            job.get("posted_date"), job.get("published_parsed")
        )

    return render_template("index.html", jobs=jobs)


@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json()
    if not data or not data.get("email"):
        return jsonify({"success": False, "message": "Email is required"}), 400

    email = data["email"].strip().lower()

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"success": False, "message": "Invalid email address"}), 400

    result = add_subscriber(email)
    status_code = 200 if result["success"] else 500
    return jsonify(result), status_code


@app.route("/unsubscribe")
def unsubscribe():
    token = request.args.get("token", "")
    if not token:
        return render_template("unsubscribed.html", success=False), 400

    success = remove_subscriber(token)
    return render_template("unsubscribed.html", success=success)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# Initialize DB on startup
with app.app_context():
    try:
        init_db()
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
