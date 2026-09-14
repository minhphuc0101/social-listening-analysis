# Automotive NLP Language & Taxonomy Specification (AutoPulse / Toyota Social Intelligence)

> **Version:** 2.0.0  
> **Last Updated:** 2026-09-14  
> **Target Audience:** Large Language Models (LLMs), NLP Extractors, Social Listening Pipelines  
> **Primary Language:** Vietnamese (`vi-VN`) with English metadata annotations  
> **Domain:** Automotive Industry, Vietnamese Consumer Sentiment, Brand Objection Mining

---

## 1. Executive Summary & Purpose

This document provides the full, definitive Natural Language Processing (NLP) taxonomy, lexicographic rules, keyword variations (accented, unaccented, teencode, automotive slang), negation heuristics, and AI system prompts utilized by the **AutoPulse / Toyota Campaign Social Listening Dashboard**.

This specification is structured specifically for automated consumption by AI models (e.g., Google Gemini, OpenAI GPT, Claude) to perform:
1. **Zero-shot / Few-shot Classification** of unstructured Vietnamese automotive discussions.
2. **Deterministic & Rule-based Regex Matching** for high-precision objection tracking.
3. **Sentiment & Intent Disambiguation** (distinguishing genuine customer complaints from used-car sales ads or police traffic ticket reports).
4. **Automotive Topic Extraction** into standardized strategic pillars.

---

## 2. 21 Sensitive Objection Keywords & Pain Points (`TOYOTA_PAIN_POINTS`)

The system monitors 21 high-risk brand objection keywords across 6 strategic pillars. Each keyword includes full Vietnamese regex definitions, semantic meanings, and fanout variants (unaccented, slang, teencode).

### 2.1 Keyword Catalog & Fanout Mapping Table

