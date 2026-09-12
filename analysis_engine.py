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
    
    # Vietnamese Facebook format: "Thứ Năm, 10 Tháng 9, 2026 lúc 11:03" or "10 Tháng 9, 2026"
    vn_match = re.search(r'(\d{1,2})\s+Tháng\s+(\d{1,2}),?\s+(\d{4})(?:\s+lúc\s+(\d{1,2}):(\d{2}))?', raw_str, re.IGNORECASE)
    if vn_match:
        d, mth, y, h, mn = vn_match.groups()
        hour = int(h) if h is not None else 0
        minute = int(mn) if mn is not None else 0
        try:
            return datetime.datetime(int(y), int(mth), int(d), hour, minute, tzinfo=VN_TZ).astimezone(timezone.utc)
        except Exception:
            pass

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
        "Tổng quan": [
            r"thương hiệu", r"hãng xe", r"độ phủ", r"phổ biến", r"nổi tiếng", r"uy tín", r"tên tuổi"
        ],
        "Cộng đồng & Đời sống": [
            r"cộng đồng", r"đời sống", r"bài viết", r"trollxe", r"fanpage", r"group", r"anh em", r"hội"
        ],
        "Hoạt động truyền thông": [
            r"truyền thông", r"quảng cáo", r"poster", r"video", r"livestream", r"phỏng vấn",
            r"autodaily", r"autopro", r"xehay", r"bimatxebiz"
        ],
        "Hệ thống phân phối": [
            r"đại lý", r"showroom", r"phân phối", r"giao xe", r"nhận xe", r"đặt cọc", r"cọc", r"sale"
        ],
        "Tình hình kinh doanh": [
            r"doanh số", r"bán chạy", r"thị phần", r"kinh doanh", r"báo cáo", r"tỷ phú", r"doanh thu", r"lãi"
        ],
        "Khởi kiện / Thu hồi": [
            r"thu hồi", r"triệu hồi", r"khởi kiện", r"kiện", r"phốt", r"bồi thường", r"lỗi hàng loạt"
        ]
    },
    "Sản phẩm": {
        "Giá bán & Khuyến mãi": [
            r"(?<!đánh\s)\bgiá\b", r"\bkhuyến\s*mãi\b", r"\bưu\s*đãi\b", r"\bgiảm\s*giá\b",
            r"\blăn\s*bánh\b", r"\btrước\s*bạ\b", r"\b\d+\s*củ\b", r"\b(vài|mấy|nhiêu)\s*củ\b",
            r"\b\d+\s*tỏi\b", r"\b(vài|mấy)\s*tỏi\b", r"\btriệu\b"
        ],
        "Động cơ & Vận hành": [
            r"vận hành", r"động cơ", r"\bmáy\s+(xăng|dầu|điện|yếu|kêu|bốc|êm|gầm|lạnh)\b",
            r"\bkhoang\s*máy\b", r"\bchết\s*máy\b", r"\bhỏng\s*máy\b",
            r"\bđộ\s*bền\b", r"\bbền\s*bỉ\b", r"\bbền\s*lành\b", r"\bxe\s*lành\b",
            r"turbo", r"twin turbo", r"công suất", r"mã lực",
            r"hộp số", r"tăng tốc", r"leo dốc", r"cảm giác lái", r"đầm", r"bốc", r"khung gầm", r"trâu bò"
        ],
        "Độ xe & Kỹ thuật": [
            r"độ", r"kỹ thuật", r"mâm", r"đèn", r"calang", r"màu sơn", r"body", r"form", r"tuning", r"remap"
        ],
        "Trang bị & Phụ kiện": [
            r"trang bị", r"phụ kiện", r"nội thất", r"ghế", r"7 chỗ", r"5 chỗ", r"khoang", r"rộng", r"hẹp", r"da nappa", r"thảm", r"cốp"
        ],
        "So sánh & Tư vấn xe": [
            r"so sánh", r"đối thủ", r"tư vấn", r"\b(ngon|tốt|đẹp|bền|ăn|hơn\s*hẳn)\s+hơn\b", r"\bhơn\s+(con|xe|tiền)\b",
            r"\bkém\s*hơn\b", r"\bthua\s*kém\b", r"hạng b", r"hạng c", r"phân vân", r"cân nhắc", r"chọn con"
        ],
        "Thông tin sản phẩm": [
            r"thông tin", r"ra mắt", r"thế hệ mới", r"bản mới", r"facelift", r"phiên bản", r"option"
        ],
        "Công nghệ": [
            r"công nghệ", r"pin", r"catl", r"byd", r"quản lý nhiệt", r"adas", r"màn hình", r"tự lái", r"phần mềm"
        ],
        "Tính năng an toàn": [
            r"an toàn", r"phanh", r"túi khí", r"cảnh báo", r"cảm biến", r"camera", r"va chạm", r"chống lật"
        ],
        "Đánh giá sản phẩm": [
            r"đánh giá", r"review", r"trải nghiệm", r"khen", r"chê", r"nhược điểm", r"ưu điểm", r"chất lượng"
        ]
    },
    "Dịch vụ": {
        "Bảo hiểm & Đăng kiểm": [
            r"bảo hiểm", r"đăng kiểm", r"rớt đăng kiểm", r"thầy cụt", r"biển số", r"phạt nguội", r"thủ tục", r"pháp lý"
        ],
        "Chất lượng & Bảo dưỡng": [
            r"\bbảo\s*dưỡng\b", r"\bchất\s*lượng\b", r"\bsửa\s*chữa\b", r"\bgara\b", r"\bxưởng\b",
            r"\bphụ\s*tùng\b", r"\bthay\s*thế\b", r"\bđịnh\s*kỳ\b",
            r"\bắc\s*quy\b", r"\bbình\s*ắc\s*quy\b", r"\bbình\s*xe\b",
            r"\bthay\s*nhớt\b", r"\bnhớt\b", r"\blọc\s*nhớt\b", r"\blọc\s*gió\b",
            r"\bmá\s*phanh\b", r"\bthay\s*dầu\b", r"\bdầu\s*máy\b"
        ],
        "Sửa chữa & Bảo hành": [
            r"sửa chữa", r"bảo dưỡng", r"bảo hành", r"gara", r"xưởng", r"phụ tùng", r"thay thế"
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
        "Mua bán & Rao vặt": [
            r"\bbán\s+(xe|chiếc|con|em|vios|cross|veloz|yaris|innova|camry|sedan|suv)\b",
            r"\bcần\s+(bán|nhượng|sang\s*nhượng|tìm\s*mua)\b",
            r"\bchính\s*chủ\s*(bán|cần\s*bán|nhượng)\b",
            r"\bxem\s*xe\s*(tại|ở|trực\s*tiếp)\b",
            r"\bbao\s*(check|test)\b",
            r"\b(sđt|lh|zalo|hotline|liên\s*hệ|alo\s*em)\s*[:.]?\s*0\d{8,10}\b",
            r"\b0[35789]\d{8}\b",
            r"\bshopee\.vn\b",
            r"\bcắm\s*(xe|sổ|đăng\s*ký)\b",
            r"\bthu\s*mua\s*xe\b",
            r"\bxe\s*lướt\b",
            r"\bchào\s*bán\b",
            r"\bđang\s*bán\b",
            r"\bgiá\s*công\s*khai\b",
            r"\binbox\s*(e|em)\s*(giá|nhé|nha)\b",
            r"\bxe\s*sẵn\s*giao\s*ngay\b",
            r"\bhỗ\s*trợ\s*trả\s*góp\b"
        ]
    }
}

