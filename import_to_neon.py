import os
import sys
import datetime
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


from database import insert_discussions_batch, init_db, get_db_stats
from analysis_engine import enrich_social_record

def import_excel_file(filepath, max_rows=None):
    if not os.path.exists(filepath):
        print(f"[Import] File not found: {filepath}")
        return 0, 0
        
    print(f"\n=======================================================")
    print(f"📥 IMPORTING TO NEON: {filepath}")
    print(f"=======================================================")
    
    # Get file modification time as reference for relative timestamps
    mtime = os.path.getmtime(filepath)
    file_dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc)
    print(f"[Import] File modified at: {file_dt}")
    
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        print(f"[Import] Error reading Excel file: {e}")
        return 0, 0

    if max_rows and max_rows > 0:
        df = df.head(max_rows)
        
    total_rows = len(df)
    print(f"[Import] Read {total_rows} rows from Excel.")
    
    # Enrich each row
    enriched_rows = []
    for idx, row in df.iterrows():
        r_dict = row.to_dict()
        # Clean NaNs
        clean_dict = {k: ("" if pd.isna(v) else v) for k, v in r_dict.items()}
        enriched = enrich_social_record(clean_dict, reference_time=file_dt)
        enriched_rows.append(enriched)
        
    print(f"[Import] Enriched {len(enriched_rows)} rows. Inserting into Neon DB...")
    inserted, duplicates = insert_discussions_batch(enriched_rows, batch_size=400)
    print(f"[Import] Done! {inserted} new rows inserted, {duplicates} duplicates skipped.")
    return inserted, duplicates

def main():
    init_db()
    
    # 1. Prioritize recent 48h crawls first
    files_to_import = [
        "FB_Crawler_Packaged/social_media_output_autoforum_20260908.xlsx",
        "FB_Crawler_Packaged/social_media_output_20260907.xlsx",
        "unified_social_comments.xlsx"
    ]
    
    if len(sys.argv) > 1:
        # Allow passing specific file via CLI
        custom_file = sys.argv[1]
        if os.path.exists(custom_file):
            files_to_import = [custom_file]
            
    total_new = 0
    for fpath in files_to_import:
        if os.path.exists(fpath):
            ins, _ = import_excel_file(fpath)
            total_new += ins
            
    print("\n=======================================================")
    print("📊 NEON DATABASE STATUS AFTER IMPORT")
    print("=======================================================")
    stats = get_db_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
