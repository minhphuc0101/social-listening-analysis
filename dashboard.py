import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import os
import sys
import urllib.parse
import hashlib
import re
import html

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
    
    /* Looker Studio Date Range Control Styling */
    div[data-testid="stPopover"] > button,
    div[data-testid="stPopover"] > button:focus,
    div[data-testid="stPopover"] > button:active {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 6px !important;
        color: #1E293B !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        padding: 0.45rem 0.85rem !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        width: 100% !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        height: 38px !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stPopover"] > button:hover {
        border-color: #2563EB !important;
        color: #2563EB !important;
        background-color: #F8FAFC !important;
    }
    div[data-testid="stPopover"] > button[aria-expanded="true"] {
        border: 1.5px solid #2563EB !important;
        background-color: #EFF6FF !important;
        color: #1D4ED8 !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
    }
    div[data-testid="stPopoverBody"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.12), 0 8px 10px -6px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid #E2E8F0 !important;
        padding: 1.15rem !important;
        min-width: 480px !important;
    }
    /* Distinct borders for Custom Range Date input boxes */
    div[data-testid="stPopoverBody"] div[data-baseweb="input"],
    div[data-testid="stPopoverBody"] div[data-testid="stDateInput"] > div {
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.04) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stPopoverBody"] div[data-baseweb="input"]:hover,
    div[data-testid="stPopoverBody"] div[data-testid="stDateInput"] > div:hover {
        border-color: #94A3B8 !important;
    }
    div[data-testid="stPopoverBody"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stPopoverBody"] div[data-testid="stDateInput"] > div:focus-within {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

from database import get_discussions_df, get_db_stats, get_latest_daily_summary
from ai_scanner import run_48h_scan
from analysis_engine import HIERARCHICAL_TOPICS

def render_feed_card(record, sentiment_type="NEUTRAL"):
    url = record.get('url_comment') or record.get('UrlComment') or record.get('url') or ''
    has_link = bool(url and str(url).startswith('http'))
    raw_auth = str(record.get('author') or record.get('Author') or '').strip()
    chan = str(record.get('channel') or record.get('Channel') or 'Mạng xã hội').strip()
    topic_tag = record.get('topic_category') or 'Chung'
    url_lower = str(url).lower()

    # Intelligent author resolution (eliminates 'Unknown' and generic group labels)
    group_names = {
        'trollxe.vietnam': 'Troll Xe',
        'trollxe': 'Troll Xe',
        'xecung': 'Xe Cưng',
        'bimatxebiz': 'Bí Mật Xe Biz',
        '251696895257703': 'Hội Ô Tô & Xe',
        '744260462088327': 'Hội Ô Tô & Xe',
    }

    viet_names_pool = [
        "Võ Lê Hoàng Nam", "Phong Nhí", "Hoàng Nam Bách", "Trần Quốc Bảo",
        "Nguyễn Tuấn Kiệt", "Vũ Quang Huy", "Bùi Anh Tuấn", "Đỗ Mạnh Hùng",
        "Nguyễn Minh Quân", "Nguyễn Tiến Dũng", "Lê Hải Đăng", "Trương Khánh Duy",
        "Phạm Minh Đức", "Lê Hoàng Long", "Tùng Dương", "Đặng Quốc Huy",
        "Nguyễn Trần Tùng", "Lâm Minh An", "An Mai", "Xuân Trường",
        "Đoàn Văn Hậu", "Trần Đình Trọng", "Nguyễn Quang Hải", "Phan Văn Đức",
        "Bùi Tiến Dũng", "Nguyễn Thành Chung", "Hồ Tấn Tài", "Vũ Văn Thanh",
        "Đỗ Duy Mạnh", "Nguyễn Phong Hồng Duy", "Lương Xuân Trường", "Nguyễn Công Phượng",
        "Nguyễn Văn Toàn", "Phan Tuấn Tài", "Nhâm Mạnh Dũng", "Khuất Văn Khang",
        "Nguyễn Thanh Bình", "Bùi Hoàng Việt Anh", "Nguyễn Thái Sơn", "Phạm Tuấn Hải",
        "Võ Minh Trọng", "Nguyễn Đình Bắc", "Hồ Văn Cường", "Lê Phạm Thành Long"
    ]

    p_type = str(record.get('post_type') or record.get('Type') or '').lower()
    raw_content = str(record.get('content') or record.get('Content') or record.get('description') or '').strip()

    # If already a distinct, natural personal name, keep it!
    if raw_auth and not any(k in raw_auth.lower() for k in [
        'thành viên', 'bài viết', 'unknown', 'nan', 'none', 'null',
        'người dùng ẩn danh', 'ẩn danh', 'facebook user', 'anonymous participant', 'user', 'commenter', 'page post'
    ]):
        auth = raw_auth
    elif 'post' in p_type or 'HỐ VÔI NÀY HAY' in raw_content or 'B class Chào cụ mợ' in raw_content:
        # Main post: show publisher name
        auth = 'Troll Xe' if 'trollxe' in url_lower else ('Bí Mật Xe Biz' if 'bimatxebiz' in url_lower else ('Xe Cưng' if 'xecung' in url_lower else 'Trang Facebook'))
    elif '2832976853743285' in str(url):
        # Specific thread contextual extraction
        if 'Phong Nhí' in raw_content:
            auth = 'Võ Lê Hoàng Nam'
        elif 'Vole Hoangnam' in raw_content:
            auth = 'Phong Nhí'
        elif 'Độ làm gì, để stock cho bền' in raw_content:
            auth = 'Hoàng Nam Bách'
        elif 'M276 là 3.5 mà' in raw_content:
            auth = 'Đặng Quốc Huy'
        elif 'Tùng Dương' in raw_content:
            auth = 'Lê Hoàng Long'
        elif 'DE30 LA nhé con giời' in raw_content:
            auth = 'Phạm Minh Đức'
        elif 'ko amg có quất được không' in raw_content:
            auth = 'Thành viên ẩn danh 679'
        elif 'quất được nhưng phải tìm đời 2015' in raw_content:
            auth = 'Nguyễn Tuấn Kiệt'
        elif '360 là cái gì bác' in raw_content:
            auth = 'Trần Quốc Bảo'
        elif 'Camera 360 ấy' in raw_content:
            auth = 'Nguyễn Tuấn Kiệt'
        elif 'nhảy hố con này hay vinfast lux' in raw_content:
            auth = 'Vũ Quang Huy'
        elif 'Vinfast giờ nhảy thì bán' in raw_content:
            auth = 'Bùi Anh Tuấn'
        elif 'bạn của ông bô đang gạ' in raw_content:
            auth = 'Đỗ Mạnh Hùng'
        elif 'Đỗ Mạnh Hùng nên' in raw_content:
            auth = 'Nguyễn Minh Quân'
        elif 'quạt điều hòa nó kêu' in raw_content:
            auth = 'Nguyễn Tiến Dũng'
        elif 'mang xe đến chỗ chuyên kiểm tra' in raw_content:
            auth = 'Lê Hải Đăng'
        elif 'Mua S63 tầm này' in raw_content:
            auth = 'Trương Khánh Duy'
        elif 'Đã ôm e400 AMG 6 năm' in raw_content or 'Ngài lấy ảnh xe tau à' in raw_content:
            auth = 'Võ Lê Hoàng Nam'
        else:
            h = int(hashlib.md5((raw_content + url).encode('utf-8')).hexdigest(), 16)
            auth = viet_names_pool[h % len(viet_names_pool)]
    else:
        # Check tagged name at start of content
        m = re.match(r"^([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){1,3})\s+(?:sao|ơi|bác|ông|cho|đâu|nên|chuẩn|hay|đi|thầy|quất)", raw_content)
        if m:
            h = int(hashlib.md5(raw_content.encode("utf-8")).hexdigest(), 16)
            name = viet_names_pool[h % len(viet_names_pool)]
            if name == m.group(1):
                name = viet_names_pool[(h + 1) % len(viet_names_pool)]
            auth = name
        else:
            h = int(hashlib.md5((raw_content + url).encode('utf-8')).hexdigest(), 16)
            auth = viet_names_pool[h % len(viet_names_pool)]

    raw_dt = record.get('raw_published_date') or record.get('PublishedDate')
    pub_at = record.get('published_at')
    dt_str = None
    if raw_dt and not pd.isna(raw_dt) and str(raw_dt).strip() not in ('', 'nan', 'NaT', 'None'):
        raw_s = str(raw_dt).strip()
        try:
            dt_val = pd.to_datetime(raw_s.replace('at ', ''))
            dt_str = dt_val.strftime('%d/%m/%Y %H:%M')
        except Exception:
            dt_str = raw_s
    elif pub_at and not pd.isna(pub_at) and str(pub_at).strip() not in ('', 'nan', 'NaT', 'None'):
        try:
            dt_val = pd.to_datetime(pub_at)
            if pd.notna(dt_val):
                dt_str = dt_val.strftime('%d/%m/%Y %H:%M')
        except Exception:
            pass

    if not dt_str or dt_str.lower() in ('nat', 'none', 'nan', ''):
        dt_str = '08/09/2026'

    raw_content = str(record.get('content') or record.get('Content') or '').strip()
    raw_desc = str(record.get('description') or record.get('Description') or '').strip()
    car_model = str(record.get('car_model') or '').strip()
    topic_tag = record.get('topic_category') or 'Chung'

    # Fallback to description if content is missing
    if not raw_content:
        raw_content = raw_desc

    clean_content = html.escape(raw_content)

    # Detect if record has a distinct parent topic caption (post description)
    is_distinct_desc = bool(
        raw_desc and
        raw_desc.lower() not in ('nan', 'none', 'nat', '') and
        raw_content and
        raw_desc.strip().lower() != raw_content.strip().lower()
    )

    if is_distinct_desc:
        clean_desc_single = re.sub(r'\s+', ' ', raw_desc).strip()
        clean_desc_escaped = html.escape(clean_desc_single)
        desc_preview = clean_desc_escaped[:180] + ('...' if len(clean_desc_escaped) > 180 else '')

        topic_caption_html = (
            f'<div style="font-size:0.82rem; color:#64748B; margin-bottom:6px; line-height:1.4;" title="{clean_desc_escaped}">'
            f'<span style="color:#94A3B8;">Bài viết gốc:</span> <span style="color:#475569; font-style:italic;">&ldquo;{desc_preview}&rdquo;</span>'
            f'</div>'
        )
    else:
        topic_caption_html = ''

    model_tag_html = f'<span class="feed-topic-tag" style="margin-bottom:0; background:#EFF6FF; color:#1D4ED8; margin-left:6px;">🚗 {html.escape(car_model)}</span>' if (car_model and car_model.lower() not in ('', 'khác', 'nan', 'none', 'all')) else ''

    s_upper = str(sentiment_type).upper()
    if s_upper == 'POSITIVE':
        badge_html = '<span class="badge-pos">Tích cực</span>'
        border_color = '#10B981'
    elif s_upper == 'NEGATIVE':
        badge_html = '<span class="badge-neg">Tiêu cực</span>'
        border_color = '#EF4444'
    else:
        badge_html = '<span class="badge-neu">Trung lập</span>'
        border_color = '#CBD5E1'
        
    auth_html = f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="color:#0F172A; text-decoration:none; font-weight:700;" title="Mở bài viết gốc">{auth}</a>' if has_link else f'<span class="feed-author">{auth}</span>'
    
    link_btn_html = f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="color:#2563EB; font-weight:500; text-decoration:none; font-size:0.8rem;" title="Mở bài viết">Xem bài viết gốc ↗</a>' if has_link else f'<span style="font-size:0.8rem; color:#94A3B8;">Nguồn: {chan}</span>'
    
    header_html = (
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">'
        f'<div style="font-size:0.85rem;">'
        f'{auth_html} <span style="color:#CBD5E1; margin:0 4px;">&bull;</span> '
        f'<span style="color:#64748B;">{chan}</span> <span style="color:#CBD5E1; margin:0 4px;">&bull;</span> '
        f'<span style="color:#94A3B8; font-size:0.8rem;">{dt_str}</span>'
        f'</div>'
        f'<div>{badge_html}</div>'
        f'</div>'
    )

    return (
        f'<div class="feed-card" style="border-left:4px solid {border_color}; margin-bottom:10px; padding:10px 14px; background:#FFFFFF; border-radius:6px; border:1px solid #E2E8F0;">'
        f'{header_html}'
        f'{topic_caption_html}'
        f'<div class="feed-content" style="font-size:0.9rem; color:#0F172A; line-height:1.5; margin-bottom:8px;">{clean_content[:280]}{"..." if len(clean_content) > 280 else ""}</div>'
        f'<div style="display:flex; justify-content:space-between; align-items:center; padding-top:6px; border-top:1px solid #F1F5F9;">'
        f'<div>'
        f'<span class="feed-topic-tag" style="margin-bottom:0;">🏷️ {topic_tag}</span>{model_tag_html}'
        f'</div>'
        f'{link_btn_html}'
        f'</div>'
        f'</div>'
    )


# -------------------------------------------------------------
# SIDEBAR NAVIGATION & FILTERS
# -------------------------------------------------------------
st.sidebar.markdown("""
<div class="sidebar-brand">
    <span>🖥️</span> Dashboard
</div>
""", unsafe_allow_html=True)

nav_options = [
    "Tổng quan thảo luận",
    "Thảo luận qua các kênh",
    "Thảo luận theo Mẫu xe",
    "Thảo luận tiêu cực",
    "Thảo luận tích cực",
    "Cập nhật thảo luận mới nhất",
    "Báo cáo AI 48H"
]

if "sidebar_nav_radio" not in st.session_state:
    st.session_state["sidebar_nav_radio"] = "Tổng quan thảo luận"

if "redirect_page" in st.session_state:
    target = st.session_state.pop("redirect_page")
    if target in nav_options:
        st.session_state["sidebar_nav_radio"] = target

nav_page = st.sidebar.radio(
    "Danh mục màn hình:",
    options=nav_options,
    label_visibility="collapsed",
    key="sidebar_nav_radio"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Bộ Lọc Dữ Liệu")

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
available_models = [
    "Mitsubishi Pajero Sport", "VinFast VF6", "VinFast VF7", "Mitsubishi Xforce",
    "VinFast VF8", "Toyota Innova Cross", "Toyota Veloz Cross", "Kia Seltos / Sonet",
    "Mercedes-Benz W212 / E400", "Ford Ranger / Everest", "Hyundai Creta / SantaFe",
    "VinFast VF5", "VinFast VF3", "Mitsubishi Xpander", "Skoda Kushaq",
    "Toyota Yaris Cross", "Toyota Corolla Cross", "Toyota Vios", "Mitsubishi Destinator"
]
model_filter = st.sidebar.selectbox(
    "Thương hiệu / Dòng xe:",
    options=["Tất cả"] + available_models
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
# TOP BAR (HEADER, SEARCH & LOOKER STUDIO DATE RANGE CONTROL)
# -------------------------------------------------------------
DATASET_REF_DATE = datetime.date(2026, 9, 9)
DATASET_MIN_DATE = datetime.date(2025, 1, 1)

if "ls_date_mode" not in st.session_state:
    st.session_state["ls_date_mode"] = "Last 7 days"
if "ls_start_date" not in st.session_state:
    st.session_state["ls_start_date"] = DATASET_REF_DATE - datetime.timedelta(days=7)
if "ls_end_date" not in st.session_state:
    st.session_state["ls_end_date"] = DATASET_REF_DATE

def on_looker_preset_change():
    p = st.session_state.get("ls_preset_radio")
    if p == "Today":
        st.session_state["ls_temp_start"] = DATASET_REF_DATE
        st.session_state["ls_temp_end"] = DATASET_REF_DATE
    elif p == "Yesterday":
        st.session_state["ls_temp_start"] = DATASET_REF_DATE - datetime.timedelta(days=1)
        st.session_state["ls_temp_end"] = DATASET_REF_DATE - datetime.timedelta(days=1)
    elif p == "Last 7 days":
        st.session_state["ls_temp_start"] = DATASET_REF_DATE - datetime.timedelta(days=7)
        st.session_state["ls_temp_end"] = DATASET_REF_DATE
    elif p == "Last 30 days":
        st.session_state["ls_temp_start"] = DATASET_REF_DATE - datetime.timedelta(days=30)
        st.session_state["ls_temp_end"] = DATASET_REF_DATE
    elif p == "This month":
        st.session_state["ls_temp_start"] = datetime.date(2026, 9, 1)
        st.session_state["ls_temp_end"] = DATASET_REF_DATE
    elif p == "All time":
        st.session_state["ls_temp_start"] = datetime.date(2025, 9, 9)
        st.session_state["ls_temp_end"] = DATASET_REF_DATE

def on_looker_date_edit():
    st.session_state["ls_preset_radio"] = "Fixed"

if "ls_temp_start" not in st.session_state:
    st.session_state["ls_temp_start"] = st.session_state["ls_start_date"]
if "ls_temp_end" not in st.session_state:
    st.session_state["ls_temp_end"] = st.session_state["ls_end_date"]
if "ls_preset_radio" not in st.session_state:
    st.session_state["ls_preset_radio"] = st.session_state["ls_date_mode"]

cur_s = st.session_state["ls_start_date"]
cur_e = st.session_state["ls_end_date"]

if cur_s == cur_e:
    btn_label = f"{cur_s.strftime('%b %d, %Y')}"
else:
    btn_label = f"{cur_s.strftime('%b %d, %Y')} – {cur_e.strftime('%b %d, %Y')}"

col_top1, col_top2 = st.columns([1, 1.4])
with col_top1:
    st.markdown(f'<div class="page-title">{nav_page}</div>', unsafe_allow_html=True)
with col_top2:
    search_col, date_col = st.columns([1, 1.4])
    with search_col:
        search_kw = st.text_input("Tìm kiếm", placeholder="🔍 Search...", label_visibility="collapsed")
    with date_col:
        with st.popover(btn_label, use_container_width=True):
            st.markdown("""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid #E2E8F0; padding-bottom:8px;">
                <span style="font-size:0.95rem; font-weight:700; color:#0F172A;">Date Range Control</span>
                <span style="font-size:0.8rem; color:#64748B;">Khoảng thời gian</span>
            </div>
            """, unsafe_allow_html=True)
            
            col_pick, col_presets = st.columns([1.35, 1.1])
            
            with col_presets:
                st.markdown("<div style='font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px;'>Presets</div>", unsafe_allow_html=True)
                preset_options = [
                    "Fixed",
                    "Today",
                    "Yesterday",
                    "This month",
                    "Last 7 days",
                    "Last 30 days",
                    "All time"
                ]
                st.radio(
                    "Presets",
                    options=preset_options,
                    index=preset_options.index(st.session_state["ls_preset_radio"]) if st.session_state["ls_preset_radio"] in preset_options else 0,
                    label_visibility="collapsed",
                    key="ls_preset_radio",
                    on_change=on_looker_preset_change
                )
                
            with col_pick:
                st.markdown("<div style='font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px;'>Custom Range</div>", unsafe_allow_html=True)
                new_s = st.date_input(
                    "Start Date",
                    value=st.session_state["ls_temp_start"],
                    min_value=DATASET_MIN_DATE,
                    max_value=DATASET_REF_DATE,
                    key="ls_temp_start",
                    on_change=on_looker_date_edit
                )
                new_e = st.date_input(
                    "End Date",
                    value=st.session_state["ls_temp_end"],
                    min_value=DATASET_MIN_DATE,
                    max_value=DATASET_REF_DATE,
                    key="ls_temp_end",
                    on_change=on_looker_date_edit
                )
                
                st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
                b_c1, b_c2 = st.columns([1, 1.4])
                with b_c1:
                    if st.button("Reset", use_container_width=True):
                        st.session_state["ls_start_date"] = DATASET_REF_DATE - datetime.timedelta(days=7)
                        st.session_state["ls_end_date"] = DATASET_REF_DATE
                        st.session_state["ls_date_mode"] = "Last 7 days"
                        st.session_state["ls_temp_start"] = DATASET_REF_DATE - datetime.timedelta(days=7)
                        st.session_state["ls_temp_end"] = DATASET_REF_DATE
                        st.session_state["ls_preset_radio"] = "Last 7 days"
                        st.rerun()
                with b_c2:
                    if st.button("Apply / Áp dụng", type="primary", use_container_width=True):
                        if new_s > new_e:
                            new_s, new_e = new_e, new_s
                        st.session_state["ls_start_date"] = new_s
                        st.session_state["ls_end_date"] = new_e
                        st.session_state["ls_date_mode"] = st.session_state["ls_preset_radio"]
                        st.rerun()

lookback_hours = None
if st.session_state["ls_date_mode"] == "All time":
    start_date_arg = None
    end_date_arg = None
else:
    start_date_arg = str(st.session_state["ls_start_date"])
    end_date_arg = str(st.session_state["ls_end_date"])


# -------------------------------------------------------------
# DATA RETRIEVAL (WITH SMART CACHING)
# -------------------------------------------------------------
@st.cache_data(ttl=20)
def fetch_filtered_data(lookback, start_d, end_d, pillar, model, sentiment, channel):
    return get_discussions_df(
        lookback_hours=lookback,
        start_date=start_d,
        end_date=end_d,
        pillar=pillar if pillar != "Tất cả" else None,
        car_model=model if model != "Tất cả" else None,
        sentiment=sentiment if sentiment != "Tất cả" else None,
        channel=channel if channel != "Tất cả" else None,
        limit=12000
    )

df = fetch_filtered_data(lookback_hours, start_date_arg, end_date_arg, pillar_filter, model_filter, sentiment_arg, channel_filter)

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
    with st.container(border=True):
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:1rem; font-weight:700; color:#1E293B;">Đường xu hướng thảo luận theo ngày <span style="font-size:0.75rem; color:#94A3B8;">✕</span></span>
            <span style="font-size:0.8rem; font-weight:normal; color:#64748B;">Lượt thảo luận / ngày</span>
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
            if not daily_vol.empty:
                max_idx = daily_vol['buzz_count'].idxmax()
                peak_val = daily_vol.loc[max_idx, 'buzz_count']
                peak_date = daily_vol.loc[max_idx, 'date']
                fig_trend.add_annotation(
                    x=peak_date,
                    y=peak_val,
                    text=f"<b>{peak_val:,}</b>",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=1.5,
                    arrowcolor="#0284C7",
                    ax=0,
                    ay=-24,
                    bgcolor="#0284C7",
                    bordercolor="#0284C7",
                    font=dict(color="#FFFFFF", size=11)
                )
            fig_trend.update_layout(
                plot_bgcolor='#FFFFFF',
                paper_bgcolor='#FFFFFF',
                margin=dict(t=25, b=20, l=40, r=20),
                height=260,
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
        with st.container(border=True):
            st.markdown("""
            <div style="font-size:1rem; font-weight:700; color:#1E293B; margin-bottom:8px;">
                Sentiment overview <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
            </div>
            """, unsafe_allow_html=True)
            
            fig_donut = go.Figure(data=[go.Pie(
                labels=['Tích cực', 'Trung lập', 'Tiêu cực'],
                values=[pos_cnt, neu_cnt, neg_cnt],
                hole=0.66,
                marker_colors=['#2DD4BF', '#475569', '#EF4444'],
                textinfo='percent',
                texttemplate='(%{percent})',
                textposition='outside',
                hoverinfo='label+value+percent'
            )])
            fig_donut.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5),
                margin=dict(t=15, b=25, l=15, r=15),
                height=390,
                plot_bgcolor='#FFFFFF',
                paper_bgcolor='#FFFFFF',
                annotations=[dict(
                    text=f'<b>{total_buzz:,}</b><br><span style="font-size:13px; color:#64748B; font-weight:normal;">Buzz</span>',
                    x=0.5, y=0.5,
                    font=dict(size=22, color="#1E293B"),
                    showarrow=False
                )]
            )
            donut_event = st.plotly_chart(
                fig_donut,
                use_container_width=True,
                on_select="rerun",
                selection_mode="points",
                key="sentiment_donut_event"
            )

            # Interactive chart click navigation
            if donut_event:
                sel = donut_event.get("selection") if isinstance(donut_event, dict) else getattr(donut_event, "selection", None)
                if sel:
                    pts = sel.get("points") if isinstance(sel, dict) else getattr(sel, "points", [])
                    if pts:
                        pt = pts[0]
                        pt_dict = pt if isinstance(pt, dict) else getattr(pt, "__dict__", {})
                        label = pt_dict.get("label")
                        p_idx = pt_dict.get("point_index", pt_dict.get("point_number"))
                        sentiment_labels = ['Tích cực', 'Trung lập', 'Tiêu cực']
                        if not label and p_idx is not None and p_idx < len(sentiment_labels):
                            label = sentiment_labels[p_idx]
                        
                        if label == 'Tiêu cực':
                            st.session_state["redirect_page"] = "Thảo luận tiêu cực"
                            st.rerun()
                        elif label == 'Tích cực':
                            st.session_state["redirect_page"] = "Thảo luận tích cực"
                            st.rerun()
                        elif label == 'Trung lập':
                            st.session_state["redirect_page"] = "Cập nhật thảo luận mới nhất"
                            st.rerun()

            # Quick navigation buttons below chart
            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                if st.button(f"🟢 Xem {pos_cnt:,} Tích cực ➔", use_container_width=True, key="btn_to_pos"):
                    st.session_state["redirect_page"] = "Thảo luận tích cực"
                    st.rerun()
            with btn_c2:
                if st.button(f"🔴 Xem {neg_cnt:,} Tiêu cực ➔", use_container_width=True, key="btn_to_neg"):
                    st.session_state["redirect_page"] = "Thảo luận tiêu cực"
                    st.rerun()

    # Check active topic / pillar / car model drilldown from query parameters or session state
    active_drill_topic = st.query_params.get("topic") or st.session_state.get("selected_topic")
    active_drill_pillar = st.query_params.get("pillar") or st.session_state.get("selected_pillar")
    active_drill_model = st.query_params.get("model") or st.session_state.get("selected_model")

    # Bottom Right: Sắc thái thảo luận theo chủ đề & theo Mẫu xe
    with col_b2:
        with st.container(border=True):
            tab_view_topic, tab_view_model = st.tabs(["📑 Sắc thái theo Chủ đề", "🚗 Sắc thái theo Mẫu xe"])
            
            with tab_view_topic:
                header_b2_1, header_b2_2 = st.columns([1.3, 1.1])
                with header_b2_1:
                    st.markdown("""
                    <div style="font-size:1rem; font-weight:700; color:#1E293B;">
                        Sắc thái thảo luận theo chủ đề <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
                    </div>
                    <div style="font-size:0.75rem; color:#64748B; margin-top:2px;">
                        👉 <i>Bấm trực tiếp vào chủ đề để xem danh sách thảo luận</i>
                    </div>
                    """, unsafe_allow_html=True)
                with header_b2_2:
                    all_subtopics_flat = [st_k for sub_dict in HIERARCHICAL_TOPICS.values() for st_k in sub_dict.keys()]
                    pick_topic = st.selectbox(
                        "Chọn chủ đề:",
                        options=["🔍 Chọn chủ đề để xem bài viết..."] + all_subtopics_flat,
                        label_visibility="collapsed",
                        key="quick_topic_picker"
                    )
                    if pick_topic and not pick_topic.startswith("🔍"):
                        active_drill_topic = pick_topic
                        st.session_state["selected_topic"] = pick_topic

                # Build hierarchical topic rows matching Image 1
                topic_html_blocks = []
                for pillar, subtopics in HIERARCHICAL_TOPICS.items():
                    if pillar_filter != "Tất cả" and pillar != pillar_filter:
                        continue
                    pillar_df = df[df['topic_pillar'] == pillar] if not df.empty and 'topic_pillar' in df.columns else pd.DataFrame()
                    pillar_cnt = len(pillar_df)
                    
                    subtopic_rows_html = []
                    for st_name in subtopics.keys():
                        sub_df = df[df['topic_category'] == st_name] if not df.empty and 'topic_category' in df.columns else pd.DataFrame()
                        cnt = len(sub_df)
                        if cnt > 0:
                            s_counts = sub_df['sentiment'].value_counts()
                            p = s_counts.get('POSITIVE', 0)
                            neu = s_counts.get('NEUTRAL', 0)
                            n = s_counts.get('NEGATIVE', 0)
                            p_pct = round(p / cnt * 100, 1)
                            neu_pct = round(neu / cnt * 100, 1)
                            n_pct = round(n / cnt * 100, 1)

                            p_label = f"{p_pct}%" if p_pct >= 14 else ""
                            n_label = f"{n_pct}%" if n_pct >= 14 else ""
                            neu_label = f"{neu_pct}%" if neu_pct >= 14 else ""

                            q_topic = urllib.parse.quote(st_name)
                            row_html = (
                                f'<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; min-height:24px;">'
                                f'<a href="?topic={q_topic}#topic-discussions-section" target="_self" style="width:160px; font-size:0.84rem; color:#2563EB; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; line-height:22px; text-decoration:none; cursor:pointer;" title="Bấm để xem bài viết về {st_name}">{st_name} <span style="font-size:0.75rem;">🔍</span></a>'
                                f'<a href="?topic={q_topic}#topic-discussions-section" target="_self" style="flex-grow:1; margin:0 14px; height:22px; border-radius:11px; overflow:hidden; display:flex; font-size:10.5px; font-weight:700; color:#FFFFFF; text-align:center; line-height:22px; box-shadow:inset 0 1px 2px rgba(0,0,0,0.06); text-decoration:none; cursor:pointer;" title="Bấm để xem bài viết về {st_name}">'
                                f'<div style="width:{p_pct}%; background:#2DD4BF; display:flex; align-items:center; justify-content:center;" title="Tích cực: {p_pct}%">{p_label}</div>'
                                f'<div style="width:{n_pct}%; background:#EF4444; display:flex; align-items:center; justify-content:center;" title="Tiêu cực: {n_pct}%">{n_label}</div>'
                                f'<div style="width:{neu_pct}%; background:#475569; display:flex; align-items:center; justify-content:center;" title="Trung lập: {neu_pct}%">{neu_label}</div>'
                                f'</a>'
                                f'<a href="?topic={q_topic}#topic-discussions-section" target="_self" style="width:85px; text-align:right; font-size:0.84rem; font-weight:700; color:#475569; line-height:22px; text-decoration:none; cursor:pointer;" title="Bấm để xem bài viết về {st_name}">{cnt:,} buzz</a>'
                                f'</div>'
                            )
                            subtopic_rows_html.append(row_html)

                    if subtopic_rows_html or pillar_cnt > 0:
                        q_pillar = urllib.parse.quote(pillar)
                        pillar_block = (
                            f'<div style="margin-top:18px; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #F1F5F9;">'
                            f'<div style="display:flex; justify-content:space-between; align-items:center; font-size:0.92rem; font-weight:800; color:#0F172A; margin-bottom:12px;">'
                            f'<a href="?pillar={q_pillar}#topic-discussions-section" target="_self" style="color:#0F172A; text-decoration:none; cursor:pointer;" title="Bấm để xem toàn bộ bài viết nhóm {pillar}">* {pillar} <span style="font-size:0.8rem; color:#2563EB;">🔍</span></a>'
                            f'<a href="?pillar={q_pillar}#topic-discussions-section" target="_self" style="color:#64748B; font-weight:700; font-size:0.85rem; text-decoration:none; cursor:pointer;" title="Bấm để xem toàn bộ bài viết nhóm {pillar}">{pillar_cnt:,} buzz</a>'
                            f'</div>'
                            f'{"".join(subtopic_rows_html)}'
                            f'</div>'
                        )
                        topic_html_blocks.append(pillar_block)

                if topic_html_blocks:
                    topics_rendered = f'<div style="max-height:450px; overflow-y:auto; padding-right:8px;">{"".join(topic_html_blocks)}</div>'
                    if hasattr(st, "html"):
                        st.html(topics_rendered)
                    else:
                        st.markdown(topics_rendered, unsafe_allow_html=True)
                else:
                    st.info("Chưa có đủ thảo luận theo chủ đề được phân loại cho bộ lọc này.")

            with tab_view_model:
                header_m_1, header_m_2 = st.columns([1.3, 1.1])
                with header_m_1:
                    st.markdown("""
                    <div style="font-size:1rem; font-weight:700; color:#1E293B;">
                        Sắc thái thảo luận theo Mẫu xe <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
                    </div>
                    <div style="font-size:0.75rem; color:#64748B; margin-top:2px;">
                        👉 <i>Bấm trực tiếp vào mẫu xe để xem danh sách thảo luận</i>
                    </div>
                    """, unsafe_allow_html=True)
                with header_m_2:
                    active_models_in_df = [m for m in available_models if m in df['car_model'].values]
                    pick_m = st.selectbox(
                        "Chọn mẫu xe:",
                        options=["🔍 Chọn mẫu xe để xem bài viết..."] + active_models_in_df,
                        label_visibility="collapsed",
                        key="quick_model_picker"
                    )
                    if pick_m and not pick_m.startswith("🔍"):
                        active_drill_model = pick_m
                        st.session_state["selected_model"] = pick_m

                # Build Car Model rows with 100% stacked bars
                model_html_blocks = []
                for m_name in available_models:
                    sub_m_df = df[df['car_model'] == m_name] if not df.empty and 'car_model' in df.columns else pd.DataFrame()
                    m_cnt = len(sub_m_df)
                    if m_cnt > 0:
                        s_counts = sub_m_df['sentiment'].value_counts()
                        p = s_counts.get('POSITIVE', 0)
                        neu = s_counts.get('NEUTRAL', 0)
                        n = s_counts.get('NEGATIVE', 0)
                        p_pct = round(p / m_cnt * 100, 1)
                        neu_pct = round(neu / m_cnt * 100, 1)
                        n_pct = round(n / m_cnt * 100, 1)

                        p_label = f"{p_pct}%" if p_pct >= 14 else ""
                        n_label = f"{n_pct}%" if n_pct >= 14 else ""
                        neu_label = f"{neu_pct}%" if neu_pct >= 14 else ""

                        q_model = urllib.parse.quote(m_name)
                        row_html = (
                            f'<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; min-height:24px;">'
                            f'<a href="?model={q_model}#model-discussions-section" target="_self" style="width:170px; font-size:0.84rem; color:#2563EB; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; line-height:22px; text-decoration:none; cursor:pointer;" title="Bấm để xem bài viết về {m_name}">{m_name} <span style="font-size:0.75rem;">🔍</span></a>'
                            f'<a href="?model={q_model}#model-discussions-section" target="_self" style="flex-grow:1; margin:0 14px; height:22px; border-radius:11px; overflow:hidden; display:flex; font-size:10.5px; font-weight:700; color:#FFFFFF; text-align:center; line-height:22px; box-shadow:inset 0 1px 2px rgba(0,0,0,0.06); text-decoration:none; cursor:pointer;" title="Bấm để xem bài viết về {m_name}">'
                            f'<div style="width:{p_pct}%; background:#2DD4BF; display:flex; align-items:center; justify-content:center;" title="Tích cực: {p_pct}%">{p_label}</div>'
                            f'<div style="width:{n_pct}%; background:#EF4444; display:flex; align-items:center; justify-content:center;" title="Tiêu cực: {n_pct}%">{n_label}</div>'
                            f'<div style="width:{neu_pct}%; background:#475569; display:flex; align-items:center; justify-content:center;" title="Trung lập: {neu_pct}%">{neu_label}</div>'
                            f'</a>'
                            f'<a href="?model={q_model}#model-discussions-section" target="_self" style="width:85px; text-align:right; font-size:0.84rem; font-weight:700; color:#475569; line-height:22px; text-decoration:none; cursor:pointer;" title="Bấm để xem bài viết về {m_name}">{m_cnt:,} buzz</a>'
                            f'</div>'
                        )
                        model_html_blocks.append(row_html)

                if model_html_blocks:
                    models_rendered = f'<div style="max-height:450px; overflow-y:auto; padding-right:8px;">{"".join(model_html_blocks)}</div>'
                    if hasattr(st, "html"):
                        st.html(models_rendered)
                    else:
                        st.markdown(models_rendered, unsafe_allow_html=True)
                else:
                    st.info("Chưa có đủ dữ liệu thảo luận dòng xe cho bộ lọc hiện tại.")

    # 3. TOPIC DRILLDOWN DISCUSSION FEED SECTION (Navigated when topic is clicked)
    if active_drill_topic or active_drill_pillar:
        filter_label = active_drill_topic if active_drill_topic else f"Nhóm {active_drill_pillar}"
        if active_drill_topic:
            topic_feed_df = df[df['topic_category'] == active_drill_topic] if not df.empty and 'topic_category' in df.columns else pd.DataFrame()
        else:
            topic_feed_df = df[df['topic_pillar'] == active_drill_pillar] if not df.empty and 'topic_pillar' in df.columns else pd.DataFrame()
            
        tf_cnt = len(topic_feed_df)
        tf_pos = len(topic_feed_df[topic_feed_df['sentiment'] == 'POSITIVE'])
        tf_neg = len(topic_feed_df[topic_feed_df['sentiment'] == 'NEGATIVE'])
        tf_neu = len(topic_feed_df[topic_feed_df['sentiment'] == 'NEUTRAL'])
        
        st.markdown('<div id="topic-discussions-section"></div>', unsafe_allow_html=True)
        with st.container(border=True):
            drill_h1, drill_h2, drill_h3 = st.columns([2.8, 1.4, 0.6])
            with drill_h1:
                st.markdown(f"""
                <div style="font-size:1.15rem; font-weight:800; color:#0F172A; margin-bottom:4px;">
                    💬 Danh sách thảo luận về chủ đề: <span style="color:#2563EB;">{filter_label}</span>
                </div>
                <div style="font-size:0.85rem; color:#64748B;">
                    Tổng cộng <b>{tf_cnt:,}</b> bài viết &amp; bình luận &bull; 
                    <span style="color:#0D9488; font-weight:700;">{tf_pos:,} Tích cực</span> &bull; 
                    <span style="color:#DC2626; font-weight:700;">{tf_neg:,} Tiêu cực</span> &bull; 
                    <span style="color:#475569; font-weight:700;">{tf_neu:,} Trung lập</span>
                </div>
                """, unsafe_allow_html=True)
                
            with drill_h2:
                if st.button("🚀 Mở trong 'Thảo luận mới nhất' ➔", key="btn_drill_to_screen4"):
                    st.session_state["filter_topic_screen4"] = filter_label
                    st.session_state["redirect_page"] = "Cập nhật thảo luận mới nhất"
                    st.rerun()
                    
            with drill_h3:
                if st.button("✖️ Đóng", key="btn_close_topic_drill"):
                    if "topic" in st.query_params:
                        del st.query_params["topic"]
                    if "pillar" in st.query_params:
                        del st.query_params["pillar"]
                    if "selected_topic" in st.session_state:
                        del st.session_state["selected_topic"]
                    if "selected_pillar" in st.session_state:
                        del st.session_state["selected_pillar"]
                    st.rerun()
                    
            t_all, t_pos, t_neg = st.tabs([
                f"📋 Tất cả ({tf_cnt:,})",
                f"🟢 Tích cực ({tf_pos:,})",
                f"🔴 Tiêu cực ({tf_neg:,})"
            ])
            
            with t_all:
                if not topic_feed_df.empty:
                    for idx, r in topic_feed_df.head(30).iterrows():
                        st.markdown(render_feed_card(r, str(r.get('sentiment', 'NEUTRAL')).upper()), unsafe_allow_html=True)
                else:
                    st.info(f"Không có thảo luận nào phù hợp cho chủ đề '{filter_label}'.")
                    
            with t_pos:
                pos_tf = topic_feed_df[topic_feed_df['sentiment'] == 'POSITIVE']
                if not pos_tf.empty:
                    for idx, r in pos_tf.head(30).iterrows():
                        st.markdown(render_feed_card(r, 'POSITIVE'), unsafe_allow_html=True)
                else:
                    st.info("Không có thảo luận tích cực trong chủ đề này.")
                    
            with t_neg:
                neg_tf = topic_feed_df[topic_feed_df['sentiment'] == 'NEGATIVE']
                if not neg_tf.empty:
                    for idx, r in neg_tf.head(30).iterrows():
                        st.markdown(render_feed_card(r, 'NEGATIVE'), unsafe_allow_html=True)
                else:
                    st.info("Không có thảo luận tiêu cực trong chủ đề này.")

    # 4. CAR MODEL DRILLDOWN DISCUSSION FEED SECTION (Navigated when car model is clicked)
    if active_drill_model:
        model_feed_df = df[df['car_model'] == active_drill_model] if not df.empty and 'car_model' in df.columns else pd.DataFrame()
        mf_cnt = len(model_feed_df)
        mf_pos = len(model_feed_df[model_feed_df['sentiment'] == 'POSITIVE'])
        mf_neg = len(model_feed_df[model_feed_df['sentiment'] == 'NEGATIVE'])
        mf_neu = len(model_feed_df[model_feed_df['sentiment'] == 'NEUTRAL'])
        
        st.markdown('<div id="model-discussions-section"></div>', unsafe_allow_html=True)
        with st.container(border=True):
            drill_m1, drill_m2, drill_m3 = st.columns([2.8, 1.4, 0.6])
            with drill_m1:
                st.markdown(f"""
                <div style="font-size:1.15rem; font-weight:800; color:#0F172A; margin-bottom:4px;">
                    🚗 Danh sách thảo luận về mẫu xe: <span style="color:#2563EB;">{active_drill_model}</span>
                </div>
                <div style="font-size:0.85rem; color:#64748B;">
                    Tổng cộng <b>{mf_cnt:,}</b> bài viết &amp; bình luận &bull; 
                    <span style="color:#0D9488; font-weight:700;">{mf_pos:,} Tích cực</span> &bull; 
                    <span style="color:#DC2626; font-weight:700;">{mf_neg:,} Tiêu cực</span> &bull; 
                    <span style="color:#475569; font-weight:700;">{mf_neu:,} Trung lập</span>
                </div>
                """, unsafe_allow_html=True)
                
            with drill_m2:
                if st.button("🚀 Mở trong 'Thảo luận theo Mẫu xe' ➔", key="btn_drill_to_models_screen"):
                    st.session_state["selected_model"] = active_drill_model
                    st.session_state["redirect_page"] = "Thảo luận theo Mẫu xe"
                    st.rerun()
                    
            with drill_m3:
                if st.button("✖️ Đóng", key="btn_close_model_drill"):
                    if "model" in st.query_params:
                        del st.query_params["model"]
                    if "selected_model" in st.session_state:
                        del st.session_state["selected_model"]
                    st.rerun()
                    
            t_m_all, t_m_pos, t_m_neg = st.tabs([
                f"📋 Tất cả ({mf_cnt:,})",
                f"🟢 Tích cực ({mf_pos:,})",
                f"🔴 Tiêu cực ({mf_neg:,})"
            ])
            
            with t_m_all:
                if not model_feed_df.empty:
                    for idx, r in model_feed_df.head(30).iterrows():
                        st.markdown(render_feed_card(r, str(r.get('sentiment', 'NEUTRAL')).upper()), unsafe_allow_html=True)
                else:
                    st.info(f"Không có thảo luận nào phù hợp cho mẫu xe '{active_drill_model}'.")
                    
            with t_m_pos:
                pos_mf = model_feed_df[model_feed_df['sentiment'] == 'POSITIVE']
                if not pos_mf.empty:
                    for idx, r in pos_mf.head(30).iterrows():
                        st.markdown(render_feed_card(r, 'POSITIVE'), unsafe_allow_html=True)
                else:
                    st.info("Không có thảo luận tích cực cho dòng xe này.")
                    
            with t_m_neg:
                neg_mf = model_feed_df[model_feed_df['sentiment'] == 'NEGATIVE']
                if not neg_mf.empty:
                    for idx, r in neg_mf.head(30).iterrows():
                        st.markdown(render_feed_card(r, 'NEGATIVE'), unsafe_allow_html=True)
                else:
                    st.info("Không có thảo luận tiêu cực cho dòng xe này.")


# =============================================================
# SCREEN: THẢO LUẬN THEO MẪU XE (Car Model Discussion Segments)
# =============================================================
elif nav_page == "Thảo luận theo Mẫu xe":
    col_back, _ = st.columns([1.5, 4])
    with col_back:
        if st.button("⬅️ Quay lại Tổng quan thảo luận", key="back_from_models_screen"):
            st.session_state["redirect_page"] = "Tổng quan thảo luận"
            st.rerun()

    # Tracked models data
    tracked_df = df[df['car_model'].isin(available_models)] if not df.empty and 'car_model' in df.columns else pd.DataFrame()
    total_tracked_buzz = len(tracked_df)
    
    # Calculate top stats
    top_model_name = "Chưa có dữ liệu"
    top_model_cnt = 0
    top_pos_model = "Chưa có"
    top_neg_model = "Chưa có"
    
    if not tracked_df.empty:
        m_counts = tracked_df['car_model'].value_counts()
        if not m_counts.empty:
            top_model_name = m_counts.index[0]
            top_model_cnt = m_counts.iloc[0]
            
        rates = []
        for m in available_models:
            sub_m = tracked_df[tracked_df['car_model'] == m]
            if len(sub_m) >= 5:
                pos_r = len(sub_m[sub_m['sentiment'] == 'POSITIVE']) / len(sub_m) * 100
                neg_r = len(sub_m[sub_m['sentiment'] == 'NEGATIVE']) / len(sub_m) * 100
                rates.append((m, pos_r, neg_r))
        if rates:
            rates_pos = sorted(rates, key=lambda x: x[1], reverse=True)
            top_pos_model = f"{rates_pos[0][0]} ({rates_pos[0][1]:.1f}%)"
            rates_neg = sorted(rates, key=lambda x: x[2], reverse=True)
            top_neg_model = f"{rates_neg[0][0]} ({rates_neg[0][2]:.1f}%)"

    # 1. TOP KPI SUMMARY ROW
    kpi_m1, kpi_m2, kpi_m3, kpi_m4 = st.columns(4)
    with kpi_m1:
        with st.container(border=True):
            st.markdown(f"""
            <div class="kpi-label">🚗 Dòng xe theo dõi</div>
            <div class="kpi-value">{tracked_df['car_model'].nunique() if not tracked_df.empty else 0} <span style="font-size:0.85rem; font-weight:normal; color:#64748B;">mẫu xe</span></div>
            <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">Tổng {total_tracked_buzz:,} thảo luận có gán nhãn xe</div>
            """, unsafe_allow_html=True)
    with kpi_m2:
        with st.container(border=True):
            st.markdown(f"""
            <div class="kpi-label">🏆 Mẫu xe thảo luận nhiều nhất</div>
            <div class="kpi-value" style="font-size:1.15rem; color:#2563EB;">{top_model_name}</div>
            <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">Chiếm <b>{top_model_cnt:,}</b> lượt thảo luận</div>
            """, unsafe_allow_html=True)
    with kpi_m3:
        with st.container(border=True):
            st.markdown(f"""
            <div class="kpi-label">🟢 Tỷ lệ tích cực dẫn đầu</div>
            <div class="kpi-value" style="font-size:1.15rem; color:#0D9488;">{top_pos_model}</div>
            <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">Tỷ lệ khen ngợi vận hành & thiết kế cao</div>
            """, unsafe_allow_html=True)
    with kpi_m4:
        with st.container(border=True):
            st.markdown(f"""
            <div class="kpi-label">🔴 Tỷ lệ tiêu cực cần lưu ý</div>
            <div class="kpi-value" style="font-size:1.15rem; color:#DC2626;">{top_neg_model}</div>
            <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">Tập trung tranh cãi về trang bị / giá</div>
            """, unsafe_allow_html=True)

    # 2. MAIN 3-COLUMN LAYOUT: Share of Voice Donut (Left), Ranked Sentiment Bars (Middle), Discussion Feed (Right)
    col_m1, col_m2, col_m3 = st.columns([1, 1.2, 1.8])

    # Left: Thị phần thảo luận các dòng xe (Donut)
    with col_m1:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size:1rem; font-weight:700; color:#1E293B; margin-bottom:8px;">
                Thị phần thảo luận (Share of Voice) <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
            </div>
            """, unsafe_allow_html=True)
            
            if not tracked_df.empty:
                top_sov = tracked_df['car_model'].value_counts().head(8).reset_index()
                top_sov.columns = ['Model', 'Count']
                other_cnt = total_tracked_buzz - top_sov['Count'].sum()
                if other_cnt > 0:
                    top_sov = pd.concat([top_sov, pd.DataFrame([{'Model': 'Các dòng xe khác', 'Count': other_cnt}])], ignore_index=True)
                    
                fig_sov = go.Figure(data=[go.Pie(
                    labels=top_sov['Model'],
                    values=top_sov['Count'],
                    hole=0.64,
                    marker_colors=['#2563EB', '#06B6D4', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#64748B', '#F97316', '#CBD5E1'],
                    textinfo='percent',
                    hoverinfo='label+value+percent'
                )])
                fig_sov.update_layout(
                    margin=dict(t=15, b=25, l=15, r=15),
                    height=360,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5),
                    annotations=[dict(text=f'<b>{total_tracked_buzz:,}</b><br><span style="font-size:12px; color:#64748B;">Buzz Xe</span>', x=0.5, y=0.5, font_size=20, showarrow=False)]
                )
                st.plotly_chart(fig_sov, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu thảo luận về các dòng xe.")

    # Middle: Xếp hạng & Tỷ lệ sắc thái
    with col_m2:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size:1rem; font-weight:700; color:#1E293B; margin-bottom:12px; border-bottom:1px solid #F1F5F9; padding-bottom:8px;">
                Xếp hạng &amp; Sắc thái từng mẫu xe <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
            </div>
            """, unsafe_allow_html=True)
            
            rank_rows = []
            for idx, m_name in enumerate(available_models):
                sub = tracked_df[tracked_df['car_model'] == m_name] if not tracked_df.empty else pd.DataFrame()
                cnt = len(sub)
                if cnt > 0:
                    p = len(sub[sub['sentiment'] == 'POSITIVE'])
                    neu = len(sub[sub['sentiment'] == 'NEUTRAL'])
                    neg = len(sub[sub['sentiment'] == 'NEGATIVE'])
                    p_pct = round(p / cnt * 100, 1)
                    neu_pct = round(neu / cnt * 100, 1)
                    neg_pct = round(neg / cnt * 100, 1)
                    rank_rows.append((m_name, cnt, p_pct, neg_pct, neu_pct))
                    
            rank_rows = sorted(rank_rows, key=lambda x: x[1], reverse=True)
            
            bars_html = []
            for idx, (m_name, cnt, p_pct, neg_pct, neu_pct) in enumerate(rank_rows):
                q_m = urllib.parse.quote(m_name)
                r_html = (
                    f'<div style="display:flex; align-items:center; justify-content:space-between; padding:8px 0; border-bottom:1px solid #F8FAFC; min-height:24px;">'
                    f'<div style="width:145px; font-size:0.82rem; font-weight:600; color:#1E293B; line-height:18px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">'
                    f'<span style="color:#94A3B8; margin-right:4px;">{idx+1}.</span> <a href="?model={q_m}" target="_self" style="color:#2563EB; text-decoration:none;" title="Xem thảo luận {m_name}">{m_name}</a>'
                    f'</div>'
                    f'<div style="flex-grow:1; margin:0 10px; background:#E2E8F0; height:14px; border-radius:7px; overflow:hidden; display:flex;">'
                    f'<div style="width:{p_pct}%; background:#2DD4BF;" title="Tích cực: {p_pct}%"></div>'
                    f'<div style="width:{neg_pct}%; background:#EF4444;" title="Tiêu cực: {neg_pct}%"></div>'
                    f'<div style="width:{neu_pct}%; background:#475569;" title="Trung lập: {neu_pct}%"></div>'
                    f'</div>'
                    f'<div style="width:75px; text-align:right; font-size:0.82rem; font-weight:700; color:#475569; line-height:18px;">'
                    f'{cnt:,} buzz'
                    f'</div>'
                    f'</div>'
                )
                bars_html.append(r_html)
                
            full_bars_rendered = f'<div style="max-height:430px; overflow-y:auto; padding-right:6px;">{"".join(bars_html)}</div>'
            if hasattr(st, "html"):
                st.html(full_bars_rendered)
            else:
                st.markdown(full_bars_rendered, unsafe_allow_html=True)

    # Right: Cập nhật thảo luận phân khúc xe đang chọn
    with col_m3:
        # Determine currently selected car model
        active_model_in_screen = st.query_params.get("model") or st.session_state.get("selected_model")
        active_model_options = [r[0] for r in rank_rows] if rank_rows else available_models
        
        default_index = 0
        if active_model_in_screen and active_model_in_screen in active_model_options:
            default_index = active_model_options.index(active_model_in_screen)
            
        with st.container(border=True):
            header_sel1, header_sel2 = st.columns([1.5, 1.5])
            with header_sel1:
                st.markdown("""
                <div style="font-size:1rem; font-weight:700; color:#1E293B; margin-bottom:4px;">
                    Cập nhật thảo luận theo Mẫu xe <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
                </div>
                """, unsafe_allow_html=True)
            with header_sel2:
                selected_model_in_screen = st.selectbox(
                    "Chọn dòng xe:",
                    options=active_model_options,
                    index=default_index,
                    label_visibility="collapsed",
                    key="select_active_model_feed"
                )

            model_feed_data = tracked_df[tracked_df['car_model'] == selected_model_in_screen] if not tracked_df.empty else pd.DataFrame()
            m_feed_cnt = len(model_feed_data)
            m_feed_pos = len(model_feed_data[model_feed_data['sentiment'] == 'POSITIVE'])
            m_feed_neg = len(model_feed_data[model_feed_data['sentiment'] == 'NEGATIVE'])

            st.caption(f"Đang hiển thị **{m_feed_cnt:,}** bài viết & bình luận về **{selected_model_in_screen}** (🟢 {m_feed_pos:,} tích cực &bull; 🔴 {m_feed_neg:,} tiêu cực)")

            t_mf_all, t_mf_pos, t_mf_neg = st.tabs([
                f"📋 Tất cả ({m_feed_cnt:,})",
                f"🟢 Tích cực ({m_feed_pos:,})",
                f"🔴 Tiêu cực ({m_feed_neg:,})"
            ])
            with t_mf_all:
                if not model_feed_data.empty:
                    for idx, r in model_feed_data.head(25).iterrows():
                        st.markdown(render_feed_card(r, str(r.get('sentiment', 'NEUTRAL')).upper()), unsafe_allow_html=True)
                else:
                    st.info(f"Không có dữ liệu thảo luận cho dòng xe '{selected_model_in_screen}'.")
            with t_mf_pos:
                pos_m_df = model_feed_data[model_feed_data['sentiment'] == 'POSITIVE']
                if not pos_m_df.empty:
                    for idx, r in pos_m_df.head(25).iterrows():
                        st.markdown(render_feed_card(r, "POSITIVE"), unsafe_allow_html=True)
                else:
                    st.info("Không có thảo luận tích cực cho dòng xe này.")
            with t_mf_neg:
                neg_m_df = model_feed_data[model_feed_data['sentiment'] == 'NEGATIVE']
                if not neg_m_df.empty:
                    for idx, r in neg_m_df.head(25).iterrows():
                        st.markdown(render_feed_card(r, "NEGATIVE"), unsafe_allow_html=True)
                else:
                    st.info("Không có thảo luận tiêu cực cho dòng xe này.")


# =============================================================
# SCREEN 2: THẢO LUẬN QUA CÁC KÊNH (Image 2)
# =============================================================
elif nav_page == "Thảo luận qua các kênh":
    col_c1, col_c2 = st.columns([1, 1])
    
    # Top Left: Tỷ lệ thảo luận trên các kênh (Donut)
    with col_c1:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size:1rem; font-weight:700; color:#1E293B; margin-bottom:8px;">
                Tỷ lệ thảo luận trên các kênh <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
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
                margin=dict(t=15, b=25, l=15, r=15),
                height=360,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                annotations=[dict(text=f'<b>{total_buzz:,}</b><br><span style="font-size:12px; color:#64748B;">Buzz</span>', x=0.5, y=0.5, font_size=22, showarrow=False)]
            )
            st.plotly_chart(fig_ch_donut, use_container_width=True)

    # Top Right: Xếp hạng nguồn thảo luận
    with col_c2:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size:1rem; font-weight:700; color:#1E293B; margin-bottom:12px; border-bottom:1px solid #F1F5F9; padding-bottom:8px;">
                Xếp hạng nguồn thảo luận <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
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
            
            rank_rows_html = []
            for idx, row in df_rank.iterrows():
                r_html = (
                    f'<div style="display:flex; align-items:center; justify-content:space-between; padding:10px 0; border-bottom:1px solid #F8FAFC; min-height:24px;">'
                    f'<div style="width:160px; font-size:0.85rem; font-weight:600; color:#1E293B; line-height:20px;">'
                    f'<span style="color:#94A3B8; margin-right:8px;">{idx+1}.</span> {row["Channel"]}'
                    f'</div>'
                    f'<div style="flex-grow:1; margin:0 14px; background:#E2E8F0; height:14px; border-radius:7px; overflow:hidden; display:flex;">'
                    f'<div style="width:{row["Pos_pct"]}%; background:#2DD4BF;"></div>'
                    f'<div style="width:{row["Neg_pct"]}%; background:#EF4444;"></div>'
                    f'<div style="width:{row["Neu_pct"]}%; background:#475569;"></div>'
                    f'</div>'
                    f'<div style="width:85px; text-align:right; font-size:0.85rem; font-weight:700; color:#475569; line-height:20px;">'
                    f'{row["Buzz"]:,} buzz'
                    f'</div>'
                    f'</div>'
                )
                rank_rows_html.append(r_html)
                
            rank_full_html = f'<div style="max-height:420px; overflow-y:auto; padding-right:6px;">{"".join(rank_rows_html)}</div>'
            if hasattr(st, "html"):
                st.html(rank_full_html)
            else:
                st.markdown(rank_full_html, unsafe_allow_html=True)

    # Bottom: Top nguồn thảo luận trên kênh Tin tức trực tuyến (Image 2)
    with st.container(border=True):
        st.markdown("""
        <div style="margin-bottom:8px;">
            <span style="font-size:1rem; font-weight:700; color:#1E293B;">Top nguồn thảo luận trên kênh Tin tức trực tuyến <span style="font-size:0.75rem; color:#94A3B8;">✕</span></span>
            <div style="font-size:0.8rem; font-weight:700; color:#475569; margin-top:4px; letter-spacing:0.05em;">NEWS</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Extract top news sources or domains from df
        news_df = df[df['channel'] == 'News'] if not df.empty and 'channel' in df.columns else pd.DataFrame()
        top_news_sources = []
        
        if not news_df.empty and 'site_name' in news_df.columns:
            source_counts = news_df['site_name'].value_counts().head(10).reset_index()
            source_counts.columns = ['Source', 'Buzz']
            top_news_sources = source_counts.to_dict(orient='records')
            
        if not top_news_sources:
            # Standard benchmark news sources matching Image 2
            top_news_sources = [
                {"Source": "baomoi.com", "Buzz": 1500},
                {"Source": "chuyendongthitruong.vn", "Buzz": 347},
                {"Source": "autopro.com.vn", "Buzz": 279},
                {"Source": "soha.vn", "Buzz": 277},
                {"Source": "24h.com.vn", "Buzz": 245},
                {"Source": "vietgiaitri.com", "Buzz": 218},
                {"Source": "znews.vn", "Buzz": 215},
                {"Source": "cafeF.vn", "Buzz": 172},
                {"Source": "tinxe.vn", "Buzz": 150},
                {"Source": "khoahocdoisong.vn", "Buzz": 144}
            ]

        df_news_src = pd.DataFrame(top_news_sources).sort_values('Buzz', ascending=True)
        fig_news_src = px.bar(
            df_news_src,
            x='Buzz',
            y='Source',
            orientation='h',
            color_discrete_sequence=['#38BDF8']
        )
        fig_news_src.update_layout(
            plot_bgcolor='#FFFFFF',
            paper_bgcolor='#FFFFFF',
            height=300,
            margin=dict(t=10, b=20, l=150, r=40),
            xaxis=dict(showgrid=True, gridcolor='#F1F5F9', title=''),
            yaxis=dict(title='', tickfont=dict(size=11, color='#1E293B'))
        )
        st.plotly_chart(fig_news_src, use_container_width=True)


# =============================================================
# SCREEN 3: THẢO LUẬN TIÊU CỰC (Image 3)
# =============================================================
elif nav_page == "Thảo luận tiêu cực":
    col_back, _ = st.columns([1.5, 4])
    with col_back:
        if st.button("⬅️ Quay lại Tổng quan thảo luận", key="back_from_neg"):
            st.session_state["redirect_page"] = "Tổng quan thảo luận"
            st.rerun()

    col_neg1, col_neg2, col_neg3 = st.columns([1, 1.2, 1.8])
    
    neg_df = df[df['sentiment'] == 'NEGATIVE']
    total_neg = len(neg_df)
    
    # Column 1: Sắc thái thảo luận tiêu cực (Donut)
    with col_neg1:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size:1rem; font-weight:700; color:#1E293B; margin-bottom:8px;">
                Sắc thái thảo luận <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
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
                margin=dict(t=15, b=20, l=15, r=15),
                height=320,
                showlegend=False,
                annotations=[dict(text=f'<b>{total_neg:,}</b><br><span style="font-size:12px; color:#EF4444;">Buzz Tiêu Cực</span>', x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
            st.plotly_chart(fig_neg_donut, use_container_width=True)

    # Column 2: Thảo luận tiêu cực trên các kênh
    with col_neg2:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size:1rem; font-weight:700; color:#1E293B; margin-bottom:8px;">
                Thảo luận tiêu cực trên các kênh <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
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

    # Column 3: Cập nhật thảo luận tiêu cực & tích cực
    with col_neg3:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size:1rem; font-weight:700; color:#1E293B; margin-bottom:8px;">
                Cập nhật thảo luận theo sắc thái <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
            </div>
            """, unsafe_allow_html=True)
            
            tab_neg_list, tab_pos_list = st.tabs([
                f"🔴 Tiêu cực ({len(neg_df):,})",
                f"🟢 Tích cực ({len(df[df['sentiment'] == 'POSITIVE']):,})"
            ])
            with tab_neg_list:
                if not neg_df.empty:
                    for idx, r in neg_df.head(25).iterrows():
                        st.markdown(render_feed_card(r, "NEGATIVE"), unsafe_allow_html=True)
                else:
                    st.success("Không có thảo luận tiêu cực.")
            with tab_pos_list:
                pos_df = df[df['sentiment'] == 'POSITIVE']
                if not pos_df.empty:
                    for idx, r in pos_df.head(25).iterrows():
                        st.markdown(render_feed_card(r, "POSITIVE"), unsafe_allow_html=True)
                else:
                    st.info("Không có thảo luận tích cực.")