| ID | Canonical Keyword | Standardized Name | Strategic Pillar | Regex Pattern (`re.IGNORECASE`) | Semantic Meaning / Automotive Context | Fanout Variants (No-accent, Teencode, Slang) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `lỗi` | Lỗi kỹ thuật / Lỗi xe | An toàn & Triệu hồi | `(?<!\w)lỗi(?!\w)` | Hardware/software/engine/steering/transmission defect on vehicle | `loi`, `bị lỗi`, `lỗi xe`, `hỏng lỗi`, `lỗi vặt`, `loi vat`, `lỗi lầm` |
| 2 | `chê` | Chê bai / Phản hồi tiêu cực | Thái độ & Trải nghiệm | `(?<!\w)chê(?!\w)` | Expressing dissatisfaction, criticism, or disparaging remarks | `che`, `bị chê`, `chê bai`, `ai cũng chê`, `dân mạng chê` |
| 3 | `ồn` | Ồn ào / Cách âm kém | Cách âm & Tiêu hao | `(?<!\w)ồn(?!\w)` | Excessive cabin noise, tire drone, road noise, poor NVH | `on`, `quá ồn`, `ồn ào`, `ồn vãi`, `ồn kinh`, `cách âm kém` |
| 4 | `cùi` | Cùi / Cùi bắp / Đồ cùi | Thiết kế & Trang bị | `(?<!\w)cùi(?!\w)` | Substandard quality, bare-bones interior, outdated equipment | `cui`, `cùi bắp`, `cui bap`, `cùi mía`, `nhìn cùi`, `đồ cùi` |
| 5 | `xấu` | Xấu (Ngoại/Nội thất) | Thiết kế & Trang bị | `(?<!xe\s)(?<!\w)xấu(?!\w)` | Ugly styling, clumsy aesthetics, unappealing front fascia | `xau`, `quá xấu`, `nhìn xấu`, `xấu đau xấu đớn`, `form xấu` |
| 6 | `xe xấu` | Xe xấu | Thiết kế & Trang bị | `(?<!\w)xe\s*xấu(?!\w)` | Explicit reference to an ugly car | `xe xau`, `xe nhìn xấu`, `xe qua xau` |
| 7 | `tốn xăng` | Tốn xăng | Cách âm & Tiêu hao | `(?<!\w)tốn\s*xăng(?!\w)` | High fuel consumption, gas guzzler | `ton xang`, `tốn xăng vãi`, `tốn xăng khiếp`, `tốn nhiên liệu` |
| 8 | `ăn xăng` | Ăn xăng | Cách âm & Tiêu hao | `(?<!\w)ăn\s*xăng(?!\w)` | Heavy fuel consumption, drinking gas | `an xang`, `ăn xăng như uống nước`, `uống xăng`, `uong xang` |
| 9 | `mắc` | Mắc / Đắt đỏ | Giá bán & Bán hàng | `(?<!thắc\s)(?<!vướng\s)(?<!bị\s)(?<!mắc\s)(?<!\w)mắc(?!\s*công)(?!\s*kẹt)(?!\s*mưa)(?!\s*cỡ)(?!\s*l\b)(?!\s*quân)(?!\s*dịch)(?!\w)` | Southern dialect for expensive/overpriced (strict boundary to avoid "mắc kẹt", "mắc công") | `mac`, `mắc quá`, `giá mắc`, `mắc vl`, `mắc khét`, `mắc vãi` |
| 10 | `ngáo` | Ngáo (Định giá / Chính sách) | Giá bán & Bán hàng | `(?<!\w)ngáo(?!\s*giá)(?!\w)` | Delusional pricing, brand arrogance | `ngao`, `ngáo tưởng`, `hãng ngáo`, `định giá ngáo` |
| 11 | `ngáo giá` | Ngáo giá | Giá bán & Bán hàng | `(?<!\w)ngáo\s*giá(?!\w)` | Explicit delusional overpricing | `ngao gia`, `ngáo giá vcl`, `định giá ngáo`, `ngao gia qua` |
| 12 | `lạc` | Bia kèm lạc / Lạc rang | Giá bán & Bán hàng | `(?<!bộ\s)(?<!hòa\s)(?<!hoà\s)(?<!liên\s)(?<!sa\s)(?<!lầm\s)(?<!\w)lạc(?!\s*đường)(?!\s*quan)(?!\s*hậu)(?!\s*lõng)(?!\s*lối)(?!\s*đề)(?!\w)` | Dealership markup, forcing extra accessories to get early car delivery | `lac`, `kèm lạc`, `bia kèm lạc`, `mua lạc`, `ăn lạc`, `tiền lạc` |
| 13 | `túi khí` | Túi khí (Không nổ / Bền) | An toàn & Triệu hồi | `(?<!\w)túi\s*khí(?!\w)` | Sarcastic airbag durability ("túi khí bền", airbags failing to deploy in crashes) | `tui khi`, `túi khí bền`, `túi khí không chịu nổ`, `đâm không nổ túi khí` |
| 14 | `thu hồi` | Thu hồi / Triệu hồi | An toàn & Triệu hồi | `(?<!\w)(thu\s*hồi\|triệu\s*hồi)(?!\w)` | Official recall, safety investigations | `thu hoi`, `trieu hoi`, `bị triệu hồi`, `lệnh triệu hồi` |
| 15 | `thùng tôn` | Thùng tôn / Vỏ mỏng | An toàn & Triệu hồi | `(?<!\w)thùng\s*tôn(?!\w)` | Metal tin can mockery, thin sheet metal, unsafe body shell | `thung ton`, `thùng tôn di động`, `vỏ thùng tôn`, `tôn mỏng` |
| 16 | `ế` | Ế / Bán ế ẩm | Doanh số & Thị trường | `(?<!\w)ế(?!\w)` | Poor sales, sitting unsold at dealerships | `e`, `bán ế`, `ế ẩm`, `ế dài cổ`, `ế chỏng chơ`, `top ế` |
| 17 | `hết thời` | Hết thời / Lỗi thời | Doanh số & Thị trường | `(?<!\w)hết\s*thời(?!\w)` | Lost market dominance, past its prime compared to rivals | `het thoi`, `xe hết thời`, `thương hiệu hết thời`, `hết thời hoàng kim` |
| 18 | `không thích` | Không thích | Thái độ & Trải nghiệm | `(?<!\w)không\s*thích(?!\w)` | Direct consumer rejection or aversion | `khong thich`, `k thích`, `ko thích`, `chẳng thích`, `kô thích` |
| 19 | `khinh thường` | Khinh thường khách hàng | Giá bán & Bán hàng | `(?<!\w)khinh\s*thường(?!\w)` | Arrogance towards customers, cutting standard options | `khinh thuong`, `khinh thường người dùng`, `khinh thường khách việt` |
| 20 | `xem thường` | Xem thường khách hàng | Giá bán & Bán hàng | `(?<!\w)xem\s*thường(?!\w)` | Disrespecting consumer intelligence or local safety regulations | `xem thuong`, `coi thường`, `xem thường khách`, `coi thường người mua` |
| 21 | `ảo tưởng` | Ảo tưởng sức mạnh / giá | Giá bán & Bán hàng | `(?<!\w)ảo\s*tưởng(?!\w)` | Overestimating brand equity and pricing above actual market value | `ao tuong`, `ảo tưởng giá`, `ảo tưởng sức mạnh`, `ao tuong suc manh` |

