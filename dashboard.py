import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import os
import sys

# Page configuration
st.set_page_config(
    page_title="AutoPulse AI - Realtime Social Intelligence",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1E3A8A, #3B82F6, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #64748B;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0F172A;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        margin-top: 0.2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        padding: 8px 18px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

from database import (
    get_discussions_df, get_db_stats, get_latest_daily_summary,
    get_all_daily_summaries, get_transfer_logs, init_db
)
from ai_scanner import run_48h_scan

# Ensure DB tables exist
try:
    init_db()
except Exception as e:
    st.error(f"Database Connection Error: {e}")
    st.stop()

# -------------------------------------------------------------
# SIDEBAR CONTROLS
# -------------------------------------------------------------
st.sidebar.markdown("### ⚙️ Điều Khiển & Bộ Lọc")

# Database health badge
stats = get_db_stats() or {}
st.sidebar.markdown(f"""
<div style="background:#F1F5F9; border-radius:8px; padding:10px; margin-bottom:15px; border:1px solid #CBD5E1;">
    <div style="font-size:0.8rem; color:#475569; font-weight:bold;">🟢 NEON POSTGRESQL KẾT NỐI</div>
    <div style="font-size:1.1rem; font-weight:800; color:#0F172A;">{stats.get('total_records', 0):,} bản ghi</div>
    <div style="font-size:0.75rem; color:#64748B;">{stats.get('total_posts', 0):,} bài viết | {stats.get('total_comments', 0):,} bình luận</div>
</div>
""", unsafe_allow_html=True)

# Time Range Filter
time_filter = st.sidebar.selectbox(
    "⏱️ Khoảng thời gian phân tích:",
    options=["🔥 48 Giờ Qua (Mặc định)", "⚡ 24 Giờ Qua", "📅 7 Ngày Qua", "🌐 Toàn Bộ Dữ Liệu"],
    index=0
)

lookback_hours = None
if "48 Giờ" in time_filter:
    lookback_hours = 48
elif "24 Giờ" in time_filter:
    lookback_hours = 24
elif "7 Ngày" in time_filter:
    lookback_hours = 168

# Topic & Model Filter
topic_options = ["All", "Giá bán & Khuyến mãi", "Động cơ & Vận hành", "Bảo hiểm & Đăng kiểm", "Trang bị & Phụ kiện", "So sánh & Tư vấn xe", "Độ xe & Kỹ thuật", "Chất lượng & Bảo dưỡng", "Cộng đồng & Đời sống"]
selected_topic = st.sidebar.selectbox("📂 Chủ đề thảo luận:", topic_options)

model_options = ["All", "Mitsubishi Xforce", "Mitsubishi Pajero Sport", "Mitsubishi Xpander", "VinFast VF6", "VinFast VF8", "Skoda Kushaq", "Mercedes-Benz W212 / E400", "Ford Ranger / Everest", "Toyota Yaris Cross"]
selected_model = st.sidebar.selectbox("🚘 Dòng xe:", model_options)

sentiment_options = ["All", "POSITIVE", "NEUTRAL", "NEGATIVE"]
selected_sentiment = st.sidebar.selectbox("🎭 Cảm xúc:", sentiment_options)

# Auto-refresh option
auto_refresh = st.sidebar.checkbox("🔄 Tự động làm mới (60 giây)", value=False)
if auto_refresh:
    st.sidebar.caption("Đang bật chế độ tự động đồng bộ thời gian thực.")

st.sidebar.divider()
st.sidebar.markdown("💡 **Cơ sở dữ liệu:** Neon Serverless Cloud")
st.sidebar.caption("Hệ thống tự động phát hiện thảo luận nóng, xu hướng phân khúc B/C và các tranh luận nổi bật.")

# -------------------------------------------------------------
# DATA LOADING
# -------------------------------------------------------------
@st.cache_data(ttl=15)
def load_data(lookback, topic, model, sentiment):
    return get_discussions_df(
        lookback_hours=lookback,
        topic=topic if topic != "All" else None,
        car_model=model if model != "All" else None,
        sentiment=sentiment if sentiment != "All" else None,
        limit=10000
    )

df = load_data(lookback_hours, selected_topic, selected_model, selected_sentiment)

# If 48h filter yields 0 records due to date offsets, fallback to recent 1000 records
if df.empty and lookback_hours:
    df = get_discussions_df(limit=3000)

# Header Title
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<div class="main-header">🚗 AutoPulse AI - Realtime Social Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Phân tích xu hướng thảo luận ô tô đa kênh thời gian thực & Quét nhanh báo cáo AI 48H</div>', unsafe_allow_html=True)
with col_h2:
    st.markdown("<div style='text-align:right; padding-top:10px;'>", unsafe_allow_html=True)
    if st.button("🔄 Làm mới dữ liệu", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# TOP KPI METRICS BAR
# -------------------------------------------------------------
total_rows = len(df)
posts_count = len(df[df['post_type'].str.contains('post', case=False, na=False)])
comments_count = len(df[df['post_type'].str.contains('comment', case=False, na=False)])
threads_count = df['url_comment'].nunique() if 'url_comment' in df.columns else 0

sent_counts = df['sentiment'].value_counts()
pos_pct = round((sent_counts.get('POSITIVE', 0) / total_rows * 100) if total_rows else 0, 1)
neg_pct = round((sent_counts.get('NEGATIVE', 0) / total_rows * 100) if total_rows else 0, 1)
neu_pct = round((sent_counts.get('NEUTRAL', 0) / total_rows * 100) if total_rows else 0, 1)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{total_rows:,}</div><div class="metric-lbl">Tổng Thảo Luận</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#2563EB;">{posts_count:,}</div><div class="metric-lbl">Bài Viết Gốc</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#059669;">{comments_count:,}</div><div class="metric-lbl">Bình Luận</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#D97706;">{threads_count:,}</div><div class="metric-lbl">Luồng Thảo Luận</div></div>', unsafe_allow_html=True)
with k5:
    st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#10B981;">{pos_pct}% <span style="color:#EF4444; font-size:1.1rem;">/ {neg_pct}%</span></div><div class="metric-lbl">Tích Cực / Tiêu Cực</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------
# MAIN TABS
# -------------------------------------------------------------
tab_dashboard, tab_scanner, tab_explorer, tab_db = st.tabs([
    "📊 Realtime Topic Radar",
    "🤖 Daily AI Scan (48H Briefing)",
    "🔍 Thread & Comment Explorer",
    "⚙️ Database & Crawler Hub"
])

# =============================================================
# TAB 1: REALTIME TOPIC RADAR
# =============================================================
with tab_dashboard:
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("📌 Tỷ trọng các Chủ đề Thảo luận")
        topic_counts = df['topic_category'].value_counts().reset_index()
        topic_counts.columns = ['Chủ đề', 'Số lượng']
        fig_topic = px.pie(
            topic_counts,
            names='Chủ đề',
            values='Số lượng',
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_topic.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=350)
        st.plotly_chart(fig_topic, use_container_width=True)

    with c2:
        st.subheader("🚘 Ma trận Cảm xúc theo Dòng xe")
        model_df = df[df['car_model'] != 'Khác']
        if not model_df.empty:
            model_sent = model_df.groupby(['car_model', 'sentiment']).size().reset_index(name='Số lượng')
            fig_sent = px.bar(
                model_sent,
                x='car_model',
                y='Số lượng',
                color='sentiment',
                barmode='stack',
                color_discrete_map={'POSITIVE': '#10B981', 'NEUTRAL': '#94A3B8', 'NEGATIVE': '#EF4444'},
                labels={'car_model': 'Dòng xe', 'Số lượng': 'Lượng thảo luận', 'sentiment': 'Cảm xúc'}
            )
            fig_sent.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=350, xaxis_tickangle=-30)
            st.plotly_chart(fig_sent, use_container_width=True)
        else:
            st.info("Chưa có đủ dữ liệu theo dòng xe cụ thể để vẽ biểu đồ cảm xúc.")

    st.divider()

    # Timeline activity chart
    st.subheader("📈 Xu hướng Thảo luận theo Thời gian")
    df_time = df[df['published_at'].notna()].copy()
    if not df_time.empty:
        df_time['hour'] = pd.to_datetime(df_time['published_at']).dt.floor('h')
        hourly_counts = df_time.groupby(['hour', 'topic_category']).size().reset_index(name='Lượt thảo luận')
        fig_time = px.area(
            hourly_counts,
            x='hour',
            y='Lượt thảo luận',
            color='topic_category',
            labels={'hour': 'Thời gian (Giờ)', 'Lượt thảo luận': 'Số bài/bình luận'},
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_time.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=340)
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.caption("Dữ liệu mốc thời gian chi tiết đang được cập nhật từ các bài viết mới.")

# =============================================================
# TAB 2: DAILY AI SCAN (48H BRIEFING)
# =============================================================
with tab_scanner:
    col_scan1, col_scan2 = st.columns([2, 1])
    with col_scan1:
        st.subheader("⚡ Báo Cáo Tóm Tắt Nhanh AI Scan (48 Giờ Qua)")
        st.caption("Quét toàn bộ tương tác 48h, phát hiện các luồng thảo luận nóng, phản ánh khách hàng & đề xuất hành động.")
    with col_scan2:
        st.markdown("<div style='text-align:right;'>", unsafe_allow_html=True)
        if st.button("🚀 Chạy Quét AI 48H Mới", type="primary", use_container_width=True):
            with st.spinner("Đang tổng hợp dữ liệu 48h và tạo báo cáo thông minh..."):
                run_48h_scan()
                st.success("Đã hoàn tất bản quét 48h mới nhất!")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Fetch latest summary from Neon
    latest_summary = get_latest_daily_summary()
    
    if latest_summary:
        st.info(f"📅 **Ngày báo cáo:** {latest_summary.get('report_date')} | **Khung thời gian:** {latest_summary.get('lookback_hours', 48)} giờ qua")
        
        # Render the full report
        report_content = latest_summary.get('full_report_markdown', '')
        st.markdown(report_content)
        
        # Export options
        st.divider()
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            st.download_button(
                "📥 Tải Báo Cáo Markdown (.md)",
                data=report_content,
                file_name=f"auto_intelligence_48h_{latest_summary.get('report_date')}.md",
                mime="text/markdown"
            )
        with col_exp2:
            html_content = f"<html><head><meta charset='utf-8'><title>48H Auto Intelligence</title></head><body style='font-family:sans-serif; line-height:1.6; padding:30px;'>{report_content.replace(chr(10), '<br>')}</body></html>"
            st.download_button(
                "🌐 Tải Báo Cáo HTML (.html)",
                data=html_content,
                file_name=f"auto_intelligence_48h_{latest_summary.get('report_date')}.html",
                mime="text/html"
            )
    else:
        st.warning("Chưa có báo cáo 48h nào được lưu. Hãy bấm '🚀 Chạy Quét AI 48H Mới' để khởi tạo ngay!")

# =============================================================
# TAB 3: THREAD & COMMENT EXPLORER
# =============================================================
with tab_explorer:
    st.subheader("🔍 Khám phá Chi tiết Từng Bài viết & Bình luận")
    
    search_query = st.text_input("🔎 Tìm kiếm nội dung thảo luận (ví dụ: 'Kushaq', 'bảo hiểm', 'đăng kiểm', 'máy 1.0', 'Xforce'):", "")
    
    display_df = df.copy()
    if search_query:
        display_df = display_df[
            display_df['content'].str.contains(search_query, case=False, na=False) |
            display_df['description'].str.contains(search_query, case=False, na=False) |
            display_df['author'].str.contains(search_query, case=False, na=False)
        ]

    st.write(f"Hiển thị **{len(display_df):,}** bản ghi phù hợp.")

    # Top Viral Threads view
    st.markdown("#### 🔥 Các Luồng Thảo Luận Sôi Nổi Nhất")
    if 'url_comment' in display_df.columns:
        top_threads = display_df.groupby('url_comment').size().sort_values(ascending=False).head(5)
        for url, count in top_threads.items():
            thread_rows = display_df[display_df['url_comment'] == url]
            desc = thread_rows['description'].dropna().iloc[0] if len(thread_rows['description'].dropna()) > 0 else "Không có tiêu đề"
            chan = thread_rows['channel'].dropna().iloc[0] if len(thread_rows['channel'].dropna()) > 0 else "Community"
            
            with st.expander(f"💬 [{count} phản hồi] - {chan}: {desc[:120]}..."):
                st.markdown(f"**Nội dung bài viết gốc:**\n> {desc}")
                st.markdown(f"🔗 [Mở bài viết trên Facebook]({url})")
                st.markdown("**Các bình luận tiêu biểu:**")
                comments = thread_rows[thread_rows['post_type'].str.contains('comment', case=False, na=False)].head(8)
                for idx, r in comments.iterrows():
                    sent_badge = "🟢" if r['sentiment'] == "POSITIVE" else ("🔴" if r['sentiment'] == "NEGATIVE" else "⚪")
                    st.markdown(f"- {sent_badge} **{r['author']}**: {r['content']}")

    st.divider()
    st.markdown("#### 📋 Bảng Dữ Liệu Chi Tiết")
    table_cols = ['published_at', 'group_name', 'channel', 'car_model', 'topic_category', 'sentiment', 'author', 'post_type', 'content', 'url_comment']
    available_cols = [c for c in table_cols if c in display_df.columns]
    st.dataframe(
        display_df[available_cols].head(300),
        use_container_width=True,
        height=400
    )

# =============================================================
# TAB 4: DATABASE & CRAWLER HUB
# =============================================================
with tab_db:
    st.subheader("⚙️ Quản Trị Cơ Sở Dữ Liệu & Nguồn Thu Thập")
    
    st.markdown("""
    Hệ thống sử dụng **Neon Serverless PostgreSQL** để lưu trữ tập trung dữ liệu mạng xã hội:
    - **Tốc độ truy vấn**: < 50ms cho các phép tổng hợp hàng chục nghìn bản ghi.
    - **Khả năng mở rộng**: Lưu trữ hàng triệu bài viết & bình luận không giới hạn dung lượng như Google Sheets.
    - **Sẵn sàng triển khai Online 24/7**: Dashboard có thể đưa lên Streamlit Community Cloud hoặc mở link xem ngay qua Cloudflare Tunnel.
    """)
    
    c_s1, c_s2 = st.columns(2)
    with c_s1:
        st.markdown("### 📊 Thống Kê Database")
        db_s = get_db_stats() or {}
        st.json(db_s)
    
    with c_s2:
        st.markdown("### 🌐 Hướng Dẫn Đưa Lên Mạng (Online)")
        st.markdown("""
        **Cách 1: Mở link Public HTTPS ngay từ máy tính (Instant Tunnel)**
        - Chạy file `Start_Online_Dashboard.bat` trong thư mục dự án.
        - Hệ thống sẽ tự động tạo một đường link HTTPS an toàn (Cloudflare Tunnel) để truy cập từ điện thoại hoặc gửi cho đồng nghiệp.
        
        **Cách 2: Đưa lên Streamlit Community Cloud (Chạy 24/7)**
        - Push mã nguồn lên GitHub.
        - Đăng nhập [share.streamlit.io](https://share.streamlit.io) và liên kết repo.
        - Thêm Secret: `NEON_DATABASE_URL` trong mục Advanced Settings.
        """)

    st.divider()
    st.markdown("### 📝 Nhật Ký Đẩy Dữ Liệu Tự Động (Batch Transfer Logs)")
    st.caption("Ghi nhận chi tiết từng đợt cào dữ liệu được nạp vào Neon DB (thời gian, chiến dịch, nhóm, số dòng thêm mới, số trùng lặp, tốc độ nạp).")
    try:
        logs_df = get_transfer_logs(limit=50)
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True, height=280)
        else:
            st.info("Chưa có lượt nạp dữ liệu nào được ghi nhận.")
    except Exception as e:
        st.warning(f"Không thể tải nhật ký nạp dữ liệu: {e}")
