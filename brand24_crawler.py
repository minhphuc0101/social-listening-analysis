import os
import sys
import argparse
import datetime
from datetime import timezone, timedelta
from dotenv import load_dotenv

# Reconfigure console output for UTF-8 on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

load_dotenv()

import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from brand24_parser import parse_brand24_excel
from database import (
    insert_discussions_batch, get_db_stats,
    record_crawl_log, get_crawl_logs, get_missing_or_failed_days
)

# Default constants
DEFAULT_USERNAME = os.getenv("BRAND24_USERNAME", "account02@digimind.asia")
DEFAULT_PASSWORD = os.getenv("BRAND24_PASSWORD", "Dgm@7979")
DEFAULT_PROJECT_ID = os.getenv("BRAND24_PROJECT_ID", "1397643108")
DEFAULT_CAMPAIGN = "Toyota"

VN_TZ = timezone(timedelta(hours=7))

def get_target_date(days_back=1, custom_date=None):
    """Calculates target date in Vietnam Time (GMT+7)."""
    if custom_date:
        return custom_date.strip()
    now_vn = datetime.datetime.now(VN_TZ)
    target_dt = now_vn - timedelta(days=int(days_back))
    return target_dt.strftime("%Y-%m-%d")

def dismiss_popups(page):
    """Dismisses common Brand24 onboarding / product update tooltips and popups."""
    selectors = [
        "button[aria-label='Close']",
        "[data-testid='close-button']",
        ".sc-gYMRRK",
        "div[class*='close']",
        "button:has-text('✕')",
        "button:has-text('Got it')",
        "button:has-text('Close')"
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=1000):
                loc.click(timeout=1000)
                print(f"[Brand24] Dismissed overlay popup ({sel}).")
        except Exception:
            pass

