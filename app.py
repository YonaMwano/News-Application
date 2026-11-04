"""
NewsPulse - Modern Real-time News Aggregator
Powered by Currents API (free tier allows commercial / production use)
Built with Flask | 2026 Design | Vercel ready
"""

import os
from datetime import datetime, timezone
from time import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me-in-production")

# Currents API (production-friendly free tier)
CURRENTS_API_KEY = os.getenv("CURRENTS_API_KEY") or os.getenv("NEWSAPI_KEY")
CURRENTS_BASE = "https://api.currentsapi.services/v1"

# Simple in-memory cache (TTL in seconds)
_cache = {}
CACHE_TTL = 180  # 3 minutes


def get_cached(key: str):
    entry = _cache.get(key)
    if entry and (time() - entry["ts"]) < CACHE_TTL:
        return entry["data"]
    return None


def set_cached(key: str, data):
    _cache[key] = {"data": data, "ts": time()}


def fetch_currents(endpoint: str, params: dict) -> dict | None:
    """Call Currents API with proper auth header and caching."""
    if not CURRENTS_API_KEY:
        return {
            "status": "error",
            "message": "CURRENTS_API_KEY is missing. Get a free key at https://currentsapi.services and add it to .env",
        }

    cache_key = f"{endpoint}:{sorted(params.items())}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cached

    headers = {"Authorization": f"Bearer {CURRENTS_API_KEY}"}

    try:
        resp = requests.get(
            f"{CURRENTS_BASE}/{endpoint}",
            params=params,
            headers=headers,
            timeout=12,
        )
        data = resp.json()

        if resp.status_code == 429:
            return {
                "status": "error",
                "message": "Rate limit reached (Free plan = 250 requests/day). Try again later.",
            }
        if resp.status_code != 200 or data.get("status") != "ok":
            msg = data.get("message") or data.get("error") or f"HTTP {resp.status_code}"
            return {"status": "error", "message": str(msg)}

        set_cached(cache_key, data)
        return data
    except requests.RequestException as e:
        return {"status": "error", "message": f"Network error: {str(e)}"}


def process_articles(articles: list) -> list:
    """Normalize Currents articles for the templates."""
    processed = []
    for a in articles:
        title = (a.get("title") or "").strip()
        if not title or title == "[Removed]":
            continue

        published = a.get("published") or a.get("publishedAt")
        relative = ""
        if published:
            try:
                # Currents format: "2026-03-24 11:10:00 +0000"
                dt = datetime.strptime(str(published)[:19], "%Y-%m-%d %H:%M:%S")
                dt = dt.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                seconds = int((now - dt).total_seconds())
                if seconds < 60:
                    relative = "Just now"
                elif seconds < 3600:
                    relative = f"{seconds // 60}m ago"
                elif seconds < 86400:
                    relative = f"{seconds // 3600}h ago"
                else:
                    relative = f"{seconds // 86400}d ago"
            except Exception:
                relative = str(published)[:10] if published else ""

        # Source is often missing; fall back to domain from url
        source = a.get("author") or ""
        if not source and a.get("url"):
            try:
                source = urlparse(a["url"]).netloc.replace("www.", "")
            except Exception:
                source = "Unknown"

        category_list = a.get("category") or []
        category = category_list[0] if isinstance(category_list, list) and category_list else ""

        processed.append({
            "title": title,
            "description": (a.get("description") or "")[:220].strip()
            + ("…" if a.get("description") and len(a["description"]) > 220 else ""),
            "url": a.get("url"),
            "image": a.get("image") or None,
            "source": source or "News",
            "publishedAt": published,
            "relativeTime": relative,
            "author": a.get("author") or "",
            "category": category,
        })
    return processed


# Map our UI categories to Currents (v1 compatible)
CATEGORY_MAP = {
    "general": None,
    "business": "business",
    "technology": "technology",
    "sports": "sports",
    "entertainment": "entertainment",
    "health": "health",
    "science": "science",
}


@app.route("/")
def index():
    category = request.args.get("category", "general")
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    categories = [
        ("general", "Top Stories"),
        ("business", "Business"),
        ("technology", "Technology"),
        ("sports", "Sports"),
        ("entertainment", "Entertainment"),
        ("health", "Health"),
        ("science", "Science"),
    ]

    articles = []
    total = 0
    error = None
    query_label = None

    if q:
        data = fetch_currents("search", {
            "keywords": q,
            "language": "en",
            "page_number": page,
            "page_size": 20,
        })
        query_label = f'Search: “{q}”'
    else:
        params = {
            "language": "en",
            "page_number": page,
            "page_size": 20,
        }
        mapped = CATEGORY_MAP.get(category)
        if mapped:
            params["category"] = mapped

        data = fetch_currents("latest-news", params)
        query_label = dict(categories).get(category, "Top Stories")

    if data and data.get("status") == "ok":
        articles = process_articles(data.get("news", []))
        total = len(articles) + (page - 1) * 20
        if len(articles) == 20:
            total += 20
    elif data:
        error = data.get("message", "Failed to load news")

    return render_template(
        "index.html",
        articles=articles,
        categories=categories,
        active_category=category if not q else "",
        country="us",
        query=q,
        query_label=query_label,
        error=error,
        total=total,
        page=page,
        has_more=len(articles) >= 20,
        api_key_missing=not CURRENTS_API_KEY,
    )


@app.route("/api/news")
def api_news():
    """JSON endpoint for future infinite scroll / SPA."""
    category = request.args.get("category", "general")
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    if q:
        data = fetch_currents("search", {
            "keywords": q,
            "language": "en",
            "page_number": page,
            "page_size": 20,
        })
    else:
        params = {"language": "en", "page_number": page, "page_size": 20}
        mapped = CATEGORY_MAP.get(category)
        if mapped:
            params["category"] = mapped
        data = fetch_currents("latest-news", params)

    if not data or data.get("status") != "ok":
        return jsonify({"error": data.get("message") if data else "Unknown error"}), 502

    return jsonify({
        "articles": process_articles(data.get("news", [])),
        "page": page,
    })


@app.context_processor
def inject_globals():
    return {
        "now": datetime.now(timezone.utc),
        "app_name": "NewsPulse",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")