---

## 3. Negative Intent & Boundary Disambiguation Rules

To prevent false positive detection in noisy social discussions, the NLP engine enforces strict negative lookahead/lookbehind patterns and syntactic prefix/suffix verification.

### 3.1 Negation Pattern Engine (`PAIN_POINT_NEGATIONS`)
If a matching keyword is preceded by any of the following prefix patterns (within a 50-character backward window), the keyword is marked as **NEGATED** and dismissed:

```python
PAIN_POINT_NEGATIONS = [
    # General negation expressions: không, k, ko, khg, chẳng, chưa, chả, đâu, đâu có, làm gì có, ai
    r'\b(không|k|ko|khg|chẳng|chưa|chả|đâu\s*có|làm\s*gì\s*có|ai)\s*(hề|hề\s*có|bao\s*giờ|thấy|bị|có|phải|một|1|chút|tí|mấy|gì)?\s*$',
    
    # Dealership sales claims & warranty affirmations: bao test, bao check, bao, cam kết, zin đẹp
    r'\b(khỏi|miễn|hết\s*chỗ|bao\s*test|bao\s*check|bao|cam\s*kết|zin\s*đẹp|đẹp)\s*(không|k|ko)?\s*$',
    
    # Diminishing modifiers: ít, đỡ, bớt, chống, giảm, hạn chế
    r'\b(ít|đỡ|bớt|chống|giảm|hạn\s*chế)\s*(khi|bị)?\s*$',
    
    # Superlative praise inversions: khỏi chê, miễn chê, hết chỗ chê, không có gì để chê
    r'\b(khỏi|miễn|hết\s*chỗ|không\s*có\s*gì\s*để|k\s*có\s*gì\s*để|ko\s*có\s*gì\s*để|chẳng\s*có\s*gì\s*(để)?|không\s*chê\s*vào\s*đâu)\s*$'
]
```

### 3.2 Contextual Boundary Edge Cases

#### Case 1: Traffic Law Infractions vs. Vehicle Technical Defects (`lỗi`)
* **Problem:** Drivers post about police fines, lane violations, and speeding tickets using the word `lỗi` (e.g., *"xe mình bị dính lỗi vượt đèn vàng"*, *"bắt lỗi sai làn"*). This is NOT a vehicle hardware flaw.
* **Negative Filter Rule:**
  - Prefix exclusion: `\b(bắt|dính|phạt|bị\s*bắt|bị\s*phạt|mắc)\s*$`
  - Suffix exclusion: `^(:\s*)?(vi\s*phạm|giao\s*thông|phạt|làn|lane|tốc\s*độ|vượt|đèn|đỗ|dừng|nguội|lộn\s*lane)`
* **Result:** Only engineering issues (`lỗi hộp số`, `lỗi thước lái`, `bị lỗi màn hình`) trigger detection.