CAR_MODELS = {
    "Mitsubishi Xforce": [r"\bxforce\b", r"\bx-force\b"],
    "Mitsubishi Pajero Sport": [r"\bpajero\b", r"\bpajero\s*sport\b"],
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
    "Kia Seltos / Sonet": [r"\bseltos\b", r"\bsonet\b"]
}

# -------------------------------------------------------------
# 3. SENTIMENT ANALYSIS
# -------------------------------------------------------------
POSITIVE_PHRASES = [
    r"\bxuất\s*sắc\b", r"\bquá\s*xuất\s*sắc\b", r"\btuyệt\s*vời\b", r"\btrâu\s*bò\b",
    r"\bđáng\s*tiền\b", r"\bphà\s*phà\b", r"\bhài\s*lòng\b", r"\bquá\s*ngon\b",
    r"\bquá\s*đẹp\b", r"\bquá\s*tốt\b", r"\bquá\s*đỉnh\b", r"\bquá\s*bền\b",
    r"\bbền\s*bỉ\b", r"\bđộ\s*bền\s*(cao|tốt|ổn|ngon|nhỉnh|hơn)\b", r"\bchất\s*lượng\s*tốt\b",
    r"\bgọn\s*gàng\b", r"\blan\s*tỏa\b", r"\bsang\s*xịn\b", r"\bđáng\s*mua\b",
    r"\bchạy\s*sướng\b", r"\bđi\s*sướng\b", r"\bêm\s*ái\b", r"\btiết\s*kiệm\s*xăng\b",
    r"\btiết\s*kiệm\b", r"\bchắc\s*chắn\b", r"\bchạy\s*bốc\b", r"\bmáy\s*bốc\b",
    r"\bmáy\s*êm\b", r"\brất\s*ổn\b", r"\brất\s*tốt\b", r"\brất\s*bền\b", r"\bquá\s*ổn\b",
    r"\brất\s*ngon\b", r"\bkhá\s*ngon\b", r"\bkhá\s*ổn\b", r"\bbền\s*lành\b",
    r"\bxe\s*lành\b", r"\bít\s*hỏng\s*(vặt|hóc)?\b", r"\bchẳng\s*hỏng\b",
    r"\bkhông\s*hỏng\b", r"\bchưa\s*hỏng\b"
]

