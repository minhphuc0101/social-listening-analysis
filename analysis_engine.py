import re
import datetime
from datetime import timezone, timedelta
import dateutil.parser

# Reference crawl base time (Vietnam timezone UTC+7)
VN_TZ = timezone(timedelta(hours=7))

# -------------------------------------------------------------
# 1. TIMESTAMP NORMALIZATION
# -------------------------------------------------------------
def parse_timestamp(raw_date, reference_time=None):
    """
    Normalizes varied timestamp formats from Facebook/TikTok into UTC datetime.
    Handles relative offsets ('2h', '1d', '30m', 'Just now'), localized English dates,
    and ISO strings.
    """
    if not raw_date or str(raw_date).strip().lower() in ['nan', 'none', '']:
        return None
        
    raw_str = str(raw_date).strip()
    if reference_time is None:
        reference_time = datetime.datetime.now(timezone.utc)
    elif reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    # 1. Check relative formats
    lower = raw_str.lower()
    if lower in ['just now', 'vừa xong', 'mới xong']:
        return reference_time
        
    # Match patterns like '2h', '12h', '1d', '3d', '45m', '10s', '1w'
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

    # 2. Check Facebook format: 'Tuesday, September 8, 2026 at 11:25 AM'
    clean_fb_date = re.sub(r'^[A-Za-z]+,\s*', '', raw_str) # strip weekday
    clean_fb_date = clean_fb_date.replace(' at ', ' ')
    clean_fb_date = clean_fb_date.replace('\u202f', ' ') # replace non-breaking spaces
    
    try:
        dt = dateutil.parser.parse(clean_fb_date)
        if dt.tzinfo is None:
            # Assume local Vietnam time (UTC+7)
            dt = dt.replace(tzinfo=VN_TZ).astimezone(timezone.utc)
        return dt
    except Exception:
        pass

    # 3. Standard fallback parser
    try:
        dt = dateutil.parser.parse(raw_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=VN_TZ).astimezone(timezone.utc)
        return dt
    except Exception:
        return None

# -------------------------------------------------------------
# 2. AUTOMOTIVE TAXONOMY & TOPIC CLASSIFICATION
# -------------------------------------------------------------
CAR_MODELS = {
    "Mitsubishi Xforce": [r"\bxforce\b", r"\bx-force\b"],
    "Mitsubishi Pajero Sport": [r"\bpajero\b", r"\bpajero\s*sport\b", r"\bps\b"],
    "Mitsubishi Destinator": [r"\bdestinator\b", r"\bdst\b"],
    "Mitsubishi Xpander": [r"\bxpander\b", r"\bxpander\s*cross\b"],
    "Mitsubishi Outlander": [r"\boutlander\b"],
    "Mitsubishi Triton": [r"\btriton\b"],
    "VinFast VF6": [r"\bvf6\b", r"\bvf\s*6\b"],
    "VinFast VF3": [r"\bvf3\b", r"\bvf\s*3\b"],
    "VinFast VF7": [r"\bvf7\b", r"\bvf\s*7\b"],
    "VinFast VF8": [r"\bvf8\b", r"\bvf\s*8\b"],
    "VinFast VF5": [r"\bvf5\b", r"\bvf\s*5\b"],
    "Toyota Yaris Cross": [r"\byaris\s*cross\b", r"\byaris\b"],
    "Toyota Corolla Cross": [r"\bcorolla\s*cross\b", r"\bcross\b"],
    "Toyota Vios": [r"\bvios\b"],
    "Toyota Fortuner": [r"\bfortuner\b"],
    "Skoda Kushaq": [r"\bkushaq\b", r"\bskoda\b"],
    "Mercedes-Benz W212 / E400": [r"\bw212\b", r"\be400\b", r"\bm276\b", r"\bmer\b", r"\bmercedes\b"],
    "Mazda CX-5": [r"\bcx-5\b", r"\bcx5\b", r"\bmazda\b"],
    "Hyundai Creta / SantaFe": [r"\bcreta\b", r"\bsantafe\b", r"\bsanta\s*fe\b", r"\btucson\b", r"\bhyundai\b"],
    "Kia Seltos / Sonet": [r"\bseltos\b", r"\bsonet\b", r"\bcarnival\b", r"\bkia\b"],
    "Ford Ranger / Everest": [r"\branger\b", r"\beverest\b", r"\bterritory\b", r"\bford\b"],
    "Honda CR-V / City": [r"\bcr-v\b", r"\bcrv\b", r"\bcity\b", r"\bcivic\b", r"\bhonda\b"]
}

