# NewsPulse — Modern Real-time News Aggregator

Powered by **Currents API** (free tier allows commercial & production use).  
Clean 2026 editorial design with Flask + Tailwind CSS.

![NewsPulse](https://img.shields.io/badge/Flask-3.0-black?logo=flask)  
![Currents](https://img.shields.io/badge/Currents%20API-Free%20Production-0ea5e9)  
![Vercel](https://img.shields.io/badge/Deploy-Vercel-black?logo=vercel)

---

## Why Currents API?

| Feature                    | NewsAPI.org (old)     | **Currents API** (new)      |
|---------------------------|-----------------------|-----------------------------|
| Free tier for production  | ❌ Development only   | ✅ **Allowed**              |
| Requests / day (free)     | 100                   | **250**                     |
| Results per request       | up to 100             | 20 (free)                   |
| Article delay             | ~24 hours             | Near real-time              |
| Commercial use            | Forbidden on free     | **Allowed** (with attribution) |

---

## Features

- Real-time / near real-time top headlines by category
- Full keyword search
- Beautiful responsive UI (dark/light mode, sticky header, card grid)
- 3-minute smart cache (respects free quota)
- Relative timestamps (“12m ago”)
- Image fallbacks + graceful error states
- JSON API endpoint (`/api/news`)
- Ready for Vercel (`vercel.json` included)

---

## Quick Start (Local)

### 1. Get a free Currents API key

1. Go to [https://currentsapi.services](https://currentsapi.services) → **Get free API key**
2. Create an account and copy your key

### 2. Setup

```bash
cd news_app
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env`:

```env
CURRENTS_API_KEY=your_actual_key_here
FLASK_SECRET_KEY=any-long-random-string
FLASK_ENV=development
```

### 4. Run

```bash
python app.py
```

Open → **http://127.0.0.1:5000**

---

## Deploy to Vercel

1. Push the project to GitHub
2. Import the repo at [vercel.com/new](https://vercel.com/new)
3. Add Environment Variables:

| Name                | Value                        |
|---------------------|------------------------------|
| `CURRENTS_API_KEY`  | your Currents API key        |
| `FLASK_SECRET_KEY`  | a long random string         |

4. Deploy

`vercel.json` is already configured (30s timeout, proper routing).

---

## Project Structure

```
news_app/
├── app.py              # Flask + Currents API
├── requirements.txt
├── vercel.json
├── .env.example
├── templates/
│   ├── base.html
│   └── index.html
└── README.md
```

---

## API Endpoint (JSON)

```
GET /api/news?category=technology&page=1
GET /api/news?q=openai&page=1
```

---

## Attribution note

Currents free plan allows commercial use **with attribution** and a link to the original article.  
The app already links every card to the original source URL.

---

Made for 2026. Stay informed.
