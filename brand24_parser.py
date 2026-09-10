import os
import re
import datetime
from datetime import timezone, timedelta
import pandas as pd

try:
    from analysis_engine import enrich_social_record, normalize_channel
except ImportError:
    enrich_social_record = None
    normalize_channel = None

VN_TZ = timezone(timedelta(hours=7))

CATEGORY_MAP = {
    'forum': 'forumComment',
    'news': 'newsArticle',
    'videos': 'videoPost',
    'video': 'videoPost',
    'web': 'webMention',
    'blogs': 'blogPost',
    'blog': 'blogPost',
    'facebook': 'socialComment',
    'social': 'socialComment',
    'podcast': 'podcastMention',
    'podcasts': 'podcastMention'
}

def infer_campaign_from_filename(filename, default='Toyota'):
    if not filename:
        return default
    base = os.path.basename(filename).lower()
    if 'toyota' in base:
        return 'Toyota'
    if 'pajero' in base:
        return 'Pajero'
    if 'mitsubishi' in base:
        return 'Mitsubishi'
    if 'honda' in base:
        return 'Honda'
    # Try regex e.g. <name>_report
    m = re.match(r'^([a-zA-Z0-9_-]+)_report', base)
    if m:
        return m.group(1).replace('_', ' ').title()
    return default

def parse_brand24_datetime(date_val, hrs_val):
    """
    Combines Brand24 Date + Hrs into a timezone-aware datetime (GMT+7)
    and a formatted string: 2026-09-09 17:20:00+07:00
    """
    if pd.isna(date_val) or not str(date_val).strip():
        now = datetime.datetime.now(VN_TZ)
        return now, now.strftime('%Y-%m-%d %H:%M:%S+07:00')

    # 1. Parse date
    d_str = str(date_val).strip()
    # If date_val is already Timestamp or datetime
    if isinstance(date_val, (pd.Timestamp, datetime.datetime)):
        parsed_date = date_val.date()
    else:
        # Match YYYY-MM-DD
        m = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', d_str)
        if m:
            parsed_date = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        else:
            try:
                parsed_date = pd.to_datetime(d_str).date()
            except Exception:
                parsed_date = datetime.datetime.now(VN_TZ).date()

    # 2. Parse Hrs
    h, m, s = 0, 0, 0
    if not pd.isna(hrs_val) and str(hrs_val).strip():
        hrs_str = str(hrs_val).strip()
        if isinstance(hrs_val, datetime.time):
            h, m, s = hrs_val.hour, hrs_val.minute, hrs_val.second
        else:
            time_match = re.search(r'(\d{1,2})[:\.](\d{2})(?:[:\.](\d{2}))?', hrs_str)
            if time_match:
                h = int(time_match.group(1))
                m = int(time_match.group(2))
                s = int(time_match.group(3)) if time_match.group(3) else 0

    combined_dt = datetime.datetime(parsed_date.year, parsed_date.month, parsed_date.day, h, m, s, tzinfo=VN_TZ)
    iso_str = combined_dt.strftime('%Y-%m-%d %H:%M:%S+07:00')
    return combined_dt, iso_str

