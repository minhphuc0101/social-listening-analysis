import re
import datetime
from datetime import timezone, timedelta
import dateutil.parser

VN_TZ = timezone(timedelta(hours=7))

# -------------------------------------------------------------
# 1. TIMESTAMP NORMALIZATION
# -------------------------------------------------------------
def parse_timestamp(raw_date, reference_time=None):
    if not raw_date or str(raw_date).strip().lower() in ['nan', 'none', '']:
        return None
        
    raw_str = str(raw_date).strip()
    if reference_time is None:
        reference_time = datetime.datetime.now(timezone.utc)
    elif reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    lower = raw_str.lower()
    if lower in ['just now', 'vừa xong', 'mới xong']:
        return reference_time
        
    rel_match = re.match(r'^(\d+)\s*([smhdw])$', lower)
    if rel_match:
        val = int(rel_match.group(1))
        unit = rel_match.group(2)
        if unit == 's':
            return reference_time - timedelta(seconds=val)
        elif unit == 'm':
            return reference_time - timedelta(minutes=val)
        elif unit == 'h':
            return reference_time - timedelta(hours=val)
        elif unit == 'd':
            return reference_time - timedelta(days=val)
        elif unit == 'w':
            return reference_time - timedelta(weeks=val)

    clean_fb_date = re.sub(r'^[A-Za-z]+,\s*', '', raw_str)
    clean_fb_date = clean_fb_date.replace(' at ', ' ')
    clean_fb_date = clean_fb_date.replace('\u202f', ' ')
    
    try:
        dt = dateutil.parser.parse(clean_fb_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=VN_TZ).astimezone(timezone.utc)
        return dt
    except Exception:
        pass

    try:
        dt = dateutil.parser.parse(raw_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=VN_TZ).astimezone(timezone.utc)
        return dt
    except Exception:
        return None

# -------------------------------------------------------------
# 2. AUTOMOTIVE TAXONOMY - EXACT 3-PILLAR STRUCTURE (MATCHING DASHBOARD)
# -------------------------------------------------------------
HIERARCHICAL_TOPICS = {
    "Thương hiệu": {
        "Hoạt động truyền thông": [
            r"truyền thông", r"quảng cáo", r"poster", r"video", r"livestream", r"phỏng vấn",
            r"bài viết", r"trollxe", r"autodaily", r"autopro", r"xehay", r"bimatxebiz", r"fanpage"
        ],
        "Hệ thống phân phối": [
            r"đại lý", r"showroom", r"phân phối", r"giao xe", r"nhận xe", r"đặt cọc", r"cọc", r"sale"
        ],
        "Độ phủ chung": [
            r"thương hiệu", r"hãng xe", r"độ phủ", r"phổ biến", r"nổi tiếng", r"uy tín", r"tên tuổi"
        ],
        "Tình hình kinh doanh": [
            r"doanh số", r"bán chạy", r"thị phần", r"kinh doanh", r"báo cáo", r"tỷ phú", r"doanh thu", r"lãi"
        ],
        "Khởi kiện / Thu hồi": [
            r"thu hồi", r"triệu hồi", r"khởi kiện", r"kiện", r"phốt", r"bồi thường", r"lỗi hàng loạt"
        ],
        "Sự kiện": [
            r"sự kiện", r"triển lãm", r"ra mắt", r"ra mắt xe", r"trải nghiệm", r"lái thử", r"test drive"
        ],
        "Pháp lý": [
            r"pháp lý", r"đăng kiểm", r"rớt đăng kiểm", r"thầy cụt", r"biển số", r"phạt nguội", r"thủ tục"
        ]
    },
    "Sản phẩm": {
        "Thông tin sản phẩm": [
            r"thông tin", r"ra mắt", r"thế hệ mới", r"bản mới", r"facelift", r"phiên bản", r"option"
        ],
        "Khả năng vận hành": [
            r"vận hành", r"động cơ", r"máy", r"turbo", r"twin turbo", r"công suất", r"mã lực",
            r"hộp số", r"tăng tốc", r"leo dốc", r"cảm giác lái", r"đầm", r"bốc", r"khung gầm", r"trâu bò"
        ],
        "Công nghệ": [
            r"công nghệ", r"pin", r"catl", r"byd", r"quản lý nhiệt", r"adas", r"màn hình", r"tự lái", r"phần mềm"
        ],
        "Ngoại thất": [
            r"ngoại thất", r"thiết kế", r"dáng", r"đẹp", r"mâm", r"đèn", r"calang", r"màu sơn", r"body", r"form"
        ],
        "Tính năng an toàn": [
            r"an toàn", r"phanh", r"túi khí", r"cảnh báo", r"cảm biến", r"camera", r"va chạm", r"chống lật"
        ],
        "Nội thất & Không gian": [
            r"nội thất", r"ghế", r"7 chỗ", r"5 chỗ", r"khoang", r"rộng", r"hẹp", r"da nappa", r"thảm", r"cốp"
        ],
        "Đánh giá sản phẩm": [
            r"đánh giá", r"review", r"trải nghiệm", r"khen", r"chê", r"nhược điểm", r"ưu điểm", r"chất lượng"
        ],
        "Tiêu thụ năng lượng": [
            r"tiêu thụ", r"hao xăng", r"ăn xăng", r"tiết kiệm", r"pin sụt", r"quãng đường", r"sạc"
        ],
        "So sánh với đối thủ": [
            r"so sánh", r"đối thủ", r"hơn", r"kém", r"hạng b", r"hạng c", r"phân vân", r"cân nhắc", r"chọn con"
        ]
    },
    "Dịch vụ": {
        "Sửa chữa & Bảo hành": [
            r"sửa chữa", r"bảo dưỡng", r"bảo hành", r"gara", r"xưởng", r"phụ tùng", r"thay thế", r"bảo hiểm"
        ],
        "Chính sách bán hàng": [
            r"chính sách", r"trả góp", r"vay", r"ngân hàng", r"hợp đồng", r"ký hợp đồng"
        ],
        "Chăm sóc khách hàng": [
            r"chăm sóc", r"cskh", r"tư vấn", r"hỗ trợ", r"nhiệt tình", r"thái độ"
        ],
        "Trải nghiệm khách hàng": [
            r"trải nghiệm", r"hài lòng", r"thất vọng", r"tệ", r"tuyệt vời", r"bất tiện"
        ],
        "Giá / Khuyến mãi": [
            r"giá", r"khuyến mãi", r"ưu đãi", r"giảm giá", r"lăn bánh", r"trước bạ", r"củ", r"tỏi", r"triệu"
        ]
    }
}