#### Case 2: Inverted Praise on Criticisms (`chê`)
* **Problem:** Phrases like *"xe này thì hết chỗ chê"*, *"chạy sướng không chê vào đâu được"* contain the token `chê` but mean highest praise.
* **Filter Rule:** Detect suffix `^vào\s*đâu\s*(được|nữa)` and prefix `(khỏi|miễn|hết\s*chỗ|không\s*có\s*gì\s*để)`.

#### Case 3: Polysemy of `mắc` and `lạc`
* **Word `mắc`:** Disambiguate price (`mắc` = expensive) from common idioms: `mắc công`, `mắc kẹt`, `mắc mưa`, `mắc cỡ`, `mắc dịch`, `vướng mắc`, `thắc mắc`.
* **Word `lạc`:** Disambiguate forced accessories (`bia kèm lạc`) from normal vocabulary: `lạc quan`, `lạc đường`, `lạc hậu`, `sa lạc`, `hòa lạc`, `liên lạc`.

---

## 4. Hierarchical Topic Taxonomy (`HIERARCHICAL_TOPICS`)

Social texts are categorized across a 3-Pillar structure encompassing 22 specialized subtopics:

```
Automotive Taxonomy
├── 1. Thương hiệu (Brand)
│   ├── Tổng quan (Overview & Reputation)
│   ├── Cộng đồng & Đời sống (Car Clubs & Social Media Life)
│   ├── Hoạt động truyền thông (Marketing, Ads, Media Reviews)
│   ├── Hệ thống phân phối (Dealerships, Showrooms, Delivery)
│   ├── Tình hình kinh doanh (Sales Figures, Market Share)
│   └── Khởi kiện / Thu hồi (Litigation, Scandals & Recalls)
├── 2. Sản phẩm (Product)
│   ├── Giá bán & Khuyến mãi (Pricing, Discounts, Registration Fees)
│   ├── Động cơ & Vận hành (Engine, Transmission, Durability, Performance)
│   ├── Độ xe & Kỹ thuật (Tuning, Remapping, Aftermarket Customization)
│   ├── Trang bị & Phụ kiện (Interior, 5-seater / 7-seater, Options)
│   ├── So sánh & Tư vấn xe (Comparison, Head-to-Head, Buying Decisions)
│   ├── Thông tin sản phẩm (Facelift, Specs, New Generation Launches)
│   ├── Công nghệ (Battery, ADAS, Infotainment, Autonomous Driving)
│   ├── Tính năng an toàn (Airbags, Brakes, Radar, Collision Avoidance)
│   └── Đánh giá sản phẩm (Comprehensive Reviews & Road Tests)
└── 3. Dịch vụ (Service)
    ├── Bảo hiểm & Đăng kiểm (Vehicle Inspection & Insurance Claims)
    ├── Chất lượng & Bảo dưỡng (Routine Maintenance, Oils, Batteries)
    ├── Sửa chữa & Bảo hành (Workshops, Repair Facilities, Parts Replacement)
    ├── Chính sách bán hàng (Bank Loans, Installment Plans, Contracts)
    ├── Chăm sóc khách hàng (Customer Service & Dealership Attitude)
    ├── Trải nghiệm khách hàng (Owner Satisfaction & Driver Journey)
    └── Mua bán & Rao vặt (Used Car Listings, Classifieds & Spam Ads)
```

### 4.1 Subtopic Pattern Definitions