def crawl_brand24_excel(
    username=DEFAULT_USERNAME,
    password=DEFAULT_PASSWORD,
    project_id=DEFAULT_PROJECT_ID,
    start_date=None,
    end_date=None,
    output_dir="reports/brand24",
    headless=True
):
    """
    Automates Brand24 dashboard navigation and Excel report download using Playwright.
    Returns the absolute path to the downloaded Excel file or None.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if not start_date:
        start_date = get_target_date(days_back=1)
    if not end_date:
        end_date = start_date

    results_url = (
        f"https://app.brand24.com/panel/results/{project_id}"
        f"?p=1&or=0&cdt=days&dr=2&va=1&d1={start_date}&d2={end_date}"
    )

    print("=" * 65)
    print(f"🚀 BRAND24 AUTOMATED CRAWLER")
    print(f"📅 Target Date Range: {start_date} to {end_date}")
    print(f"🎯 Project ID:        {project_id}")
    print(f"🔗 Target Results:    {results_url}")
    print("=" * 65)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            accept_downloads=True,
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        # 1. Login flow
        print("[Step 1/4] Navigating to Brand24 Login...")
        try:
            page.goto("https://app.brand24.com/login", wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"[Brand24] Direct login navigation warning: {e}. Navigating to home page...")
            page.goto("https://brand24.com/", wait_until="domcontentloaded", timeout=45000)
            login_link = page.locator("a:has-text('Login'), a:has-text('Log in')").first
            if login_link.is_visible():
                login_link.click()

        # Fill credentials
        email_loc = page.locator("input[type='email'], input[name='email'], input[name='login']").first
        pass_loc = page.locator("input[type='password'], input[name='password']").first
        submit_loc = page.locator("button[type='submit'], input[type='submit'], button:has-text('Log in')").first

        try:
            email_loc.wait_for(state="visible", timeout=20000)
            print("[Step 1/4] Entering credentials...")
            email_loc.fill(username)
            pass_loc.fill(password)
            submit_loc.click()
        except PlaywrightTimeoutError:
            print("[Brand24] Email input not found. Checking if already logged in...")

        # Wait for authentication redirect into panel
        try:
            page.wait_for_url("**/panel**", timeout=35000)
            print("[Brand24] Authenticated successfully into dashboard.")
        except Exception:
            print(f"[Brand24] Current URL after login attempt: {page.url}")

        # 2. Navigate to target results page
        print(f"[Step 2/4] Navigating to target results URL: {results_url}...")
        page.goto(results_url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000)
        dismiss_popups(page)

        # 3. Click 'Excel report' in left sidebar
        print("[Step 3/4] Locating 'Excel report' button...")
        excel_selectors = [
            "text='Excel report'",
            "span:has-text('Excel report')",
            ".sc-gRhIYd:has-text('Excel report')",
            "a[href*='excel']",
            "button:has-text('Excel report')"
        ]

        excel_btn = None
        for sel in excel_selectors:
            loc = page.locator(sel).first
            if loc.is_visible():
                excel_btn = loc
                break

        if not excel_btn:
            # Fallback to waiting for primary selector
            excel_btn = page.locator("text='Excel report'").first
            excel_btn.wait_for(state="visible", timeout=20000)

        excel_btn.scroll_into_view_if_needed()
        excel_btn.click()
        print("[Brand24] Clicked 'Excel report'. Waiting for modal...")
        page.wait_for_timeout(3000)
        dismiss_popups(page)

        # 4. Click 'Download report' and capture download
        print("[Step 4/4] Locating 'Download report' button...")
        dl_selectors = [
            "text='Download report'",
            "div:has-text('Download report')",
            "button:has-text('Download report')",
            ".sc-jGNhvO:has-text('Download report')"
        ]

        dl_btn = None
        for sel in dl_selectors:
            loc = page.locator(sel).first
            if loc.is_visible():
                dl_btn = loc
                break

        if not dl_btn:
            dl_btn = page.locator("text='Download report'").first
            dl_btn.wait_for(state="visible", timeout=20000)

        print("[Brand24] Initiating report download...")
        with page.expect_download(timeout=60000) as dl_info:
            dl_btn.click()

        download = dl_info.value
        filename = f"toyota_report_{start_date}.xlsx"
        saved_path = os.path.abspath(os.path.join(output_dir, filename))
        download.save_as(saved_path)

        file_size = os.path.getsize(saved_path)
        print(f"[Brand24] Successfully downloaded Excel report!")
        print(f"           File: {saved_path}")
        print(f"           Size: {file_size} bytes")

        browser.close()
        return saved_path

def run_daily_task(args):
    """Coordinates download, parsing, and database synchronization with audit logging."""
    target_date = get_target_date(days_back=args.days_back, custom_date=args.date)
    start_date = args.start_date or target_date
    end_date = args.end_date or target_date
    start_time = time.time()

    excel_path = None
    try:
        # 1. Download report
        excel_path = crawl_brand24_excel(
            username=args.username,
            password=args.password,
            project_id=args.project_id,
            start_date=start_date,
            end_date=end_date,
            output_dir=args.output_dir,
            headless=not args.headed
        )

        if not excel_path or not os.path.exists(excel_path):
            duration = time.time() - start_time
            record_crawl_log(
                target_date=start_date,
                status="FAILED",
                report_file=None,
                error_message="Excel report could not be downloaded from Brand24",
                duration_sec=duration,
                campaign=args.campaign
            )
            print("[Error] Brand24 Excel report was not downloaded.")
            return False

        # 2. Parse report
        print("\n" + "=" * 65)
        print("📊 PARSING BRAND24 EXCEL REPORT")
        print("=" * 65)
        records = parse_brand24_excel(excel_path, campaign=args.campaign)
        print(f"[Parser] Extracted {len(records)} mention records.")

        duration = time.time() - start_time

        if not records:
            record_crawl_log(
                target_date=start_date,
                status="NO_MENTIONS",
                total_mentions=0,
                inserted_count=0,
                duplicate_count=0,
                report_file=excel_path,
                error_message=None,
                duration_sec=duration,
                campaign=args.campaign
            )
            print("[Brand24] No new mentions found to ingest for this time window. Logged status: NO_MENTIONS.")
            return True

        # 3. Database Upload
        if args.no_db:
            print("[DB Sync] Skipping database upload (--no-db specified).")
            record_crawl_log(
                target_date=start_date,
                status="OFFLINE_CACHE",
                total_mentions=len(records),
                inserted_count=0,
                duplicate_count=0,
                report_file=excel_path,
                error_message="Skipped DB sync (--no-db flag)",
                duration_sec=duration,
                campaign=args.campaign
            )
            return True

        print("\n" + "=" * 65)
        print("💾 SYNCHRONIZING TO DATABASE")
        print("=" * 65)
        inserted, duplicates = insert_discussions_batch(records)
        duration = time.time() - start_time

        record_crawl_log(
            target_date=start_date,
            status="SUCCESS",
            total_mentions=len(records),
            inserted_count=inserted,
            duplicate_count=duplicates,
            report_file=excel_path,
            error_message=None,
            duration_sec=duration,
            campaign=args.campaign
        )
        print(f"[DB Sync] Complete: {inserted} inserted, {duplicates} duplicates skipped.")

        # Print summary stats
        try:
            stats = get_db_stats()
            if stats:
                print("\n📈 Database Statistics:")
                for k, v in stats.items():
                    print(f"   {k}: {v}")
        except Exception:
            pass

        return True

    except Exception as e:
        duration = time.time() - start_time
        record_crawl_log(
            target_date=start_date,
            status="FAILED",
            report_file=excel_path,
            error_message=str(e),
            duration_sec=duration,
            campaign=args.campaign
        )
        print(f"[Fatal Error] Daily crawl failed for {start_date}: {e}")
        return False

def show_crawl_logs(campaign="Toyota", limit=20):
    """Displays the latest execution logs and skipped/failed days."""
    print("\n" + "=" * 65)
    print("📋 BRAND24 CRAWL & DB SYNC EXECUTION LOGS")
    print("=" * 65)
    df = get_crawl_logs(campaign=campaign, limit=limit)
    if df.empty:
        print("No crawl logs recorded yet.")
    else:
        cols_to_show = [c for c in ["target_date", "status", "total_mentions", "inserted_count", "duplicate_count", "duration_sec", "created_at"] if c in df.columns]
        print(df[cols_to_show].to_string(index=False))

def check_and_show_skipped(lookback_days=14, campaign="Toyota"):
    """Scans and reports any missing or failed days in the lookback period."""
    print("\n" + "=" * 65)
    print(f"🔍 SCANNING FOR SKIPPED OR FAILED DAYS (Last {lookback_days} days)")
    print("=" * 65)
    missing = get_missing_or_failed_days(lookback_days=lookback_days, campaign=campaign)
    if not missing:
        print(f"✅ All days in the last {lookback_days} days are accounted for! No missed crawls.")
    else:
        print(f"⚠️ Found {len(missing)} skipped or failed day(s):")
        for m in missing:
            print(f"   - Date: {m['target_date']} | Status: {m['reason']}")
        print("\n💡 Tip: You can backfill these days using: python brand24_crawler.py --backfill-skipped")
    return missing

def backfill_skipped_days(args, lookback_days=14):
    """Iterates through all missing or failed days and crawls each sequentially."""
    missing = check_and_show_skipped(lookback_days=lookback_days, campaign=args.campaign)
    if not missing:
        return True

    print("\n" + "=" * 65)
    print(f"🔄 STARTING AUTOMATIC BACKFILL FOR {len(missing)} DAY(S)")
    print("=" * 65)
    
    total_success = 0
    for idx, item in enumerate(missing, 1):
        target_d = item["target_date"]
        print(f"\n>>> [{idx}/{len(missing)}] Backfilling date: {target_d} (Reason: {item['reason']})")
        args.date = target_d
        args.start_date = target_d
        args.end_date = target_d
        ok = run_daily_task(args)
        if ok:
            total_success += 1
        time.sleep(3)

    print("\n" + "=" * 65)
    print(f"🎉 BACKFILL COMPLETE: {total_success}/{len(missing)} days successfully recovered.")
    print("=" * 65)
    return total_success == len(missing)

def main():
    parser = argparse.ArgumentParser(description="Brand24 Daily Automated Playwright Crawler & DB Ingestion")
    parser.add_argument("--date", type=str, default=None, help="Target date YYYY-MM-DD (default: yesterday in GMT+7)")
    parser.add_argument("--start-date", type=str, default=None, help="Start date YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, default=None, help="End date YYYY-MM-DD")
    parser.add_argument("--days-back", type=int, default=1, help="Number of days back (default: 1)")
    parser.add_argument("--project-id", type=str, default=DEFAULT_PROJECT_ID, help="Brand24 project ID")
    parser.add_argument("--campaign", type=str, default=DEFAULT_CAMPAIGN, help="Campaign name (default: Toyota)")
    parser.add_argument("--username", type=str, default=DEFAULT_USERNAME, help="Brand24 username/email")
    parser.add_argument("--password", type=str, default=DEFAULT_PASSWORD, help="Brand24 password")
    parser.add_argument("--output-dir", type=str, default="reports/brand24", help="Output directory for Excel files")
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode (for debugging)")
    parser.add_argument("--no-db", action="store_true", help="Skip DB ingestion")
    parser.add_argument("--logs", action="store_true", help="Display recent crawl execution logs")
    parser.add_argument("--check-skipped", action="store_true", help="Check and display any skipped or failed days")
    parser.add_argument("--backfill-skipped", action="store_true", help="Automatically crawl and backfill all skipped or failed days")
    parser.add_argument("--lookback", type=int, default=14, help="Lookback days for skipped check/backfill (default: 14)")

    args = parser.parse_args()

    if args.logs:
        show_crawl_logs(campaign=args.campaign)
        sys.exit(0)

    if args.check_skipped:
        check_and_show_skipped(lookback_days=args.lookback, campaign=args.campaign)
        sys.exit(0)

    if args.backfill_skipped:
        success = backfill_skipped_days(args, lookback_days=args.lookback)
        sys.exit(0 if success else 1)

    success = run_daily_task(args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

