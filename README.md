# 🚗 AutoPulse AI - Realtime Social Intelligence & Daily 48H AI Scan

A standalone, production-ready automotive social media intelligence platform powered by **Neon Serverless PostgreSQL** and **Streamlit**.

---

## 📁 What's in this Folder

| File | Purpose |
| :--- | :--- |
| **`dashboard.py`** | Realtime interactive Streamlit web dashboard with Plotly charts. |
| **`ai_scanner.py`** | 48-hour intelligence scan engine (Gemini AI + Local NLP). |
| **`database.py`** | High-performance Neon PostgreSQL connection & query layer. |
| **`analysis_engine.py`** | Vietnamese automotive taxonomy, model detection & sentiment analysis. |
| **`run_daily_summary.py`** | CLI runner for scheduled daily scans (used by GitHub Actions). |
| **`import_to_neon.py`** | Data migration utility to ingest crawled Excel files into Neon DB. |
| **`share_online.py`** | Cloudflare Tunnel utility for instant 100% free HTTPS sharing. |
| **`requirements.txt`** | Lightweight dependencies (Streamlit, Plotly, Psycopg2, etc.). |
| **`Start_Dashboard.bat`** | Windows 1-click local launcher (`http://localhost:8501`). |
| **`Start_Online_Dashboard.bat`** | Windows 1-click launcher with instant public HTTPS link. |
| **`.streamlit/config.toml`** | Streamlit UI theme and production server settings. |
| **`.github/workflows/`** | GitHub Actions daily cron workflow running everyday at 08:00 AM VN time. |
| **`reports/`** | Directory archiving daily executive summaries in Markdown. |

---

## 🚀 How to Run

### 1. Run Locally
Double-click:
```bat
Start_Dashboard.bat
```
The dashboard will open automatically in your browser at `http://localhost:8501`.

### 2. Share Online Instantly (Free Public HTTPS Link)
Double-click:
```bat
Start_Online_Dashboard.bat
```
It starts the dashboard and automatically prints a secure public HTTPS URL (via Cloudflare Tunnel) that you can open on your smartphone or share with teammates anywhere.

### 3. Deploy 24/7 to Streamlit Community Cloud (Free)
1. Push this folder to your GitHub repository.
2. Visit [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Configure your app:
   - **Repository:** Your repo name
   - **Main file path:** `analytics/dashboard.py` (or `dashboard.py` if pushing this folder directly)
4. In **Advanced Settings ➔ Secrets**, add:
   ```toml
   NEON_DATABASE_URL = "your_neon_database_url_here"
   GEMINI_API_KEY = "your_gemini_key_here"  # Optional
   ```
5. Click **Deploy**!

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