```json
{
  "Thương hiệu": {
    "Tổng quan": ["thương hiệu", "hãng xe", "độ phủ", "phổ biến", "nổi tiếng", "uy tín", "tên tuổi"],
    "Cộng đồng & Đời sống": ["cộng đồng", "đời sống", "bài viết", "trollxe", "fanpage", "group", "anh em", "hội"],
    "Hoạt động truyền thông": ["truyền thông", "quảng cáo", "poster", "video", "livestream", "phỏng vấn", "autodaily", "autopro", "xehay", "bimatxebiz"],
    "Hệ thống phân phối": ["đại lý", "showroom", "phân phối", "giao xe", "nhận xe", "đặt cọc", "cọc", "sale"],
    "Tình hình kinh doanh": ["doanh số", "bán chạy", "thị phần", "kinh doanh", "báo cáo", "tỷ phú", "doanh thu", "lãi"],
    "Khởi kiện / Thu hồi": ["thu hồi", "triệu hồi", "khởi kiện", "kiện", "phốt", "bồi thường", "lỗi hàng loạt"]
  },
  "Sản phẩm": {
    "Giá bán & Khuyến mãi": ["(?<!đánh\\s)\\bgiá\\b", "\\bkhuyến\\s*mãi\\b", "\\bưu\\s*đãi\\b", "\\bgiảm\\s*giá\\b", "\\blăn\\s*bánh\\b", "\\btrước\\s*bạ\\b", "\\b\\d+\\s*củ\\b", "\\b\\d+\\s*tỏi\\b", "\\btriệu\\b"],
    "Động cơ & Vận hành": ["vận hành", "động cơ", "\\bmáy\\s+(xăng|dầu|điện|yếu|kêu|bốc|êm|gầm|lạnh)\\b", "\\bđộ\\s*bền\\b", "\\bbền\\s*bỉ\\b", "\\bbền\\s*lành\\b", "turbo", "twin turbo", "hộp số", "tăng tốc", "leo dốc", "cảm giác lái", "đầm", "bốc", "khung gầm"],
    "Độ xe & Kỹ thuật": ["độ", "kỹ thuật", "mâm", "đèn", "calang", "màu sơn", "body", "form", "tuning", "remap"],
    "Trang bị & Phụ kiện": ["trang bị", "phụ kiện", "nội thất", "ghế", "7 chỗ", "5 chỗ", "khoang", "rộng", "hẹp", "da nappa", "thảm", "cốp"],
    "So sánh & Tư vấn xe": ["so sánh", "đối thủ", "tư vấn", "\\b(ngon|tốt|đẹp|bền|ăn|hơn\\s*hẳn)\\s+hơn\\b", "\\bkém\\s*hơn\\b", "\\bthua\\s*kém\\b", "hạng b", "hạng c", "phân vân", "cân nhắc", "chọn con"],
    "Thông tin sản phẩm": ["thông tin", "ra mắt", "thế hệ mới", "bản mới", "facelift", "phiên bản", "option"],
    "Công nghệ": ["công nghệ", "pin", "catl", "byd", "quản lý nhiệt", "adas", "màn hình", "tự lái", "phần mềm"],
    "Tính năng an toàn": ["an toàn", "phanh", "túi khí", "cảnh báo", "cảm biến", "camera", "va chạm", "chống lật"],
    "Đánh giá sản phẩm": ["đánh giá", "review", "trải nghiệm", "khen", "chê", "nhược điểm", "ưu điểm", "chất lượng"]
  },
  "Dịch vụ": {
    "Bảo hiểm & Đăng kiểm": ["bảo hiểm", "đăng kiểm", "rớt đăng kiểm", "thầy cụt", "biển số", "phạt nguội", "thủ tục", "pháp lý"],
    "Chất lượng & Bảo dưỡng": ["\\bbảo\\s*dưỡng\\b", "\\bchất\\s*lượng\\b", "\\bsửa\\s*chữa\\b", "\\bgara\\b", "\\bxưởng\\b", "\\bphụ\\s*tùng\\b", "\\bắc\\s*quy\\b", "\\bthay\\s*nhớt\\b", "\\blọc\\s*gió\\b"],
    "Sửa chữa & Bảo hành": ["sửa chữa", "bảo dưỡng", "bảo hành", "gara", "xưởng", "phụ tùng", "thay thế"],
    "Chính sách bán hàng": ["chính sách", "trả góp", "vay", "ngân hàng", "hợp đồng", "ký hợp đồng"],
    "Chăm sóc khách hàng": ["chăm sóc", "cskh", "tư vấn", "hỗ trợ", "nhiệt tình", "thái độ"],
    "Trải nghiệm khách hàng": ["trải nghiệm", "hài lòng", "thất vọng", "tệ", "tuyệt vời", "bất tiện"],
    "Mua bán & Rao vặt": ["\\bbán\\s+(xe|chiếc|con|em|vios|cross|veloz|yaris|innova|camry|sedan|suv)\\b", "\\bchính\\s*chủ\\s*bán\\b", "\\bbao\\s*(check|test)\\b", "\\b(sđt|lh|zalo|hotline|liên\\s*hệ)\\s*[:.]?\\s*0\\d{8,10}\\b", "\\bxe\\s*lướt\\b"]
  }
}
```

