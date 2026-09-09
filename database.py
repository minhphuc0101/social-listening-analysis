import os
import hashlib
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

DEFAULT_NEON_URL = "postgresql://neondb_owner:npg_mwlJ7K6vWkMA@ep-holy-shape-aze8zqv1-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

def get_database_url(conn_str=None):
    url = conn_str or os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL") or DEFAULT_NEON_URL
    if "channel_binding=" in url:
        url = url.split("&channel_binding=")[0].split("?channel_binding=")[0]
    if "?" not in url and "sslmode=require" not in url:
        url += "?sslmode=require"
    return url

def get_connection(conn_str=None):
    return psycopg2.connect(get_database_url(conn_str))

def init_db(conn_str=None):
    """Initializes tables and indexes in Neon PostgreSQL."""
    with get_connection(conn_str) as conn:
        with conn.cursor() as cur:
            # 1. Social Discussions Table (Enriched Analytics Schema)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS social_discussions (
                    id SERIAL PRIMARY KEY,
                    url_comment TEXT,
                    group_name VARCHAR(255),
                    campaign VARCHAR(100),
                    content TEXT,
                    description TEXT,
                    published_at TIMESTAMP WITH TIME ZONE,
                    raw_published_date TEXT,
                    sentiment VARCHAR(20) DEFAULT 'NEUTRAL',
                    topic_category VARCHAR(100) DEFAULT 'Tổng quan',
                    car_model VARCHAR(100) DEFAULT 'Khác',
                    tags TEXT[],
                    site_name VARCHAR(50) DEFAULT 'Facebook',
                    channel VARCHAR(150) DEFAULT 'Community',
                    author TEXT DEFAULT 'Unknown',
                    post_type VARCHAR(50) DEFAULT 'Comment',
                    content_hash VARCHAR(64) UNIQUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                ALTER TABLE social_discussions ADD COLUMN IF NOT EXISTS group_name VARCHAR(255);
                ALTER TABLE social_discussions ADD COLUMN IF NOT EXISTS campaign VARCHAR(100);

                CREATE INDEX IF NOT EXISTS idx_sd_published_at ON social_discussions(published_at);
                CREATE INDEX IF NOT EXISTS idx_sd_topic ON social_discussions(topic_category);
                CREATE INDEX IF NOT EXISTS idx_sd_model ON social_discussions(car_model);
                CREATE INDEX IF NOT EXISTS idx_sd_sentiment ON social_discussions(sentiment);
                CREATE INDEX IF NOT EXISTS idx_sd_url ON social_discussions(url_comment);
                CREATE INDEX IF NOT EXISTS idx_sd_hash ON social_discussions(content_hash);
                CREATE INDEX IF NOT EXISTS idx_sd_group_name ON social_discussions(group_name);
                CREATE INDEX IF NOT EXISTS idx_sd_campaign ON social_discussions(campaign);

                -- 2. Social Media Posts Table (Raw Crawler Schema)
                CREATE TABLE IF NOT EXISTS social_media_posts (
                    id BIGSERIAL PRIMARY KEY,
                    campaign VARCHAR(100) NOT NULL,
                    group_name VARCHAR(255),
                    url_comment TEXT NOT NULL,
                    content TEXT,
                    description TEXT,
                    published_date TEXT,
                    sentiment VARCHAR(50),
                    channel VARCHAR(100),
                    author VARCHAR(255),
                    type VARCHAR(50),
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_social_posts_unique 
                ON social_media_posts (url_comment, md5(COALESCE(content, '')));

                -- 3. Daily Summaries Table
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

                -- 4. Batch Transfer Logs Table
                CREATE TABLE IF NOT EXISTS batch_transfer_logs (
                    id BIGSERIAL PRIMARY KEY,
                    campaign VARCHAR(100),
                    target_url TEXT,
                    group_name VARCHAR(255),
                    total_rows INT DEFAULT 0,
                    inserted_count INT DEFAULT 0,
                    duplicate_count INT DEFAULT 0,
                    status VARCHAR(50) DEFAULT 'SUCCESS',
                    error_message TEXT,
                    execution_time_ms INT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_btl_created_at ON batch_transfer_logs(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_btl_campaign ON batch_transfer_logs(campaign);
            """)
            conn.commit()
    print("[Neon DB] Tables and indexes verified and initialized.")

def compute_hash(url_comment, content, author=""):
    raw = f"{str(url_comment).strip()}||{str(content).strip()}||{str(author).strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def insert_discussions_batch(rows, batch_size=500, conn_str=None):
    """Batch inserts social discussions and crawler posts with atomic deduplication."""
    if not rows:
        return 0, 0

    init_db(conn_str)
    
    insert_discussions_sql = """
        INSERT INTO social_discussions (
            url_comment, group_name, campaign, content, description, published_at, raw_published_date,
            sentiment, topic_category, car_model, tags, site_name,
            channel, author, post_type, content_hash
        ) VALUES %s
        ON CONFLICT (content_hash) DO NOTHING
    """

    insert_posts_sql = """
        INSERT INTO social_media_posts (
            campaign, group_name, url_comment, content, description,
            published_date, sentiment, channel, author, type
        ) VALUES %s
        ON CONFLICT (url_comment, md5(COALESCE(content, ''))) DO NOTHING
    """
    
    disc_records = []
    post_records = []

    for r in rows:
        u_com = str(r.get("UrlComment", "") or r.get("url_comment", "")).strip()
        grp = str(r.get("GroupName", "") or r.get("group_name", "")).strip()
        camp = str(r.get("Campaign", "") or r.get("campaign", "") or r.get("Channel", "") or "General").strip()
        cnt = str(r.get("Content", "") or r.get("content", "")).strip()
        desc = str(r.get("Description", "") or r.get("description", "")).strip()
        p_at = r.get("published_at")
        r_date = str(r.get("PublishedDate", "") or r.get("raw_published_date", "")).strip()
        sent = str(r.get("Sentiment", "") or r.get("sentiment", "NEUTRAL")).upper().strip()
        if sent not in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
            sent = "NEUTRAL"
        topic = str(r.get("topic_category", "") or r.get("Lable 1", "") or "Tổng quan").strip()
        model = str(r.get("car_model", "") or r.get("Tag 1", "") or "Khác").strip()
        tags = r.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        site = str(r.get("SiteName", "") or r.get("site_name", "Facebook")).strip()
        chan = str(r.get("Channel", "") or r.get("channel", "Community")).strip()
        auth = str(r.get("Author", "") or r.get("author", "Unknown")).strip()
        p_type = str(r.get("Type", "") or r.get("post_type", "Comment")).strip()
        c_hash = r.get("content_hash") or compute_hash(u_com, cnt, auth)

        disc_records.append((
            u_com, grp, camp, cnt, desc, p_at, r_date,
            sent, topic, model, tags, site,
            chan, auth, p_type, c_hash
        ))

        post_records.append((
            camp, grp, u_com, cnt, desc,
            r_date, sent, chan, auth, p_type
        ))

    total_inserted = 0
    with get_connection(conn_str) as conn:
        with conn.cursor() as cur:
            for i in range(0, len(disc_records), batch_size):
                chunk_disc = disc_records[i:i + batch_size]
                chunk_posts = post_records[i:i + batch_size]
                execute_values(cur, insert_discussions_sql, chunk_disc)
                total_inserted += cur.rowcount
                execute_values(cur, insert_posts_sql, chunk_posts)
            conn.commit()
            
    print(f"[Neon DB] Processed {len(disc_records)} records. New rows inserted: {total_inserted}")
    return total_inserted, len(disc_records) - total_inserted

def get_db_stats():
    """Returns overall DB metrics."""
    with get_connection() as conn:
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
            return cur.fetchone()

def get_discussions_df(lookback_hours=None, topic=None, car_model=None, sentiment=None, channel=None, group_name=None, limit=15000):
    """Queries social discussions into a Pandas DataFrame."""
    conditions = []
    params = []
    
    if lookback_hours:
        conditions.append(f"published_at >= NOW() - INTERVAL '{int(lookback_hours)} hours'")
    if topic and topic != "All":
        conditions.append("topic_category = %s")
        params.append(topic)
    if car_model and car_model != "All":
        conditions.append("car_model = %s")
        params.append(car_model)
    if sentiment and sentiment != "All":
        conditions.append("sentiment = %s")
        params.append(sentiment.upper())
    if channel and channel != "All":
        conditions.append("channel = %s")
        params.append(channel)
    if group_name and group_name != "All":
        conditions.append("group_name = %s")
        params.append(group_name)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""
        SELECT 
            id, url_comment, group_name, campaign, content, description, published_at, raw_published_date,
            sentiment, topic_category, car_model, tags, site_name, channel, author, post_type
        FROM social_discussions
        {where_clause}
        ORDER BY published_at DESC NULLS LAST
        LIMIT {int(limit)};
    """
    
    with get_connection() as conn:
        df = pd.read_sql_query(sql, conn, params=params)
    return df

def save_daily_summary(report_date, lookback_hours, tldr, hot_topics, voice, momentum, full_report, metadata=None):
    """Upserts a daily AI briefing into Neon DB."""
    import json
    meta_json = json.dumps(metadata or {}, ensure_ascii=False)
    sql = """
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
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (report_date, lookback_hours, tldr, hot_topics, voice, momentum, full_report, meta_json))
            conn.commit()
    print(f"[Neon DB] Saved daily summary for {report_date}")

def get_latest_daily_summary():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM daily_summaries
                ORDER BY report_date DESC, created_at DESC
                LIMIT 1;
            """)
            return cur.fetchone()

def get_all_daily_summaries(limit=30):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, report_date, lookback_hours, executive_tldr, created_at
                FROM daily_summaries
                ORDER BY report_date DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

def log_batch_transfer(campaign, target_url, group_name, total_rows, inserted_count, duplicate_count, status="SUCCESS", error_message=None, execution_time_ms=None, conn_str=None):
    """Records a batch transfer event into batch_transfer_logs."""
    try:
        init_db(conn_str)
        with get_connection(conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO batch_transfer_logs (
                        campaign, target_url, group_name, total_rows,
                        inserted_count, duplicate_count, status, error_message,
                        execution_time_ms
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    campaign or "General",
                    target_url or "",
                    group_name or "",
                    total_rows or 0,
                    inserted_count or 0,
                    duplicate_count or 0,
                    status,
                    error_message,
                    execution_time_ms
                ))
                conn.commit()
    except Exception as e:
        print(f"[Neon Log Error] Failed to write batch transfer log: {e}")

def get_transfer_logs(limit=50, campaign=None, conn_str=None):
    """Retrieves latest batch transfer logs into a Pandas DataFrame."""
    conditions = []
    params = []
    if campaign and campaign != "All":
        conditions.append("campaign = %s")
        params.append(campaign)
    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    
    sql = f"""
        SELECT 
            id, created_at, campaign, group_name, total_rows, inserted_count, duplicate_count, status, execution_time_ms, target_url, error_message
        FROM batch_transfer_logs
        {where_clause}
        ORDER BY created_at DESC
        LIMIT {int(limit)};
    """
    with get_connection(conn_str) as conn:
        df = pd.read_sql_query(sql, conn, params=params)
    return df

if __name__ == "__main__":
    init_db()