CAR_MODELS = {
    "Mitsubishi Xforce": [r"\bxforce\b", r"\bx-force\b"],
    "Mitsubishi Pajero Sport": [r"\bpajero\b", r"\bpajero\s*sport\b", r"\bps\b"],
    "Mitsubishi Destinator": [r"\bdestinator\b", r"\bdst\b"],
    "Mitsubishi Xpander": [r"\bxpander\b", r"\bxpander\s*cross\b"],
    "Mitsubishi Outlander": [r"\boutlander\b"],
    "VinFast VF6": [r"\bvf6\b", r"\bvf\s*6\b"],
    "VinFast VF3": [r"\bvf3\b", r"\bvf\s*3\b"],
    "VinFast VF7": [r"\bvf7\b", r"\bvf\s*7\b"],
    "VinFast VF8": [r"\bvf8\b", r"\bvf\s*8\b"],
    "VinFast VF5": [r"\bvf5\b", r"\bvf\s*5\b"],
    "Toyota Veloz Cross": [r"\bveloz\b", r"\bveloz\s*cross\b"],
    "Toyota Innova Cross": [r"\binnova\s*cross\b", r"\bin\s*cross\b", r"\bỉn\s*cross\b", r"\binnova\b"],
    "Toyota Yaris Cross": [r"\byaris\s*cross\b", r"\byaris\b"],
    "Toyota Corolla Cross": [r"\bcorolla\s*cross\b", r"\bcorolla\b"],
    "Toyota Vios": [r"\bvios\b"],
    "Skoda Kushaq": [r"\bkushaq\b", r"\bskoda\b"],
    "Mercedes-Benz W212 / E400": [r"\bw212\b", r"\be400\b", r"\bm276\b", r"\bmer\b", r"\bmercedes\b"],
    "Ford Ranger / Everest": [r"\branger\b", r"\beverest\b", r"\bford\b"],
    "Hyundai Creta / SantaFe": [r"\bcreta\b", r"\bsantafe\b", r"\bhyundai\b"],
    "Kia Seltos / Sonet": [r"\bseltos\b", r"\bsonet\b", r"\bkia\b"]
}

# -------------------------------------------------------------
# 3. SENTIMENT ANALYSIS
# -------------------------------------------------------------
POSITIVE_WORDS = [
    "bền", "ngon", "đẹp", "mượt", "keng", "trâu bò", "chất", "ưng", "hài lòng", "yêu",
    "thích", "lực", "tiện", "rẻ", "đáng tiền", "tuyệt", "tốt", "ok", "ổn", "phà phà",
    "gọn gàng", "lan tỏa", "ưu đãi", "sang xịn", "zin", "chuẩn", "đỉnh"
]

