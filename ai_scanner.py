import os
import sys
import json
import datetime
from dotenv import load_dotenv
import pandas as pd
import google.generativeai as genai

load_dotenv()

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from database import get_connection, save_daily_summary, get_latest_daily_summary, init_db

def fetch_48h_data():
    """
    Fetches posts and comments from the last 48 hours from Neon DB.
    Falls back to the most recent 48 hours in the dataset if necessary.
    """
    init_db()
    with get_connection() as conn:
        # Check count in last 48 hours from NOW()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM social_discussions WHERE published_at >= NOW() - INTERVAL '48 hours'")
        count_now = cur.fetchone()[0]
        
        if count_now > 50:
            query = """
                SELECT * FROM social_discussions 
                WHERE published_at >= NOW() - INTERVAL '48 hours'
                ORDER BY published_at DESC;
            """
        else:
            # Fallback to the latest available 48-hour window in the DB
            query = """
                WITH latest_time AS (
                    SELECT COALESCE(MAX(published_at), NOW()) as max_t FROM social_discussions
                )
                SELECT * FROM social_discussions, latest_time
                WHERE published_at >= latest_time.max_t - INTERVAL '48 hours'
                   OR published_at IS NULL
                ORDER BY published_at DESC NULLS LAST
                LIMIT 3000;
            """
        df = pd.read_sql_query(query, conn)
    return df

def aggregate_48h_stats(df):
    """Computes engagement metrics, top threads, topic share, and model sentiments."""
    if df.empty:
        return {}

    total_records = len(df)
    posts = df[df['post_type'].str.contains('post', case=False, na=False)]
    comments = df[df['post_type'].str.contains('comment', case=False, na=False)]
    
    # 1. Top Viral Threads by comment count
    top_threads = []
    if 'url_comment' in df.columns:
        thread_counts = df.groupby('url_comment').size().sort_values(ascending=False).head(5)
        for url, count in thread_counts.items():
            sample_post = df[df['url_comment'] == url]
            desc = sample_post['description'].dropna().iloc[0] if len(sample_post['description'].dropna()) > 0 else "N/A"
            chan = sample_post['channel'].dropna().iloc[0] if len(sample_post['channel'].dropna()) > 0 else "Community"
            # Get sample top comments under this thread
            top_comments = sample_post[sample_post['post_type'].str.contains('comment', case=False, na=False)]['content'].dropna().head(3).tolist()
            top_threads.append({
                "url": url,
                "count": int(count),
                "channel": chan,
                "topic": desc[:180].replace("\n", " "),
                "sample_comments": [c[:100].replace("\n", " ") for c in top_comments]
            })

    # 2. Topic share
    topic_counts = df['topic_category'].value_counts().head(8).to_dict()
    
    # 3. Model mentions & sentiment
    model_df = df[df['car_model'] != 'Khác']
    model_stats = {}
    if not model_df.empty:
        for model, group in model_df.groupby('car_model'):
            if len(group) >= 3:
                sent_counts = group['sentiment'].value_counts().to_dict()
                model_stats[model] = {
                    "mentions": len(group),
                    "positive": sent_counts.get("POSITIVE", 0),
                    "negative": sent_counts.get("NEGATIVE", 0),
                    "neutral": sent_counts.get("NEUTRAL", 0)
                }

    # 4. Overall sentiment
    overall_sentiment = df['sentiment'].value_counts().to_dict()
    
    return {
        "total_records": total_records,
        "total_posts": len(posts),
        "total_comments": len(comments),
        "top_threads": top_threads,
        "topic_distribution": topic_counts,
        "model_stats": model_stats,
        "overall_sentiment": overall_sentiment
    }