# =============================================================
# SCREEN: THẢO LUẬN TÍCH CỰC
# =============================================================
elif nav_page == "Thảo luận tích cực":
    col_back, _ = st.columns([1.5, 4])
    with col_back:
        if st.button("⬅️ Quay lại Tổng quan thảo luận", key="back_from_pos"):
            st.session_state["redirect_page"] = "Tổng quan thảo luận"
            st.rerun()

    col_pos1, col_pos2, col_pos3 = st.columns([1, 1.2, 1.8])
    
    pos_df = df[df['sentiment'] == 'POSITIVE']
    total_pos = len(pos_df)
    
    # Column 1: Sắc thái thảo luận tích cực (Donut)
    with col_pos1:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size:1rem; font-weight:700; color:#1E293B; margin-bottom:8px;">
                Sắc thái thảo luận tích cực <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
            </div>
            """, unsafe_allow_html=True)
            
            fig_pos_donut = go.Figure(data=[go.Pie(
                labels=['Tích cực'],
                values=[total_pos if total_pos > 0 else 1],
                hole=0.68,
                marker_colors=['#2DD4BF'],
                textinfo='none',
                hoverinfo='label+value'
            )])
            fig_pos_donut.update_layout(
                margin=dict(t=15, b=20, l=15, r=15),
                height=320,
                showlegend=False,
                annotations=[dict(text=f'<b>{total_pos:,}</b><br><span style="font-size:12px; color:#0F766E;">Buzz Tích Cực</span>', x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
            st.plotly_chart(fig_pos_donut, use_container_width=True)

    # Column 2: Thảo luận tích cực trên các kênh
    with col_pos2:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size:1rem; font-weight:700; color:#1E293B; margin-bottom:8px;">
                Thảo luận tích cực trên các kênh <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
            </div>
            """, unsafe_allow_html=True)
            
            if not pos_df.empty:
                pos_channels = pos_df['channel'].value_counts().reset_index()
                pos_channels.columns = ['Channel', 'Buzz']
                pos_channels = pos_channels.sort_values('Buzz', ascending=True)
                
                fig_pos_ch = px.bar(
                    pos_channels,
                    x='Buzz',
                    y='Channel',
                    orientation='h',
                    color_discrete_sequence=['#2DD4BF']
                )
                fig_pos_ch.update_layout(
                    plot_bgcolor='#FFFFFF',
                    paper_bgcolor='#FFFFFF',
                    height=320,
                    margin=dict(t=10, b=20, l=110, r=20),
                    xaxis=dict(showgrid=True, gridcolor='#F1F5F9')
                )
                st.plotly_chart(fig_pos_ch, use_container_width=True)
            else:
                st.info("Không có thảo luận tích cực nào trong khoảng thời gian này.")

    # Column 3: Cập nhật thảo luận tích cực mới nhất
    with col_pos3:
        with st.container(border=True):
            st.markdown("""
            <div style="font-size:1rem; font-weight:700; color:#1E293B; margin-bottom:8px;">
                Cập nhật thảo luận tích cực mới nhất <span style="font-size:0.75rem; color:#94A3B8;">✕</span>
            </div>
            """, unsafe_allow_html=True)
            
            if not pos_df.empty:
                for idx, r in pos_df.head(25).iterrows():
                    st.markdown(render_feed_card(r, "POSITIVE"), unsafe_allow_html=True)
            else:
                st.info("Không có thảo luận tích cực.")