def parse_brand24_excel(filepath, campaign=None):
    """
    Parses a Brand24 Excel report file into normalized, schema-compliant records.
    Returns list of dicts.
    """
    if not os.path.exists(filepath):
        print(f"[Brand24 Parser] File not found: {filepath}")
        return []

    if campaign is None:
        campaign = infer_campaign_from_filename(filepath)

    try:
        xl = pd.ExcelFile(filepath)
    except Exception as e:
        print(f"[Brand24 Parser] Error opening Excel file {filepath}: {e}")
        return []

    # Identify mentions sheet
    target_sheet = None
    for s in xl.sheet_names:
        if 'mention' in s.lower():
            target_sheet = s
            break
    if not target_sheet:
        target_sheet = xl.sheet_names[0]

    # Read sheet without header first to detect header row
    df_raw = xl.parse(target_sheet, header=None)
    if df_raw.empty:
        print(f"[Brand24 Parser] Sheet '{target_sheet}' is empty.")
        return []

    # Find header row containing required columns
    header_idx = -1
    for idx, row in df_raw.head(10).iterrows():
        row_vals = [str(v).strip().lower() for v in row.values if pd.notna(v)]
        if any('source' in v for v in row_vals) and any('content' in v or 'date' in v for v in row_vals):
            header_idx = idx
            break

    if header_idx == -1:
        # Try finding row containing 'ID' or 'Date'
        for idx, row in df_raw.head(10).iterrows():
            row_vals = [str(v).strip() for v in row.values if pd.notna(v)]
            if 'ID' in row_vals and 'Date' in row_vals:
                header_idx = idx
                break

    if header_idx == -1:
        print(f"[Brand24 Parser] Could not find header row in '{target_sheet}'.")
        return []

    # Re-read with proper header row
    df = xl.parse(target_sheet, header=header_idx)

    # Check for empty "No mentions" state
    for col in df.columns:
        if df[col].astype(str).str.contains("No mentions", case=False, na=False).any():
            print(f"[Brand24 Parser] Report indicates 'No mentions' for this time period.")
            return []

    # Clean column names (strip whitespace)
    df.columns = [str(c).strip() for c in df.columns]

    # Required column names mapping (Brand24 -> Standard)
    col_find = {}
    for c in df.columns:
        c_low = c.lower()
        if c_low == 'source':
            col_find['source'] = c
        elif c_low == 'content':
            col_find['content'] = c
        elif c_low == 'title':
            col_find['title'] = c
        elif c_low == 'date':
            col_find['date'] = c
        elif c_low in ('hrs', 'hour', 'time'):
            col_find['hrs'] = c
        elif c_low == 'sentiment':
            col_find['sentiment'] = c
        elif c_low == 'domain':
            col_find['domain'] = c
        elif c_low == 'category':
            col_find['category'] = c
        elif c_low == 'tags':
            col_find['tags'] = c
        elif c_low == 'author':
            col_find['author'] = c

    # Filter out empty rows
    if 'source' in col_find:
        df = df[df[col_find['source']].notna() & (df[col_find['source']].astype(str).str.strip() != '') & (df[col_find['source']].astype(str).str.strip() != 'nan')]
    elif 'content' in col_find:
        df = df[df[col_find['content']].notna() & (df[col_find['content']].astype(str).str.strip() != '') & (df[col_find['content']].astype(str).str.strip() != 'nan')]

    if df.empty:
        print(f"[Brand24 Parser] No valid mention rows found in {filepath}.")
        return []

    results = []
    for _, row in df.iterrows():
        # 1. Source -> url_comment
        raw_source = str(row.get(col_find.get('source', ''), '') or '').strip()
        if raw_source.lower() in ('nan', 'none', 'no mentions', ''):
            continue

        # 2. Content -> content
        raw_content = str(row.get(col_find.get('content', ''), '') or '').strip()
        if raw_content.lower() in ('nan', 'none'):
            raw_content = ''

        # 3. Title -> description
        raw_title = str(row.get(col_find.get('title', ''), '') or '').strip()
        if raw_title.lower() in ('nan', 'none'):
            raw_title = ''

        # 4. Date + Hrs -> published_at & raw_published_date
        date_val = row.get(col_find.get('date', ''))
        hrs_val = row.get(col_find.get('hrs', ''))
        published_dt, raw_published_date = parse_brand24_datetime(date_val, hrs_val)

        # 5. Sentiment -> POSITIVE, NEGATIVE, NEUTRAL
        raw_sent = str(row.get(col_find.get('sentiment', ''), '') or '').strip().upper()
        if 'POS' in raw_sent:
            sentiment = 'POSITIVE'
        elif 'NEG' in raw_sent:
            sentiment = 'NEGATIVE'
        else:
            sentiment = 'NEUTRAL'

        # 6. Domain -> GroupName / Channel / SiteName
        domain = str(row.get(col_find.get('domain', ''), '') or '').strip()
        if domain.lower() in ('nan', 'none'):
            domain = ''

        # Fallback extract domain from url if domain is blank
        if not domain and raw_source.startswith('http'):
            try:
                from urllib.parse import urlparse
                domain = urlparse(raw_source).netloc.replace('www.', '')
            except Exception:
                domain = ''

        group_name = domain or 'Brand24'
        site_name = domain or 'Brand24'

        # Channel mapping
        if normalize_channel:
            channel = normalize_channel(domain, url=raw_source)
        else:
            channel = domain or 'Social Media'

        # 7. Category -> Type (post_type)
        raw_cat = str(row.get(col_find.get('category', ''), '') or '').strip().lower()
        post_type = CATEGORY_MAP.get(raw_cat, f"{raw_cat}Mention" if raw_cat and raw_cat != 'nan' else 'socialMention')

        # 8. Title / Domain -> Author
        raw_author = str(row.get(col_find.get('author', ''), '') or '').strip()
        if not raw_author or raw_author.lower() in ('nan', 'none', 'unknown'):
            if domain:
                raw_author = domain
            elif raw_title:
                raw_author = raw_title[:50]
            else:
                raw_author = 'Brand24 User'

        # 9. Tags -> list
        raw_tags = row.get(col_find.get('tags', ''))
        tags_list = []
        if pd.notna(raw_tags) and str(raw_tags).strip() and str(raw_tags).lower() != 'nan':
            tags_list = [t.strip() for t in str(raw_tags).split(',') if t.strip()]

        record = {
            'UrlComment': raw_source,
            'url_comment': raw_source,
            'Content': raw_content,
            'content': raw_content,
            'Description': raw_title,
            'description': raw_title,
            'PublishedDate': raw_published_date,
            'raw_published_date': raw_published_date,
            'published_at': published_dt,
            'Sentiment': sentiment,
            'sentiment': sentiment,
            'GroupName': group_name,
            'group_name': group_name,
            'SiteName': site_name,
            'site_name': site_name,
            'Channel': channel,
            'channel': channel,
            'Type': post_type,
            'post_type': post_type,
            'Author': raw_author,
            'author': raw_author,
            'tags': tags_list,
            'Campaign': campaign,
            'campaign': campaign
        }

        # Enrich automotive taxonomy if analysis_engine is available
        if enrich_social_record:
            enriched = enrich_social_record(record, reference_time=published_dt)
            record.update(enriched)
            # Ensure mapped fields are preserved
            record['campaign'] = campaign
            record['Campaign'] = campaign
            record['group_name'] = group_name
            record['GroupName'] = group_name
            record['post_type'] = post_type
            record['Type'] = post_type

        results.append(record)

    print(f"[Brand24 Parser] Successfully parsed {len(results)} mentions from {filepath}")
    return results