---

## 5. Car Models Recognition Dictionary (`CAR_MODELS`)

Maps conversational vehicle aliases and informal abbreviations to official OEM names:

```json
{
  "Toyota Vios": ["\\bvios\\b"],
  "Toyota Camry": ["\\bcamry\\b"],
  "Toyota Corolla Cross": ["\\bcorolla\\s*cross\\b", "\\bcorolla\\b"],
  "Toyota Veloz Cross": ["\\bveloz\\b", "\\bveloz\\s*cross\\b"],
  "Toyota Innova Cross": ["\\binnova\\s*cross\\b", "\\bin\\s*cross\\b", "\\bỉn\\s*cross\\b", "\\binnova\\b"],
  "Toyota Yaris Cross": ["\\byaris\\s*cross\\b"],
  "Toyota Yaris": ["\\byaris\\b"],
  "Toyota Fortuner": ["\\bfortuner\\b"],
  "Toyota Altis": ["\\baltis\\b", "\\bcorolla\\s*altis\\b"],
  "Toyota Wigo": ["\\bwigo\\b"],
  "Toyota Raize": ["\\braize\\b"],
  "Toyota Hilux": ["\\bhilux\\b"],
  "Toyota Land Cruiser": ["\\bland\\s*cruiser\\b", "\\bprado\\b", "\\blc\\s*300\\b", "\\blc\\s*200\\b"],
  "Toyota Alphard": ["\\balphard\\b"],
  "Mitsubishi Xforce": ["\\bxforce\\b", "\\bx-force\\b"],
  "Mitsubishi Xpander": ["\\bxpander\\b", "\\bxpander\\s*cross\\b"],
  "Mitsubishi Pajero Sport": ["\\bpajero\\b", "\\bpajero\\s*sport\\b"],
  "Mitsubishi Destinator": ["\\bdestinator\\b", "\\bdst\\b"],
  "Mitsubishi Outlander": ["\\boutlander\\b"],
  "VinFast VF3": ["\\bvf3\\b", "\\bvf\\s*3\\b"],
  "VinFast VF5": ["\\bvf5\\b", "\\bvf\\s*5\\b"],
  "VinFast VF6": ["\\bvf6\\b", "\\bvf\\s*6\\b"],
  "VinFast VF7": ["\\bvf7\\b", "\\bvf\\s*7\\b"],
  "VinFast VF8": ["\\bvf8\\b", "\\bvf\\s*8\\b"],
  "Hyundai Creta / SantaFe": ["\\bcreta\\b", "\\bsantafe\\b", "\\bhyundai\\b"],
  "Kia Seltos / Sonet": ["\\bseltos\\b", "\\bsonet\\b"],
  "Ford Ranger / Everest": ["\\branger\\b", "\\beverest\\b", "\\bford\\b"],
  "Mercedes-Benz W212 / E400": ["\\bw212\\b", "\\be400\\b", "\\bm276\\b", "\\bmer\\b", "\\bmercedes\\b"],
  "Skoda Kushaq": ["\\bkushaq\\b", "\\bskoda\\b"]
}
```

---

## 6. Sentiment Lexicon & Scoring Engine

Sentiment classification evaluates three classes: `POSITIVE`, `NEGATIVE`, `NEUTRAL`.