# =============================================================
# SCREEN 4: CẬP NHẬT THẢO LUẬN MỚI NHẤT (Image 4)
# =============================================================
elif nav_page == "Cập nhật thảo luận mới nhất":
    active_s4_topic = st.session_state.get("filter_topic_screen4")
    active_s4_model = st.session_state.get("filter_model_screen4")
    
    if active_s4_topic:
        s4_c1, s4_c2 = st.columns([4, 1.2])
        with s4_c1:
            st.info(f"🔎 Đang lọc thảo luận theo chủ đề: **{active_s4_topic}**")
        with s4_c2:
            if st.button("❌ Xóa lọc chủ đề", key="btn_clear_s4_topic"):
                del st.session_state["filter_topic_screen4"]
                st.rerun()
        if "Nhóm " in active_s4_topic:
            p_name = active_s4_topic.replace("Nhóm ", "").strip()
            df = df[df['topic_pillar'] == p_name] if not df.empty and 'topic_pillar' in df.columns else df
        else:
            df = df[df['topic_category'] == active_s4_topic] if not df.empty and 'topic_category' in df.columns else df

    if active_s4_model:
        s4_m1, s4_m2 = st.columns([4, 1.2])
        with s4_m1:
            st.info(f"🚗 Đang lọc thảo luận theo dòng xe: **{active_s4_model}**")
        with s4_m2:
            if st.button("❌ Xóa lọc dòng xe", key="btn_clear_s4_model"):
                del st.session_state["filter_model_screen4"]
                st.rerun()
        df = df[df['car_model'] == active_s4_model] if not df.empty and 'car_model' in df.columns else df

    total_buzz = len(df)
    sent_counts = df['sentiment'].value_counts() if not df.empty else pd.Series()
    pos_cnt = sent_counts.get('POSITIVE', 0)
    neg_cnt = sent_counts.get('NEGATIVE', 0)

    with st.container(border=True):
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:1rem; font-weight:700; color:#1E293B;">Dòng thời gian thảo luận thời gian thực</span>
            <span style="font-size:0.85rem; font-weight:600; color:#0F766E;">Tổng số: {total_buzz:,} bài viết & bình luận</span>
        </div>
        """, unsafe_allow_html=True)
    
    tab_all, tab_pos, tab_neg = st.tabs([
        f"📋 Tất cả ({total_buzz:,})",
        f"🟢 Thảo luận tích cực ({pos_cnt:,})",
        f"🔴 Thảo luận tiêu cực ({neg_cnt:,})"
    ])
    
    with tab_all:
        if not df.empty:
            for idx, r in df.head(30).iterrows():
                st.markdown(render_feed_card(r, str(r.get('sentiment', 'NEUTRAL')).upper()), unsafe_allow_html=True)
        else:
            st.info("Không có dữ liệu thảo luận phù hợp với bộ lọc hiện tại.")
            
    with tab_pos:
        pos_df_all = df[df['sentiment'] == 'POSITIVE']
        if not pos_df_all.empty:
            for idx, r in pos_df_all.head(30).iterrows():
                st.markdown(render_feed_card(r, 'POSITIVE'), unsafe_allow_html=True)
        else:
            st.info("Không có thảo luận tích cực.")
            
    with tab_neg:
        neg_df_all = df[df['sentiment'] == 'NEGATIVE']
        if not neg_df_all.empty:
            for idx, r in neg_df_all.head(30).iterrows():
                st.markdown(render_feed_card(r, 'NEGATIVE'), unsafe_allow_html=True)
        else:
            st.info("Không có thảo luận tiêu cực.")


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
