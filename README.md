# 🚗 AutoPulse AI - Realtime Social Intelligence & Daily 48H AI Scan

A standalone, production-ready automotive social media intelligence platform powered by **Neon Serverless PostgreSQL** and **Streamlit**.

---

## 📁 What's in this Folder

| File | Purpose |
| :--- | :--- |
| **`dashboard.py`** | Autoforum Campaign Dashboard (all auto groups, excluding Toyota Campaign). |
| **`toyota_dashboard.py`** | **Toyota Dedicated Campaign Dashboard** (Toyota Crimson theme, dedicated models & KPIs). |
| **`ai_scanner.py`** | 48-hour intelligence scan engine (Gemini AI + Local NLP). |
| **`database.py`** | High-performance Neon PostgreSQL connection & query layer with campaign isolation. |
| **`analysis_engine.py`** | Vietnamese automotive taxonomy, model detection & sentiment analysis. |
| **`run_daily_summary.py`** | CLI runner for scheduled daily scans (used by GitHub Actions). |
| **`import_to_neon.py`** | Data migration utility to ingest crawled Excel files into Neon DB. |
| **`share_online.py`** | Cloudflare Tunnel utility for instant 100% free HTTPS sharing. |
| **`requirements.txt`** | Lightweight dependencies (Streamlit, Plotly, Psycopg2, etc.). |
| **`Start_Dashboard.bat`** | 1-click launcher for **Autoforum Dashboard** (`http://localhost:8501`). |
| **`Start_Online_Dashboard.bat`** | 1-click HTTPS tunnel launcher for Autoforum Dashboard. |
| **`Start_Toyota_Dashboard.bat`** | 1-click launcher for **Toyota Campaign Dashboard** (`http://localhost:8502`). |
| **`Start_Toyota_Online_Dashboard.bat`** | 1-click HTTPS tunnel launcher for Toyota Campaign Dashboard. |
| **`.streamlit/config.toml`** | Streamlit UI theme and production server settings. |
| **`.github/workflows/`** | GitHub Actions daily cron workflow running everyday at 08:00 AM VN time. |
| **`reports/`** | Directory archiving daily executive summaries in Markdown. |

---

## 🚀 How to Run

### 1. Run Locally (Choose Your Campaign)
* **Autoforum Dashboard** (port 8501):
  ```bat
  Start_Dashboard.bat
  ```
* **Toyota Campaign Dashboard** (port 8502):
  ```bat
  Start_Toyota_Dashboard.bat
  ```

### 2. Share Online Instantly (Free Public HTTPS Link)
* For Autoforum: `Start_Online_Dashboard.bat`
* For Toyota: `Start_Toyota_Online_Dashboard.bat`

### 3. Deploy 24/7 to Streamlit Community Cloud (Free)
You can deploy **two separate independent live apps** from this single GitHub repository:
1. **App 1: Autoforum Dashboard**:
   - Main file path: `analytics/dashboard.py` (or `dashboard.py`)
2. **App 2: Toyota Campaign Dashboard**:
   - Main file path: `analytics/toyota_dashboard.py` (or `toyota_dashboard.py`)

In both apps' **Advanced Settings ➔ Secrets**, add:
```toml
NEON_DATABASE_URL = "your_neon_database_url_here"
GEMINI_API_KEY = "your_gemini_key_here"  # Optional
```

---

## ⏰ Automated Daily 48H AI Scan via GitHub Actions

This repository includes a pre-configured GitHub Actions workflow (`.github/workflows/daily_analysis.yml`):
- **Schedule:** Wakes up automatically everyday at **08:00 AM Vietnam Time (01:00 UTC)**.
- **Action:** Connects to your live Neon DB, pulls the last 48 hours of discussions, synthesizes the executive briefing, saves it into Neon's `daily_summaries` table, and commits the report to `reports/`.
- **Live Sync:** Your online dashboard automatically displays the new daily scan without requiring any server restarts!

### GitHub Secrets Required:
In your GitHub Repo ➔ **Settings** ➔ **Secrets and variables** ➔ **Actions**:
- `NEON_DATABASE_URL`: `postgresql://...`
- `GEMINI_API_KEY`: *(Optional)* For Google Gemini narrative summaries.