### 6.1 Lexicon Dictionaries
* **Multi-word Positive Phrases (Weight 2.0):**
  `xuất sắc`, `quá xuất sắc`, `tuyệt vời`, `trâu bò`, `đáng tiền`, `phà phà`, `hài lòng`, `quá ngon`, `quá đẹp`, `quá tốt`, `quá đỉnh`, `quá bền`, `bền bỉ`, `độ bền cao`, `chất lượng tốt`, `sang xịn`, `đáng mua`, `chạy sướng`, `đi sướng`, `êm ái`, `tiết kiệm xăng`, `tiết kiệm`, `chắc chắn`, `máy bốc`, `máy êm`, `bền lành`, `xe lành`, `ít hỏng vặt`, `chẳng hỏng`, `không hỏng`.
* **Single-word Positive Tokens (Weight 1.0):**
  `bền`, `ngon`, `đẹp`, `mượt`, `keng`, `chất`, `ưng`, `yêu`, `thích`, `lực`, `tiện`, `rẻ`, `tuyệt`, `tốt`, `ok`, `ổn`, `zin`, `chuẩn`, `đỉnh`, `sướng`, `êm`, `khen`, `lành`.
* **Multi-word Negative Phrases (Weight 2.0):**
  `hao xăng`, `tắc đường`, `ngáo giá`, `bẩn tính`, `rớt đăng kiểm`, `hỏng hóc`, `lỗi lầm`, `bị lỗi`, `lỗi thước lái`, `lỗi hộp số`, `chảy dầu`, `kém chất lượng`, `quá tệ`, `quá chán`, `quá đắt`, `quá ồn`, `thất vọng`, `lừa đảo`, `phốt`, `cháy xe`.
* **Single-word Negative Tokens (Weight 1.0):**
  `lỗi`, `hỏng`, `kém`, `ồn`, `đắt`, `chán`, `bất tiện`, `móp`, `xước`, `rớt`, `đíu`, `đéo`, `đm`, `cay`, `chê`, `ngáo`, `nguy hiểm`, `chết`, `chửi`, `lừa`, `tệ`, `yếu`, `lỏ`.

### 6.2 Commercial Post Filter (`COMMERCIAL_PATTERNS`)
Commercial used car listings and promotional sales pitches (e.g. *"bán xe vios 2021 chính chủ bao check hãng giá inbox"*) frequently contain positive keywords (`đẹp`, `zin`, `bền`, `rẻ`) but represent promotional ads rather than organic user praise.
* If a post matches commercial advertising patterns, it is classified as **`NEUTRAL`** (or **`NEGATIVE`** only if containing 2+ distinct complaint tokens).

---

## 7. Channel Normalization Taxonomy

Standardizes unstructured raw channel descriptors and source URLs into 9 uniform categories:

```json
[
  {"Normalized": "TikTok", "Rules": "url or channel contains 'tiktok'"},
  {"Normalized": "YouTube", "Rules": "url contains 'youtube' or 'youtu.be'"},
  {"Normalized": "Facebook Groups", "Rules": "url contains '/groups/' or channel contains 'group'"},
  {"Normalized": "Facebook Pages", "Rules": "url contains '/posts/' or channel contains 'page' or 'community'"},
  {"Normalized": "Facebook Users", "Rules": "url contains '/user/', 'profile', or channel contains 'user'"},
  {"Normalized": "Forum", "Rules": "domain in ['otofun.net', 'otosaigon.com', 'voz.vn', 'tinhte.vn', 'webtretho.com']"},
  {"Normalized": "News", "Rules": "domain in ['vnexpress.net', 'dantri.com.vn', 'autopro.com.vn', 'autodaily.vn', 'vietnamnet.vn', 'thanhnien.vn', 'tuoitre.vn', 'vietnamplus.vn', 'cafef.vn', 'baomoi.com']"},
  {"Normalized": "Social Sites", "Rules": "url or channel contains ['threads.net', 'instagram', 'x.com', 'twitter']"},
  {"Normalized": "E-commerce Sites", "Rules": "domain in ['bonbanh.com', 'chotot.com', 'oto.com.vn', 'carmudi.vn']"}
]
```

