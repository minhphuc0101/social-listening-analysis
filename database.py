import os
import hashlib
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from dotenv import load_dotenv
import pandas as pd
import datetime

load_dotenv()

def get_database_url(conn_str=None):
    url = conn_str or os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                if "NEON_DATABASE_URL" in st.secrets:
                    url = st.secrets["NEON_DATABASE_URL"]
                elif "DATABASE_URL" in st.secrets:
                    url = st.secrets["DATABASE_URL"]
                elif "postgres" in st.secrets and "url" in st.secrets["postgres"]:
                    url = st.secrets["postgres"]["url"]
        except Exception:
            pass
    if not url:
        return None
    if "channel_binding=" in url:
        url = url.split("&channel_binding=")[0].split("?channel_binding=")[0]
    if "?" not in url and "sslmode=require" not in url:
        url += "?sslmode=require"
    return url

def get_connection(conn_str=None):
    url = get_database_url(conn_str)
    if not url:
        return None
    return psycopg2.connect(url, connect_timeout=6)

def init_db(conn_str=None):
    """Initializes tables and indexes in Neon PostgreSQL."""
    try:
        conn = get_connection(conn_str)
        if not conn:
            return False
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS social_discussions (
                        id SERIAL PRIMARY KEY,
                        url_comment TEXT,
                        content TEXT,
                        description TEXT,
                        published_at TIMESTAMP WITH TIME ZONE,
                        raw_published_date TEXT,
                        sentiment VARCHAR(20) DEFAULT 'NEUTRAL',
                        topic_pillar VARCHAR(50) DEFAULT 'Sản phẩm',
                        topic_category VARCHAR(100) DEFAULT 'Đánh giá sản phẩm',
                        car_model VARCHAR(100) DEFAULT 'Khác',
                        tags TEXT[],
                        site_name VARCHAR(50) DEFAULT 'Facebook',
                        channel VARCHAR(150) DEFAULT 'Facebook Pages',
                        author TEXT DEFAULT 'Unknown',
                        post_type VARCHAR(50) DEFAULT 'Comment',
                        content_hash VARCHAR(64) UNIQUE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );

                    CREATE INDEX IF NOT EXISTS idx_sd_published_at ON social_discussions(published_at);
                    CREATE INDEX IF NOT EXISTS idx_sd_pillar ON social_discussions(topic_pillar);
                    CREATE INDEX IF NOT EXISTS idx_sd_topic ON social_discussions(topic_category);
                    CREATE INDEX IF NOT EXISTS idx_sd_model ON social_discussions(car_model);
                    CREATE INDEX IF NOT EXISTS idx_sd_sentiment ON social_discussions(sentiment);
                    CREATE INDEX IF NOT EXISTS idx_sd_url ON social_discussions(url_comment);
                    CREATE INDEX IF NOT EXISTS idx_sd_hash ON social_discussions(content_hash);

                    CREATE TABLE IF NOT EXISTS daily_summaries (
                        id SERIAL PRIMARY KEY,
                        report_date DATE UNIQUE,
                        lookback_hours INT DEFAULT 48,
                        executive_tldr TEXT,
                        hot_topics_markdown TEXT,
                        customer_voice_markdown TEXT,
                        model_momentum_markdown TEXT,
                        full_report_markdown TEXT,
                        metadata_json JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );

                    CREATE INDEX IF NOT EXISTS idx_ds_date ON daily_summaries(report_date);
                """)
        return True
    except Exception as e:
        # Fallback to local
        return False

# -------------------------------------------------------------
# LOCAL FALLBACK CACHED DATA LOADER
# -------------------------------------------------------------
_LOCAL_CACHE_DF = None

def load_local_fallback_data():
    global _LOCAL_CACHE_DF
    if _LOCAL_CACHE_DF is not None:
        return _LOCAL_CACHE_DF

    col_remap = {
        'UrlComment': 'url_comment',
        'Content': 'content',
        'Description': 'description',
        'SiteName': 'site_name',
        'Author': 'author',
        'Type': 'post_type',
        'PublishedDate': 'raw_published_date',
        'Sentiment': 'sentiment',
        'Channel': 'channel'
    }

    # 1. Fast path: check bundled parquet file
    seed_paths = [
        "data_seed.parquet",
        "analytics/data_seed.parquet",
        "../data_seed.parquet"
    ]
    for sp in seed_paths:
        if os.path.exists(sp):
            try:
                df = pd.read_parquet(sp)
                for old_c, new_c in col_remap.items():
                    if old_c in df.columns and new_c not in df.columns:
                        df[new_c] = df[old_c]
                _LOCAL_CACHE_DF = df
                return _LOCAL_CACHE_DF
            except Exception:
                pass

    # 2. Excel fallback
    from analysis_engine import enrich_social_record

    candidate_paths = [
        "FB_Crawler_Packaged/social_media_output_autoforum_20260908.xlsx",
        "../FB_Crawler_Packaged/social_media_output_autoforum_20260908.xlsx",
        "social_comments_output.xlsx",
        "../social_comments_output.xlsx",
        "unified_social_comments.xlsx",
        "../unified_social_comments.xlsx"
    ]
    
    excel_path = None
    for p in candidate_paths:
        if os.path.exists(p):
            excel_path = p
            break

    if not excel_path:
        return pd.DataFrame(columns=[
            'id', 'url_comment', 'content', 'description', 'published_at',
            'raw_published_date', 'sentiment', 'topic_pillar', 'topic_category',
            'car_model', 'tags', 'site_name', 'channel', 'author', 'post_type'
        ])

    try:
        df_raw = pd.read_excel(excel_path)
        mtime = os.path.getmtime(excel_path)
        file_dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc)

        enriched_rows = []
        for idx, row in df_raw.head(8000).iterrows():
            r_dict = {k: ("" if pd.isna(v) else v) for k, v in row.to_dict().items()}
            enriched = enrich_social_record(r_dict, reference_time=file_dt)
            enriched_rows.append(enriched)

        df = pd.DataFrame(enriched_rows)
        for old_c, new_c in col_remap.items():
            if old_c in df.columns and new_c not in df.columns:
                df[new_c] = df[old_c]
        _LOCAL_CACHE_DF = df
        return _LOCAL_CACHE_DF
    except Exception:
        return pd.DataFrame(columns=[
            'id', 'url_comment', 'content', 'description', 'published_at',
            'raw_published_date', 'sentiment', 'topic_pillar', 'topic_category',
            'car_model', 'tags', 'site_name', 'channel', 'author', 'post_type'
        ])

def get_discussions_df(lookback_hours=None, start_date=None, end_date=None, pillar=None, topic=None, car_model=None, sentiment=None, channel=None, limit=15000):
    """
    Fetches discussions from Neon DB with automatic fallback to local enriched data.
    Uses native psycopg2 cursor for maximum speed and compatibility.
    """
    try:
        conn = get_connection()
        if conn:
            conditions = []
            params = []
            
            if lookback_hours:
                conditions.append(f"published_at >= NOW() - INTERVAL '{int(lookback_hours)} hours'")
            if start_date:
                conditions.append("published_at >= %s")
                params.append(start_date)
            if end_date:
                conditions.append("published_at <= %s")
                params.append(f"{end_date} 23:59:59" if len(str(end_date)) == 10 else end_date)
            if pillar and pillar not in ("All", "Tất cả"):
                conditions.append("topic_pillar = %s")
                params.append(pillar)
            if topic and topic not in ("All", "Tất cả"):
                conditions.append("topic_category = %s")
                params.append(topic)
            if car_model and car_model not in ("All", "Tất cả"):
                conditions.append("car_model = %s")
                params.append(car_model)
            if sentiment and sentiment not in ("All", "Tất cả"):
                conditions.append("sentiment = %s")
                params.append(sentiment.upper())
            if channel and channel not in ("All", "Tất cả"):
                conditions.append("channel = %s")
                params.append(channel)

            where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            sql = f"""
                SELECT 
                    id, url_comment, content, description, published_at, raw_published_date,
                    sentiment, topic_pillar, topic_category, car_model, tags, site_name, channel, author, post_type
                FROM social_discussions
                {where_clause}
                ORDER BY published_at DESC NULLS LAST
                LIMIT {int(limit)};
            """
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, tuple(params) if params else None)
                rows = cur.fetchall()
                if rows:
                    return pd.DataFrame(rows)
    except Exception:
        pass

    # Local fallback
    df = load_local_fallback_data().copy()
    if df.empty:
        return df

    if topic and topic not in ("All", "Tất cả") and "topic_category" in df.columns:
        df = df[df["topic_category"] == topic]
    if pillar and pillar not in ("All", "Tất cả") and "topic_pillar" in df.columns:
        df = df[df["topic_pillar"] == pillar]
    if car_model and car_model not in ("All", "Tất cả") and "car_model" in df.columns:
        df = df[df["car_model"] == car_model]
    if sentiment and sentiment not in ("All", "Tất cả") and "sentiment" in df.columns:
        df = df[df["sentiment"] == sentiment.upper()]
    if channel and channel not in ("All", "Tất cả") and "channel" in df.columns:
        df = df[df["channel"] == channel]
    if lookback_hours and "published_at" in df.columns:
        try:
            max_dt = pd.to_datetime(df["published_at"]).max()
            now_dt = datetime.datetime.now(datetime.timezone.utc)
            base_time = max(now_dt, max_dt) if pd.notna(max_dt) else now_dt
            cutoff = base_time - datetime.timedelta(hours=int(lookback_hours))
            df = df[pd.to_datetime(df["published_at"]) >= cutoff]
        except Exception:
            pass
    if start_date and "published_at" in df.columns:
        try:
            s_dt = pd.to_datetime(start_date)
            if s_dt.tzinfo is None:
                s_dt = s_dt.tz_localize(datetime.timezone.utc)
            df = df[pd.to_datetime(df["published_at"]) >= s_dt]
        except Exception:
            pass
    if end_date and "published_at" in df.columns:
        try:
            e_str = f"{end_date} 23:59:59" if len(str(end_date)) == 10 else str(end_date)
            e_dt = pd.to_datetime(e_str)
            if e_dt.tzinfo is None:
                e_dt = e_dt.tz_localize(datetime.timezone.utc)
            df = df[pd.to_datetime(df["published_at"]) <= e_dt]
        except Exception:
            pass

    return df.head(limit)

def get_db_stats():
    """Returns database statistics with fallback."""
    try:
        conn = get_connection()
        if conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(*) FILTER (WHERE post_type ILIKE '%post%') as total_posts,
                        COUNT(*) FILTER (WHERE post_type ILIKE '%comment%') as total_comments,
                        COUNT(DISTINCT channel) as unique_channels,
                        COUNT(DISTINCT url_comment) as unique_threads,
                        MIN(published_at) as oldest_post,
                        MAX(published_at) as newest_post,
                        COUNT(*) FILTER (WHERE published_at >= NOW() - INTERVAL '48 hours') as last_48h_count
                    FROM social_discussions;
                """)
                stats = cur.fetchone()
                if stats and stats["total_records"] > 0:
                    stats["source"] = "Neon Cloud PostgreSQL"
                    return stats
    except Exception:
        pass

    df = load_local_fallback_data()
    return {
        "total_records": len(df),
        "total_posts": len(df[df.get("post_type", "").astype(str).str.contains("post", case=False, na=False)]),
        "total_comments": len(df[df.get("post_type", "").astype(str).str.contains("comment", case=False, na=False)]),
        "unique_channels": df["channel"].nunique() if "channel" in df.columns else 1,
        "unique_threads": df["url_comment"].nunique() if "url_comment" in df.columns else 0,
        "oldest_post": df["published_at"].min() if "published_at" in df.columns and not df.empty else None,
        "newest_post": df["published_at"].max() if "published_at" in df.columns and not df.empty else None,
        "last_48h_count": len(df),
        "source": "Local Storage (Neon password reset in progress)"
    }