POSITIVE_WORDS = [
    "bền", "ngon", "đẹp", "mượt", "keng", "chất", "ưng", "yêu",
    "thích", "lực", "tiện", "rẻ", "tuyệt", "tốt", "ok", "ổn",
    "ưu đãi", "zin", "chuẩn", "đỉnh", "sướng", "êm", "khen", "lành"
]

NEGATIVE_PHRASES = [
    r"\bhao\s*xăng\b", r"\btắc\s*đường\b", r"\bngáo\s*giá\b", r"\bbẩn\s*tính\b",
    r"\brớt\s*đăng\s*kiểm\b", r"\bhỏng\s*hóc\b", r"\blỗi\s*lầm\b", r"\bbị\s*lỗi\b",
    r"\blỗi\s*thước\s*lái\b", r"\blỗi\s*hộp\s*số\b", r"\bchảy\s*dầu\b", r"\bkém\s*chất\s*lượng\b",
    r"\bquá\s*tệ\b", r"\bquá\s*chán\b", r"\bquá\s*đắt\b", r"\bquá\s*ồn\b",
    r"\bthất\s*vọng\b", r"\blừa\s*đảo\b", r"\bphốt\b", r"\bcháy\s*xe\b"
]

NEGATIVE_WORDS = [
    "lỗi", "hỏng", "kém", "ồn", "đắt", "chán", "bất tiện", "móp", "xước",
    "rớt", "đíu", "đéo", "đm", "cay", "chê",
    "ngáo", "nguy hiểm", "chết", "chửi", "lừa", "tệ", "yếu", "lỏ"
]

NEGATION_WORDS = ["không", "k", "chẳng", "chưa", "đừng", "kô", "ko"]

COMMERCIAL_PATTERNS = [
    r"\bbán\s+(xe|chiếc|con|em|vios|cross|veloz|yaris|innova|camry|sedan|suv)\b",
    r"\bcần\s+(bán|nhượng|sang\s*nhượng|tìm\s*mua)\b",
    r"\bchính\s*chủ\s*(bán|cần\s*bán|nhượng)\b",
    r"\bxem\s*xe\s*(tại|ở|trực\s*tiếp)\b",
    r"\bbao\s*(check|test)\b",
    r"\b(sđt|lh|zalo|hotline|liên\s*hệ|alo\s*em)\s*[:.]?\s*0\d{8,10}\b",
    r"\b0[35789]\d{8}\b",
    r"\bshopee\.vn\b",
    r"\bcắm\s*(xe|sổ|đăng\s*ký)\b",
    r"\bthu\s*mua\s*xe\b",
    r"\bxe\s*lướt\b",
    r"\bchào\s*bán\b",
    r"\bđang\s*bán\b",
    r"\bgiá\s*công\s*khai\b",
    r"\binbox\s*(e|em)\s*(giá|nhé|nha)\b",
    r"\bxe\s*sẵn\s*giao\s*ngay\b",
    r"\bhỗ\s*trợ\s*trả\s*góp\b",
    r"\bmáy\s*số\s*zin\b",
    r"\bsơn\s*zin\b",
    r"\blốp\s*theo\s*xe\b",
    r"\bchạy\s*chuẩn\s*\d+\s*(vạn|v|km)\b",
    r"\bodo\s*chuẩn\b",
    r"\bxe\s*còn\s*rất\s*mới\b",
    r"\bbao\s*hồ\s*sơ\b",
    r"\bcam\s*kết\s*không\s*(đâm\s*đụng|ngập\s*nước)\b"
]

def is_commercial_buy_sell(text):
    if not text:
        return False
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in COMMERCIAL_PATTERNS)

def analyze_sentiment(text):
    if not text:
        return "NEUTRAL"
    text_lower = text.lower()
    
    # Commercial buy/sell listings (car ads, sales links) are promotional/commercial, NOT customer praise.
    if is_commercial_buy_sell(text_lower):
        words = re.findall(r"\w+", text_lower)
        neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
        if neg_count >= 2:
            return "NEGATIVE"
        return "NEUTRAL"

    pos_score = 0.0
    neg_score = 0.0

    # 1. Check multi-word positive phrases (weight 2.0)
    for p in POSITIVE_PHRASES:
        for m in re.finditer(p, text_lower):
            start = m.start()
            prefix = text_lower[max(0, start-15):start]
            if any(nw in prefix.split() for nw in NEGATION_WORDS):
                neg_score += 1.5
            else:
                pos_score += 2.0

    # 2. Check multi-word negative phrases (weight 2.0)
    for p in NEGATIVE_PHRASES:
        for m in re.finditer(p, text_lower):
            start = m.start()
            prefix = text_lower[max(0, start-15):start]
            if any(nw in prefix.split() for nw in NEGATION_WORDS):
                pos_score += 1.5
            else:
                neg_score += 2.0

    # 3. Check individual words
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
            if i > 0 and words[i-1] in ["ít", "hiếm", "không", "chẳng", "chưa"]:
                pos_score += 1.5
            elif is_negated:
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
    
    # Check commercial buy/sell first
    if is_commercial_buy_sell(text_lower):
        return "Dịch vụ", "Mua bán & Rao vặt"

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
