import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import os
import sys

# Page Configuration
st.set_page_config(
    page_title="Dashboard - Tổng Quan Thảo Luận Mạng Xã Hội",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling to match the uploaded design
st.markdown("""
<style>
    /* Global Styles */
    body, .stApp {
        background-color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Sidebar Navigation Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
        padding-top: 1rem;
    }
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1.35rem;
        font-weight: 700;
        color: #0F766E;
        padding: 0.5rem 0.5rem 1.5rem 0.5rem;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 1rem;
    }
    
    /* Custom Card Containers */
    .dashboard-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        padding: 1.25rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    .card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* Top Bar */
    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 1rem;
        margin-bottom: 1.25rem;
        border-bottom: 1px solid #E2E8F0;
    }
    .page-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0F172A;
    }
    
    /* Discussion Feed Card */
    .feed-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 0.85rem;
        transition: all 0.2s ease;
    }
    .feed-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .feed-topic-tag {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        background: #F1F5F9;
        color: #475569;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 0.4rem;
    }
    .feed-author {
        font-weight: 700;
        color: #1E293B;
        font-size: 0.9rem;
    }
    .feed-channel {
        color: #2563EB;
        font-size: 0.85rem;
    }
    .feed-date {
        color: #94A3B8;
        font-size: 0.8rem;
    }
    .feed-content {
        color: #334155;
        font-size: 0.92rem;
        margin-top: 0.5rem;
        line-height: 1.5;
    }
    .badge-pos {
        background: #DCFCE7;
        color: #16A34A;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
    }
    .badge-neu {
        background: #F1F5F9;
        color: #64748B;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
    }
    .badge-neg {
        background: #FEE2E2;
        color: #DC2626;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

from database import get_discussions_df, get_db_stats, get_latest_daily_summary
from ai_scanner import run_48h_scan
from analysis_engine import HIERARCHICAL_TOPICS

# -------------------------------------------------------------
# SIDEBAR NAVIGATION & FILTERS
# -------------------------------------------------------------
st.sidebar.markdown("""
<div class="sidebar-brand">
    <span>🖥️</span> Dashboard
</div>
""", unsafe_allow_html=True)

nav_page = st.sidebar.radio(
    "Danh mục màn hình:",
    options=[
        "Tổng quan thảo luận",
        "Thảo luận qua các kênh",
        "Thảo luận tiêu cực",
        "Cập nhật thảo luận mới nhất",
        "Báo cáo AI 48H"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Bộ Lọc Dữ Liệu")

# Date range selection
date_preset = st.sidebar.selectbox(
    "Khoảng thời gian:",
    options=["Toàn thời gian (1 năm)", "48 Giờ Qua (Mới nhất)", "24 Giờ Qua", "7 Ngày Qua", "30 Ngày Qua"],
    index=0
)

lookback_hours = None
if date_preset == "48 Giờ Qua (Mới nhất)":
    lookback_hours = 48
elif date_preset == "24 Giờ Qua":
    lookback_hours = 24
elif date_preset == "7 Ngày Qua":
    lookback_hours = 168
elif date_preset == "30 Ngày Qua":
    lookback_hours = 720

# Channel Filter
channel_filter = st.sidebar.selectbox(
    "Kênh thảo luận:",
    options=["Tất cả", "TikTok", "Facebook Pages", "Facebook Groups", "Facebook Users", "News", "YouTube", "Forum"]
)

# Pillar / Category Filter
pillar_filter = st.sidebar.selectbox(
    "Nhóm chủ đề chính:",
    options=["Tất cả", "Thương hiệu", "Sản phẩm", "Dịch vụ"]
)

# Car Model Filter
model_filter = st.sidebar.selectbox(
    "Thương hiệu / Dòng xe:",
    options=["Tất cả", "Mitsubishi Xforce", "VinFast VF6", "Toyota Yaris Cross", "Skoda Kushaq", "Mitsubishi Pajero Sport", "VinFast VF8", "Mercedes-Benz W212 / E400", "Ford Ranger / Everest"]
)

# Sentiment Filter
sentiment_filter = st.sidebar.selectbox(
    "Sắc thái thảo luận:",
    options=["Tất cả", "Tích cực (POSITIVE)", "Trung lập (NEUTRAL)", "Tiêu cực (NEGATIVE)"]
)

sentiment_arg = None
if "Tích cực" in sentiment_filter:
    sentiment_arg = "POSITIVE"
elif "Trung lập" in sentiment_filter:
    sentiment_arg = "NEUTRAL"
elif "Tiêu cực" in sentiment_filter:
    sentiment_arg = "NEGATIVE"

# -------------------------------------------------------------
# DATA RETRIEVAL (WITH SMART CACHING)
# -------------------------------------------------------------
@st.cache_data(ttl=20)
def fetch_filtered_data(lookback, pillar, model, sentiment, channel):
    return get_discussions_df(
        lookback_hours=lookback,
        pillar=pillar if pillar != "Tất cả" else None,
        car_model=model if model != "Tất cả" else None,
        sentiment=sentiment_arg,
        channel=channel if channel != "Tất cả" else None,
        limit=12000
    )

df = fetch_filtered_data(lookback_hours, pillar_filter, model_filter, sentiment_arg, channel_filter)

# Top Bar (Header & Search)
col_top1, col_top2 = st.columns([3, 2])
with col_top1:
    st.markdown(f'<div class="page-title">{nav_page}</div>', unsafe_allow_html=True)
with col_top2:
    search_col, date_col = st.columns([1, 1])
    with search_col:
        search_kw = st.text_input("Tìm kiếm", placeholder="🔍 Search...", label_visibility="collapsed")
    with date_col:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:6px; padding:6px 12px; font-size:0.8rem; color:#475569; text-align:center; font-weight:600;">
            📅 09-09-2025 - 09-09-2026
        </div>
        """, unsafe_allow_html=True)

# Apply search filter if keyword entered
if search_kw and not df.empty:
    df = df[
        df['content'].astype(str).str.contains(search_kw, case=False, na=False) |
        df['description'].astype(str).str.contains(search_kw, case=False, na=False) |
        df['author'].astype(str).str.contains(search_kw, case=False, na=False)
    ]

total_buzz = len(df)
sent_counts = df['sentiment'].value_counts() if not df.empty else pd.Series()
pos_cnt = sent_counts.get('POSITIVE', 0)
neu_cnt = sent_counts.get('NEUTRAL', 0)
neg_cnt = sent_counts.get('NEGATIVE', 0)


# =============================================================
# SCREEN 1: TỔNG QUAN THẢO LUẬN (Image 1)
# =============================================================
if nav_page == "Tổng quan thảo luận":
    # 1. TOP CHART: Đường xu hướng thảo luận theo ngày (Full Width)
    st.markdown("""
    <div class="dashboard-card">
        <div class="card-title">
            <span>Đường xu hướng thảo luận theo ngày</span>
            <span style="font-size:0.8rem; font-weight:normal; color:#64748B;">Lượt thảo luận / ngày</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not df.empty and 'published_at' in df.columns:
        df_daily = df.copy()
        df_daily['date'] = pd.to_datetime(df_daily['published_at']).dt.date
        daily_vol = df_daily.groupby('date').size().reset_index(name='buzz_count')
        daily_vol = daily_vol.sort_values('date')
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=daily_vol['date'],
            y=daily_vol['buzz_count'],
            marker_color='#38BDF8',
            marker_line_color='#0284C7',
            marker_line_width=1,
            hovertemplate='<b>Ngày:</b> %{x|%d/%m/%Y}<br><b>Số thảo luận:</b> %{y:,} buzz<extra></extra>'
        ))
        fig_trend.update_layout(
            plot_bgcolor='#FFFFFF',
            paper_bgcolor='#FFFFFF',
            margin=dict(t=10, b=30, l=40, r=20),
            height=280,
            xaxis=dict(showgrid=True, gridcolor='#F1F5F9', tickformat='%d/%m'),
            yaxis=dict(showgrid=True, gridcolor='#F1F5F9')
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Đang nạp dữ liệu xu hướng theo ngày...")

    # 2. BOTTOM ROW: Sentiment Overview (Left) + Sắc thái thảo luận theo chủ đề (Right)
    col_b1, col_b2 = st.columns([2, 3])
    
    # Bottom Left: Sentiment Donut Chart
    with col_b1:
        st.markdown("""
        <div class="dashboard-card" style="min-height: 480px;">
            <div class="card-title">Sentiment overview</div>
        </div>
        """, unsafe_allow_html=True)
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Tích cực', 'Trung lập', 'Tiêu cực'],
            values=[pos_cnt, neu_cnt, neg_cnt],
            hole=0.68,
            marker_colors=['#2DD4BF', '#475569', '#EF4444'],
            textinfo='percent',
            hoverinfo='label+value+percent'
        )])
        fig_donut.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            margin=dict(t=20, b=20, l=20, r=20),
            height=360,
            annotations=[dict(text=f'<b>{total_buzz:,}</b><br><span style="font-size:12px; color:#64748B;">Buzz</span>', x=0.5, y=0.5, font_size=22, showarrow=False)]
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # Bottom Right: Sắc thái thảo luận theo chủ đề (Hierarchical 100% Stacked Horizontal Bars)
    with col_b2:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-title">
                <span>Sắc thái thảo luận theo chủ đề</span>
                <span style="font-size:0.8rem; font-weight:normal; color:#64748B;">Tỷ lệ cảm xúc & Tổng buzz</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Build hierarchical topic rows matching Image 1
        records_topic = []
        for pillar, subtopics in HIERARCHICAL_TOPICS.items():
            for st_name in subtopics.keys():
                sub_df = df[df['topic_category'] == st_name]
                cnt = len(sub_df)
                if cnt > 0:
                    s_counts = sub_df['sentiment'].value_counts()
                    p = s_counts.get('POSITIVE', 0)
                    neu = s_counts.get('NEUTRAL', 0)
                    n = s_counts.get('NEGATIVE', 0)
                    records_topic.append({
                        "Pillar": pillar,
                        "Subtopic": f"{pillar} > {st_name}",
                        "Name": st_name,
                        "Count": cnt,
                        "Pos_pct": round(p / cnt * 100, 1),
                        "Neu_pct": round(neu / cnt * 100, 1),
                        "Neg_pct": round(n / cnt * 100, 1)
                    })

        df_topic_chart = pd.DataFrame(records_topic)
        if not df_topic_chart.empty:
            df_topic_chart = df_topic_chart.sort_values('Count', ascending=True)
            
            fig_topics = go.Figure()
            # Positive (Green)
            fig_topics.add_trace(go.Bar(
                y=df_topic_chart['Name'],
                x=df_topic_chart['Pos_pct'],
                name='Tích cực',
                orientation='h',
                marker_color='#2DD4BF',
                hovertemplate='%{y}: %{x}% Tích cực<extra></extra>'
            ))
            # Negative (Red)
            fig_topics.add_trace(go.Bar(
                y=df_topic_chart['Name'],
                x=df_topic_chart['Neg_pct'],
                name='Tiêu cực',
                orientation='h',
                marker_color='#EF4444',
                hovertemplate='%{y}: %{x}% Tiêu cực<extra></extra>'
            ))
            # Neutral (Grey)
            fig_topics.add_trace(go.Bar(
                y=df_topic_chart['Name'],
                x=df_topic_chart['Neu_pct'],
                name='Trung lập',
                orientation='h',
                marker_color='#475569',
                hovertemplate='%{y}: %{x}% Trung lập<extra></extra>'
            ))
            
            fig_topics.update_layout(
                barmode='stack',
                plot_bgcolor='#FFFFFF',
                paper_bgcolor='#FFFFFF',
                height=450,
                margin=dict(t=10, b=20, l=150, r=40),
                xaxis=dict(showgrid=False, range=[0, 100]),
                yaxis=dict(tickfont=dict(size=11))
            )
            st.plotly_chart(fig_topics, use_container_width=True)
        else:
            st.info("Chưa có đủ thảo luận theo chủ đề được phân loại.")


# =============================================================
# SCREEN 2: THẢO LUẬN QUA CÁC KÊNH (Image 2)
# =============================================================
elif nav_page == "Thảo luận qua các kênh":
    col_c1, col_c2 = st.columns([1, 1])
    
    # Top Left: Tỷ lệ thảo luận trên các kênh (Donut)
    with col_c1:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-title">Tỷ lệ thảo luận trên các kênh</div>
        </div>
        """, unsafe_allow_html=True)
        
        channel_counts = df['channel'].value_counts().reset_index()
        channel_counts.columns = ['Channel', 'Count']
        
        fig_ch_donut = go.Figure(data=[go.Pie(
            labels=channel_counts['Channel'],
            values=channel_counts['Count'],
            hole=0.65,
            marker_colors=['#3B82F6', '#06B6D4', '#F59E0B', '#8B5CF6', '#10B981', '#EC4899', '#64748B'],
            textinfo='percent',
            hoverinfo='label+value+percent'
        )])
        fig_ch_donut.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            height=340,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            annotations=[dict(text=f'<b>{total_buzz:,}</b><br><span style="font-size:12px; color:#64748B;">Buzz</span>', x=0.5, y=0.5, font_size=22, showarrow=False)]
        )
        st.plotly_chart(fig_ch_donut, use_container_width=True)

    # Top Right: Xếp hạng nguồn thảo luận
    with col_c2:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-title">Xếp hạng nguồn thảo luận</div>
        </div>
        """, unsafe_allow_html=True)
        
        standard_channels = ["News", "TikTok", "Facebook Pages", "Facebook Users", "Facebook Groups", "YouTube", "Forum", "Social Sites", "E-commerce Sites"]
        rank_data = []
        for ch in standard_channels:
            sub = df[df['channel'] == ch]
            c_cnt = len(sub)
            p = len(sub[sub['sentiment'] == 'POSITIVE'])
            neu = len(sub[sub['sentiment'] == 'NEUTRAL'])
            neg = len(sub[sub['sentiment'] == 'NEGATIVE'])
            rank_data.append({
                "Channel": ch,
                "Buzz": c_cnt,
                "Pos_pct": round(p/c_cnt*100, 1) if c_cnt else 0,
                "Neu_pct": round(neu/c_cnt*100, 1) if c_cnt else 0,
                "Neg_pct": round(neg/c_cnt*100, 1) if c_cnt else 0
            })
            
        df_rank = pd.DataFrame(rank_data).sort_values('Buzz', ascending=False).reset_index(drop=True)
        
        # Display as ranked list matching screenshot
        for idx, row in df_rank.iterrows():
            st.markdown(f"""
            <div style="display:flex; align-items:center; justify-content:space-between; padding:6px 0; border-bottom:1px solid #F1F5F9;">
                <div style="width:180px; font-size:0.85rem; font-weight:600; color:#1E293B;">
                    <span style="color:#94A3B8; margin-right:8px;">{idx+1}.</span> {row['Channel']}
                </div>
                <div style="flex-grow:1; margin:0 15px; background:#E2E8F0; height:10px; border-radius:5px; overflow:hidden; display:flex;">
                    <div style="width:{row['Pos_pct']}%; background:#2DD4BF;"></div>
                    <div style="width:{row['Neg_pct']}%; background:#EF4444;"></div>
                    <div style="width:{row['Neu_pct']}%; background:#475569;"></div>
                </div>
                <div style="width:90px; text-align:right; font-size:0.85rem; font-weight:700; color:#475569;">
                    {row['Buzz']:,} buzz
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Bottom: Top nguồn thảo luận trên kênh trực tuyến
    st.markdown("""
    <div class="dashboard-card">
        <div class="card-title">Top nguồn thảo luận (Fanpages, Groups & Diễn đàn hàng đầu)</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Extract domain / author / group names
    if 'url_comment' in df.columns:
        source_df = df.groupby('channel').size().reset_index(name='count').sort_values('count', ascending=True)
        fig_sources = px.bar(
            source_df,
            x='count',
            y='channel',
            orientation='h',
            labels={'count': 'Số lượng thảo luận', 'channel': 'Kênh / Nguồn'},
            color_discrete_sequence=['#38BDF8']
        )
        fig_sources.update_layout(
            plot_bgcolor='#FFFFFF',
            paper_bgcolor='#FFFFFF',
            height=260,
            margin=dict(t=10, b=20, l=120, r=20)
        )
        st.plotly_chart(fig_sources, use_container_width=True)


# =============================================================
# SCREEN 3: THẢO LUẬN TIÊU CỰC (Image 3)
# =============================================================
elif nav_page == "Thảo luận tiêu cực":
    col_neg1, col_neg2, col_neg3 = st.columns([1, 1.2, 1.8])
    
    neg_df = df[df['sentiment'] == 'NEGATIVE']
    total_neg = len(neg_df)
    
    # Column 1: Sắc thái thảo luận tiêu cực (Donut)
    with col_neg1:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-title">Sắc thái thảo luận</div>
        </div>
        """, unsafe_allow_html=True)
        
        fig_neg_donut = go.Figure(data=[go.Pie(
            labels=['Tiêu cực'],
            values=[total_neg if total_neg > 0 else 1],
            hole=0.68,
            marker_colors=['#EF4444'],
            textinfo='none',
            hoverinfo='label+value'
        )])
        fig_neg_donut.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            height=320,
            showlegend=False,
            annotations=[dict(text=f'<b>{total_neg:,}</b><br><span style="font-size:12px; color:#EF4444;">Buzz Tiêu Cực</span>', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        st.plotly_chart(fig_neg_donut, use_container_width=True)

    # Column 2: Thảo luận tiêu cực trên các kênh
    with col_neg2:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-title">Thảo luận tiêu cực trên các kênh</div>
        </div>
        """, unsafe_allow_html=True)
        
        if not neg_df.empty:
            neg_channels = neg_df['channel'].value_counts().reset_index()
            neg_channels.columns = ['Channel', 'Buzz']
            neg_channels = neg_channels.sort_values('Buzz', ascending=True)
            
            fig_neg_ch = px.bar(
                neg_channels,
                x='Buzz',
                y='Channel',
                orientation='h',
                color_discrete_sequence=['#EF4444']
            )
            fig_neg_ch.update_layout(
                plot_bgcolor='#FFFFFF',
                paper_bgcolor='#FFFFFF',
                height=320,
                margin=dict(t=10, b=20, l=110, r=20),
                xaxis=dict(showgrid=True, gridcolor='#F1F5F9')
            )
            st.plotly_chart(fig_neg_ch, use_container_width=True)
        else:
            st.info("Không có thảo luận tiêu cực nào trong khoảng thời gian này.")

    # Column 3: Cập nhật thảo luận tiêu cực mới nhất
    with col_neg3:
        st.markdown("""
        <div class="dashboard-card">
            <div class="card-title">Cập nhật thảo luận tiêu cực mới nhất</div>
        </div>
        """, unsafe_allow_html=True)
        
        if not neg_df.empty:
            for idx, r in neg_df.head(15).iterrows():
                dt_str = str(r.get('raw_published_date') or r.get('published_at') or 'Gần đây')
                auth = r.get('author') or 'Người dùng ẩn danh'
                chan = r.get('channel') or 'Mạng xã hội'
                content = str(r.get('content') or r.get('description') or '')
                st.markdown(f"""
                <div class="feed-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <span class="feed-author">{auth}</span> &nbsp;<span class="feed-channel">({chan})</span>
                            <div class="feed-date">🕒 {dt_str}</div>
                        </div>
                        <span class="badge-neg">Tiêu cực</span>
                    </div>
                    <div class="feed-content">{content[:180]}...</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("Không có thảo luận tiêu cực.")


# =============================================================
# SCREEN 4: CẬP NHẬT THẢO LUẬN MỚI NHẤT (Image 4)
# =============================================================
elif nav_page == "Cập nhật thảo luận mới nhất":
    st.markdown(f"""
    <div class="dashboard-card">
        <div class="card-title">
            <span>Dòng thời gian thảo luận thời gian thực</span>
            <span style="font-size:0.85rem; font-weight:600; color:#0F766E;">Tổng số: {total_buzz:,} bài viết & bình luận</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not df.empty:
        for idx, r in df.head(30).iterrows():
            topic_tag = r.get('topic_category') or 'Đánh giá sản phẩm'
            auth = r.get('author') or 'Facebook User'
            chan = r.get('channel') or 'Facebook'
            dt_str = str(r.get('raw_published_date') or r.get('published_at') or 'Gần đây')
            content = str(r.get('content') or r.get('description') or '')
            sentiment = str(r.get('sentiment') or 'NEUTRAL').upper()
            
            badge_html = '<span class="badge-neu">Trung lập</span>'
            if sentiment == 'POSITIVE':
                badge_html = '<span class="badge-pos">Tích cực</span>'
            elif sentiment == 'NEGATIVE':
                badge_html = '<span class="badge-neg">Tiêu cực</span>'
                
            st.markdown(f"""
            <div class="feed-card">
                <span class="feed-topic-tag">🏷️ {topic_tag}</span>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span class="feed-author">{auth}</span> &nbsp;<span style="color:#64748B;">trên</span>&nbsp; <span class="feed-channel">{chan}</span>
                        <div class="feed-date">🕒 {dt_str}</div>
                    </div>
                    <div>{badge_html}</div>
                </div>
                <div class="feed-content">{content}</div>
                <div style="margin-top:8px; font-size:0.8rem; color:#94A3B8;">
                    👍 Like &nbsp;&nbsp; 💬 Bình luận &nbsp;&nbsp; 🔗 <a href="{r.get('url_comment', '#')}" target="_blank" style="color:#2563EB; text-decoration:none;">Xem bài viết gốc</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Không có dữ liệu thảo luận phù hợp với bộ lọc hiện tại.")


# =============================================================
# SCREEN 5: BÁO CÁO AI 48H
# =============================================================
elif nav_page == "Báo cáo AI 48H":
    c_ai1, c_ai2 = st.columns([3, 1])
    with c_ai1:
        st.subheader("⚡ Báo Cáo AI Scan 48 Giờ Qua")
        st.caption("Quét toàn bộ luồng thông tin, phát hiện điểm nóng & đề xuất hành động thông minh.")
    with c_ai2:
        if st.button("🚀 Chạy Quét AI 48H Mới", type="primary", use_container_width=True):
            with st.spinner("Đang tổng hợp thông tin và tạo báo cáo AI..."):
                run_48h_scan()
                st.success("Đã hoàn tất bản quét 48h mới nhất!")
                st.rerun()

    latest_summary = get_latest_daily_summary()
    if latest_summary:
        st.markdown(latest_summary.get('full_report_markdown', ''))
        st.divider()
        st.download_button(
            "📥 Tải Báo Cáo Markdown (.md)",
            data=latest_summary.get('full_report_markdown', ''),
            file_name=f"ai_intelligence_48h_{latest_summary.get('report_date')}.md",
            mime="text/markdown"
        )
    else:
        st.warning("Chưa có báo cáo 48h. Bấm '🚀 Chạy Quét AI 48H Mới' để khởi tạo ngay.")