TOPIC_RULES = {
    "Động cơ & Vận hành": [
        r"động cơ", r"máy", r"công suất", r"mã lực", r"twin turbo", r"turbo", r"hộp số",
        r"vận hành", r"leo dốc", r"cảm giác lái", r"khung gầm", r"treo", r"hao xăng",
        r"tiêu hao", r"ăn xăng", r"cách âm", r"đầm chắc", r"độ ồn"
    ],
    "Độ xe & Kỹ thuật": [
        r"độ", r"remap", r"tune", r"downpipe", r"hố vôi", r"mâm", r"body", r"lò xo",
        r"sên cam", r"muội carbon", r"nghịch ngợm", r"nâng cấp", r"lên 500hp", r"phục hồi"
    ],
    "Bảo hiểm & Đăng kiểm": [
        r"bảo hiểm", r"thân vỏ", r"2 chiều", r"hai chiều", r"va chạm", r"móp", r"húc",
        r"xước", r"đăng kiểm", r"rớt", r"thầy cụt", r"tem", r"phạt nguội", r"công an", r"giao thông"
    ],
    "Giá bán & Khuyến mãi": [
        r"giá", r"lăn bánh", r"củ", r"tỏi", r"triệu", r"trăm", r"trước bạ", r"giảm giá",
        r"ưu đãi", r"khuyến mãi", r"đại lý", r"sale", r"trả góp", r"cọc", r"mua xe"
    ],
    "Trang bị & Phụ kiện": [
        r"thảm", r"lót sàn", r"nappa", r"khóa cửa", r"lên kính", r"cắm zin", r"màn hình",
        r"cam 360", r"camera", r"phim cách nhiệt", r"đồ chơi", r"bọc ghế", r"phụ kiện"
    ],
    "So sánh & Tư vấn xe": [
        r"so sánh", r"phân vân", r"cân nhắc", r"hạng b", r"hạng c", r"mua xe lần đầu",
        r"tư vấn", r"nên mua", r"chọn con nào", r"đánh giá"
    ],
    "Chất lượng & Bảo dưỡng": [
        r"bảo dưỡng", r"hỏng", r"lỗi", r"thay thế", r"phụ tùng", r"bền", r"trâu bò",
        r"bảo hành", r"xưởng", r"gara"
    ],
    "Cộng đồng & Đời sống": [
        r"troll", r"chém gió", r"hội", r"anh em", r"hầm rượu", r"đi phượt", r"chia sẻ",
        r"kinh nghiệm", r"giao lưu", r"hài hước"
    ]
}

# -------------------------------------------------------------
# 3. SENTIMENT ANALYSIS (VIETNAMESE AUTOMOTIVE TUNED)
# -------------------------------------------------------------
POSITIVE_WORDS = [
    "bền", "ngon", "đẹp", "mượt", "keng", "trâu bò", "chất", "ưng", "hài lòng", "yêu",
    "thích", "lực", "tiện", "rẻ", "đáng tiền", "tuyệt", "tốt", "ok", "ổn", "phà phà",
    "gọn gàng", "lan tỏa", "ưu đãi", "sang xịn", "zin", "chuẩn"
]

NEGATIVE_WORDS = [
    "lỗi", "hỏng", "kém", "ồn", "hao xăng", "đắt", "chán", "bất tiện", "móp", "xước",
    "rớt", "tắc đường", "đíu", "đéo", "đm", "cay", "chê", "thất vọng", "ngáo giá",
    "ngáo", "nguy hiểm", "chết", "chửi", "lừa", "tệ", "yếu", "lỏ"
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
# 4. COMBINED RECORD ENRICHER
# -------------------------------------------------------------
def enrich_social_record(record, reference_time=None):
    """
    Enriches a raw comment/post record with normalized published_at,
    topic_category, car_model, tags, and sentiment.
    """
    content = str(record.get("Content", "") or record.get("content", "")).strip()
    description = str(record.get("Description", "") or record.get("description", "")).strip()
    full_text = f"{description} {content}".strip()
    
    # 1. Normalize Date
    raw_date = record.get("PublishedDate") or record.get("raw_published_date")
    p_at = record.get("published_at") or parse_timestamp(raw_date, reference_time)
    
    # 2. Detect Car Model
    detected_model = "Khác"
    for model_name, patterns in CAR_MODELS.items():
        if any(re.search(pat, full_text, re.IGNORECASE) for pat in patterns):
            detected_model = model_name
            break
            
    # 3. Detect Topic Category
    detected_topic = "Tổng quan"
    matched_topics = []
    for topic_name, patterns in TOPIC_RULES.items():
        if any(re.search(pat, full_text, re.IGNORECASE) for pat in patterns):
            matched_topics.append(topic_name)
    if matched_topics:
        detected_topic = matched_topics[0]
        
    # 4. Sentiment
    sentiment = record.get("Sentiment") or record.get("sentiment")
    if not sentiment or sentiment.upper() not in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
        sentiment = analyze_sentiment(content or description)
        
    # 5. Tags
    tags = []
    if detected_model != "Khác":
        tags.append(detected_model)
    if len(matched_topics) > 1:
        tags.extend(matched_topics[1:])

    enriched = dict(record)
    enriched["published_at"] = p_at
    enriched["raw_published_date"] = str(raw_date or "")
    enriched["topic_category"] = detected_topic
    enriched["car_model"] = detected_model
    enriched["sentiment"] = sentiment
    enriched["tags"] = tags
    return enriched