NEGATIVE_WORDS = [
    "lỗi", "hỏng", "kém", "ồn", "hao xăng", "đắt", "chán", "bất tiện", "móp", "xước",
    "rớt", "tắc đường", "đíu", "đéo", "đm", "cay", "chê", "thất vọng", "ngáo giá",
    "ngáo", "nguy hiểm", "chết", "chửi", "lừa", "tệ", "yếu", "lỏ", "bẩn tính"
]

NEGATION_WORDS = ["không", "k", "chẳng", "chưa", "đừng", "kô", "ko"]

def analyze_sentiment(text):
    if not text:
        return "NEUTRAL"
    text_lower = text.lower()
    
    pos_score = 0
    neg_score = 0
    words = re.findall(r"\w+", text_lower)
    
    for i, w in enumerate(words):
        is_negated = False
        if i > 0 and words[i-1] in NEGATION_WORDS:
            is_negated = True
        elif i > 1 and words[i-2] in NEGATION_WORDS:
            is_negated = True
            
        if w in POSITIVE_WORDS:
            if is_negated:
                neg_score += 1.5
            else:
                pos_score += 1.0
        elif w in NEGATIVE_WORDS:
            if is_negated:
                pos_score += 1.0
            else:
                neg_score += 1.5

    if pos_score > neg_score and pos_score >= 1.0:
        return "POSITIVE"
    elif neg_score > pos_score and neg_score >= 1.0:
        return "NEGATIVE"
    return "NEUTRAL"

# -------------------------------------------------------------
# 4. TOPIC & CHANNEL CLASSIFIER
# -------------------------------------------------------------
def classify_topic_hierarchy(text):
    """
    Returns (pillar, sub_topic).
    Pillar is one of: 'Thương hiệu', 'Sản phẩm', 'Dịch vụ'.
    """
    text_lower = text.lower()
    
    for pillar, sub_dict in HIERARCHICAL_TOPICS.items():
        for sub_topic, patterns in sub_dict.items():
            if any(re.search(pat, text_lower) for pat in patterns):
                return pillar, sub_topic
                
    # Fallback to general product topic
    return "Sản phẩm", "Đánh giá sản phẩm"

def normalize_channel(raw_channel, url="", post_type=""):
    """
    Normalizes channel into standard Vietnamese social media channels:
    'TikTok', 'Facebook Pages', 'Facebook Groups', 'Facebook Users', 'News', 'YouTube', 'Forum'
    """
    raw = str(raw_channel or "").lower()
    u = str(url or "").lower()
    
    if "tiktok" in raw or "tiktok" in u:
        return "TikTok"
    if "youtube" in raw or "youtube" in u or "youtu.be" in u:
        return "YouTube"
    if "otofun" in raw or "otosaigon" in raw or "forum" in raw:
        return "Forum"
    if any(site in u for site in ["baomoi", "autopro", "autodaily", "24h", "vnexpress", "dantri"]):
        return "News"
    if "group" in raw or "/groups/" in u:
        return "Facebook Groups"
    if "page" in raw or "community" in raw or "/posts/" in u or "reel" in u:
        return "Facebook Pages"
    if "facebook" in raw or "facebook" in u:
        return "Facebook Users"
    return "Facebook Pages"

def enrich_social_record(record, reference_time=None):
    content = str(record.get("Content", "") or record.get("content", "")).strip()
    description = str(record.get("Description", "") or record.get("description", "")).strip()
    full_text = f"{description} {content}".strip()
    
    # 1. Date
    raw_date = record.get("PublishedDate") or record.get("raw_published_date")
    p_at = record.get("published_at") or parse_timestamp(raw_date, reference_time)
    
    # 2. Car Model
    detected_model = "Khác"
    if content:
        for model_name, patterns in CAR_MODELS.items():
            if any(re.search(pat, content, re.IGNORECASE) for pat in patterns):
                detected_model = model_name
                break
    if detected_model == "Khác" and description:
        for model_name, patterns in CAR_MODELS.items():
            if any(re.search(pat, description, re.IGNORECASE) for pat in patterns):
                detected_model = model_name
                break
            
    # 3. Topic Hierarchy
    pillar, sub_topic = classify_topic_hierarchy(full_text)
    
    # 4. Sentiment
    sentiment = record.get("Sentiment") or record.get("sentiment")
    if not sentiment or sentiment.upper() not in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
        sentiment = analyze_sentiment(content or description)
        
    # 5. Channel
    channel = normalize_channel(
        record.get("Channel") or record.get("channel"),
        url=record.get("UrlComment") or record.get("url_comment"),
        post_type=record.get("Type") or record.get("post_type")
    )

    enriched = dict(record)
    enriched["published_at"] = p_at
    enriched["raw_published_date"] = str(raw_date or "")
    enriched["topic_pillar"] = pillar
    enriched["topic_category"] = sub_topic
    enriched["car_model"] = detected_model
    enriched["sentiment"] = sentiment
    enriched["channel"] = channel
    return enriched