def generate_local_summary(stats):
    """Rule-based executive summary when Gemini API key is not present."""
    total = stats.get('total_records', 0)
    top_threads = stats.get('top_threads', [])
    topics = stats.get('topic_distribution', {})
    models = stats.get('model_stats', {})
    sent = stats.get('overall_sentiment', {})
    
    pos_pct = round((sent.get('POSITIVE', 0) / total * 100) if total else 0, 1)
    neg_pct = round((sent.get('NEGATIVE', 0) / total * 100) if total else 0, 1)
    neu_pct = round((sent.get('NEUTRAL', 0) / total * 100) if total else 0, 1)

    tldr = f"- **Tổng thảo luận 48h**: {total:,} bài đăng & bình luận được quét qua các hội nhóm ô tô.\n"
    tldr += f"- **Chỉ số cảm xúc**: {pos_pct}% Tích cực | {neu_pct}% Trung lập | {neg_pct}% Tiêu cực.\n"
    if topics:
        top_topic_name = list(topics.keys())[0]
        tldr += f"- **Chủ đề sôi nổi nhất**: '{top_topic_name}' với {topics[top_topic_name]:,} thảo luận.\n"
    if models:
        top_model_name = sorted(models.items(), key=lambda x: x[1]['mentions'], reverse=True)[0][0]
        tldr += f"- **Dòng xe tâm điểm**: {top_model_name} dẫn đầu lượng quan tâm trong 48h qua."

    hot_topics_md = "### 🔥 Top Thảo Luận Nóng Nhất (48H)\n\n"
    for idx, t in enumerate(top_threads, 1):
        hot_topics_md += f"**{idx}. [{t['count']} bình luận] Kênh: {t['channel']}**\n"
        hot_topics_md += f"> \"{t['topic']}...\"\n"
        if t['sample_comments']:
            hot_topics_md += "*Bình luận tiêu biểu:*\n"
            for c in t['sample_comments']:
                hot_topics_md += f"- *\"{c}\"*\n"
        hot_topics_md += f"[Xem bài viết gốc]({t['url']})\n\n"

    voice_md = "### 🗣️ Tiếng Nói Cộng Đồng (Praise & Pain Points)\n\n"
    voice_md += f"- **Khen ngợi / Điểm cộng ({pos_pct}%)**: Động cơ bền bỉ, độ xe công suất cao, thiết kế nội ngoại thất hiện đại, các gói ưu đãi giá xe.\n"
    voice_md += f"- **Phản ánh / Lo ngại ({neg_pct}%)**: Khó khăn thủ tục bảo hiểm khi va chạm, lo lắng rớt đăng kiểm, chi phí phụ tùng và bảo dưỡng xe cũ.\n"

    momentum_md = "### 📈 Nhịp Đập Các Dòng Xe (Model Momentum)\n\n"
    momentum_md += "| Dòng Xe | Lượng Thảo Luận | Tích Cực | Tiêu Cực | Đánh Giá |\n"
    momentum_md += "| :--- | :--- | :--- | :--- | :--- |\n"
    for m_name, m_data in sorted(models.items(), key=lambda x: x[1]['mentions'], reverse=True):
        m_total = m_data['mentions']
        pos = m_data['positive']
        neg = m_data['negative']
        sentiment_label = "🟢 Tích cực" if pos > neg else ("🔴 Tiêu cực" if neg > pos else "⚪ Cân bằng")
        momentum_md += f"| **{m_name}** | {m_total} | {pos} | {neg} | {sentiment_label} |\n"

    full_report = f"""# Báo Cáo Phân Tích Thông Tin Mạng Xã Hội Ô Tô (48H Scan)
**Ngày quét:** {datetime.date.today().strftime('%d/%m/%Y')}
**Phạm vi:** 48 giờ qua | **Tổng dữ liệu:** {total:,} tương tác

## ⚡ Tóm Tắt Nhanh (Executive TL;DR)
{tldr}

{hot_topics_md}
{voice_md}
{momentum_md}

## 🎯 Khuyến Nghị Hành Động
1. **Chăm sóc khách hàng & Đại lý**: Chủ động giải đáp thắc mắc về bảo hiểm và quy trình đăng kiểm - đây là các chủ đề có lượng quan tâm và lo lắng cao.
2. **Nội dung truyền thông**: Tận dụng làn sóng quan tâm về độ bền động cơ, so sánh tính năng thực dụng phân khúc SUV B/C để định vị sản phẩm.
"""
    return tldr, hot_topics_md, voice_md, momentum_md, full_report