---

## 8. AI Prompting Instructions & JSON Schemas

These system prompts instruct LLM agents (Google Gemini 1.5 Flash / Pro) when running automated comment extraction and intelligence briefing scans.

### 8.1 Comment NLP Tagging System Prompt

```markdown
You are an expert social listening analyst specializing in the Vietnamese automotive industry.
Analyze the sentiment, category, and entity tags for each social comment.

For each comment, output:
- Sentiment: "POSITIVE", "NEGATIVE", or "NEUTRAL"
- Label 1: Broad Category ("PERFORMANCE", "EXTERIOR", "PRICING", "INTERIOR", "SERVICE", "GENERAL")
- Label 2: Secondary Category (optional)
- Tag 1: Specific keyword/feature mentioned (e.g., "1.5L ENGINE", "AIRBAG", "SEAT", "SALES", "NOISE")
- Tag 2: Additional specific keyword (optional)

Respond ONLY with a valid JSON array matching this exact schema:
[
  {
    "id": 0,
    "Sentiment": "POSITIVE | NEGATIVE | NEUTRAL",
    "Lable 1": "string",
    "Lable 2": "string",
    "Tag 1": "string",
    "Tag 2": "string"
  }
]
```

### 8.2 Daily 48H Executive Intelligence Briefing Prompt

```markdown
Bạn là Giám đốc Nghiên cứu Thị trường & Phân tích Dữ liệu Mạng Xã hội ngành Ô tô tại Việt Nam.
Dưới đây là dữ liệu thảo luận được trích xuất trong 48 GIỜ QUA từ các diễn đàn lớn (Troll Xe, Otofun, Otosaigon, Xe Cưng, hội nhóm thương hiệu...):

YÊU CẦU:
Viết bản báo cáo tóm tắt tình hình 48 giờ (Daily 48H Intelligence Briefing) bằng tiếng Việt thật sắc sảo, chuyên nghiệp, hấp dẫn theo định dạng Markdown với 5 phần:

1. **TÓM TẮT NHANH (Executive TL;DR)**: 3-4 gạch đầu dòng cốt lõi nhất về những gì đang xảy ra trong 48h qua.
2. **TOP CHỦ ĐỀ & TRANH LUẬN NÓNG NHẤT (What's Hot)**: Phân tích 3-4 chủ đề / bài viết bùng nổ, lý do tranh cãi, quan điểm cộng đồng.
3. **TIẾNG NÓI KHÁCH HÀNG (Driver Voice - Praise & Pain Points)**: Người dùng đang khen điều gì? Đang gặp bức xúc / lo ngại gì (bảo hiểm, đăng kiểm, máy móc, giá cả)?
4. **NHỊP ĐẬP DÒNG XE (Model & Brand Momentum)**: Đánh giá sức nóng và cảm xúc của các mẫu xe nổi bật (Mitsubishi Xforce/Pajero, VinFast, Toyota Vios/Innova Cross, Skoda Kushaq, Mercedes...).
5. **KHUYẾN NGHỊ HÀNH ĐỘNG (Strategic Recommendations)**: 2-3 gợi ý cho đội ngũ marketing / truyền thông / đại lý.

Hãy viết trực diện, số liệu dẫn chứng cụ thể, văn phong chuyên nghiệp.
```

---

## 9. Integration Checklist for Downstream AI Agents

When deploying an LLM or subagent to process new social listening batches:
1. **Always apply `PAIN_POINT_NEGATIONS`** before flagging any text as containing a brand objection.
2. **Always cross-check `COMMERCIAL_PATTERNS`** to avoid treating car salesperson listings as consumer positive buzz.
3. **Always map vehicle aliases through `CAR_MODELS`** to ensure clean aggregations across OEM reports.
4. **Respect case-insensitive Vietnamese diacritics**: Regexes with `re.IGNORECASE` properly match both accented uppercase/lowercase (`LỖI`, `Lỗi`, `lỗi`).
