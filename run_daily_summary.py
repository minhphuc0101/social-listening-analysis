import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ai_scanner import run_48h_scan

if __name__ == "__main__":
    print("Executing Daily 48H Social Media Scan...")
    run_48h_scan()
    print("Done! Daily report updated.")