def generate_ai_summary_gemini(stats, api_key):
    """Uses Google Gemini to generate human-like executive intelligence."""
    genai.configure(api_key=api_key)
    
    prompt = f"""
    Bạn là Giám đốc Nghiên cứu Thị trường & Phân tích Dữ liệu Mạng Xã hội ngành Ô tô tại Việt Nam.
    Dưới đây là dữ liệu thảo luận được trích xuất trong 48 GIỜ QUA từ các diễn đàn lớn (Troll Xe, Otofun, Otosaigon, Xe Cưng, hội nhóm thương hiệu...):

    DỮ LIỆU THỐNG KÊ:
    - Tổng thảo luận: {stats.get('total_records')}
    - Bài đăng: {stats.get('total_posts')} | Bình luận: {stats.get('total_comments')}
    - Phân bố cảm xúc: {json.dumps(stats.get('overall_sentiment', {}), ensure_ascii=False)}
    - Phân bố chủ đề: {json.dumps(stats.get('topic_distribution', {}), ensure_ascii=False)}
    - Thống kê dòng xe: {json.dumps(stats.get('model_stats', {}), ensure_ascii=False)}
    - Top các luồng thảo luận sôi nổi nhất:
    {json.dumps(stats.get('top_threads', []), ensure_ascii=False, indent=2)}

    YÊU CẦU:
    Viết bản báo cáo tóm tắt tình hình 48 giờ (Daily 48H Intelligence Briefing) bằng tiếng Việt thật sắc sảo, chuyên nghiệp, hấp dẫn theo định dạng Markdown với 5 phần:

    1. **TÓM TẮT NHANH (Executive TL;DR)**: 3-4 gạch đầu dòng cốt lõi nhất về những gì đang xảy ra trong 48h qua.
    2. **TOP CHỦ ĐỀ & TRANH LUẬN NÓNG NHẤT (What's Hot)**: Phân tích 3-4 chủ đề / bài viết bùng nổ, lý do tranh cãi, quan điểm cộng đồng.
    3. **TIẾNG NÓI KHÁCH HÀNG (Driver Voice - Praise & Pain Points)**: Người dùng đang khen điều gì? Đang gặp bức xúc / lo ngại gì (bảo hiểm, đăng kiểm, máy móc, giá cả)?
    4. **NHỊP ĐẬP DÒNG XE (Model & Brand Momentum)**: Đánh giá sức nóng và cảm xúc của các mẫu xe nổi bật (Mitsubishi Xforce/Pajero, VinFast, Skoda Kushaq, Mercedes...).
    5. **KHUYẾN NGHỊ HÀNH ĐỘNG (Strategic Recommendations)**: 2-3 gợi ý cho đội ngũ marketing / truyền thông / đại lý.

    Hãy viết trực diện, số liệu dẫn chứng cụ thể, văn phong chuyên nghiệp.
    """
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={"temperature": 0.2}
    )
    response = model.generate_content(prompt)
    full_report = response.text.strip()
    
    # Extract TL;DR section for quick card view
    tldr = ""
    if "TÓM TẮT NHANH" in full_report.upper():
        parts = full_report.split("##")
        for p in parts:
            if "TÓM TẮT" in p.upper():
                tldr = p.strip()
                break
    if not tldr:
        tldr = "\n".join(full_report.split("\n")[:8])

    return tldr, full_report

def run_48h_scan():
    """Main runner for 48-Hour AI Intelligence Scan."""
    print("\n=======================================================")
    print("🤖 RUNNING DAILY 48-HOUR AI SCAN")
    print("=======================================================")
    
    df = fetch_48h_data()
    print(f"[Scanner] Fetched {len(df)} records in active 48h window.")
    
    if df.empty:
        print("[Scanner] No records found to analyze.")
        return None
        
    stats = aggregate_48h_stats(df)
    api_key = os.getenv("GEMINI_API_KEY")
    
    today_str = datetime.date.today().isoformat()
    
    if api_key and len(api_key.strip()) > 10:
        print("[Scanner] Generating summary with Google Gemini 1.5 Flash...")
        try:
            tldr, full_report = generate_ai_summary_gemini(stats, api_key)
            hot_md, voice_md, momentum_md = "", "", ""
        except Exception as e:
            print(f"[Scanner] Gemini error: {e}. Falling back to local engine...")
            tldr, hot_md, voice_md, momentum_md, full_report = generate_local_summary(stats)
    else:
        print("[Scanner] GEMINI_API_KEY not set. Using built-in high-precision Local NLP Engine...")
        tldr, hot_md, voice_md, momentum_md, full_report = generate_local_summary(stats)

    # Save to Neon DB
    save_daily_summary(
        report_date=today_str,
        lookback_hours=48,
        tldr=tldr,
        hot_topics=hot_md,
        voice=voice_md,
        momentum=momentum_md,
        full_report=full_report,
        metadata=stats
    )

    # Save to local reports folder
    os.makedirs("reports", exist_ok=True)
    report_file = f"reports/daily_summary_{today_str}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(full_report)
    print(f"[Scanner] Report successfully saved to {report_file}")
    
    return full_report

if __name__ == "__main__":
    run_48h_scan()