def get_latest_daily_summary():
    try:
        conn = get_connection()
        if conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM daily_summaries
                    ORDER BY report_date DESC, created_at DESC
                    LIMIT 1;
                """)
                res = cur.fetchone()
                if res:
                    return res
    except Exception:
        pass

    # Read from local reports
    report_candidates = ["reports/daily_summary_2026-09-09.md", "../reports/daily_summary_2026-09-09.md"]
    for rp in report_candidates:
        if os.path.exists(rp):
            with open(rp, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "report_date": "2026-09-09",
                "lookback_hours": 48,
                "full_report_markdown": content
            }
    return None

def save_daily_summary(report_date, lookback_hours, tldr, hot_topics, voice, momentum, full_report, metadata=None):
    import json
    meta_json = json.dumps(metadata or {}, ensure_ascii=False)
    try:
        conn = get_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO daily_summaries (
                        report_date, lookback_hours, executive_tldr, hot_topics_markdown,
                        customer_voice_markdown, model_momentum_markdown, full_report_markdown, metadata_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (report_date) DO UPDATE SET
                        lookback_hours = EXCLUDED.lookback_hours,
                        executive_tldr = EXCLUDED.executive_tldr,
                        hot_topics_markdown = EXCLUDED.hot_topics_markdown,
                        customer_voice_markdown = EXCLUDED.customer_voice_markdown,
                        model_momentum_markdown = EXCLUDED.model_momentum_markdown,
                        full_report_markdown = EXCLUDED.full_report_markdown,
                        metadata_json = EXCLUDED.metadata_json,
                        created_at = NOW();
                """, (report_date, lookback_hours, tldr, hot_topics, voice, momentum, full_report, meta_json))
                conn.commit()
    except Exception:
        pass
