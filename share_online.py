import os
import sys
import subprocess
import urllib.request
import re
import time

CLOUDFLARED_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
EXE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloudflared.exe")

def ensure_cloudflared():
    if not os.path.exists(EXE_PATH):
        print("Downloading Cloudflare Tunnel (100% Free HTTPS sharing, one-time download)...")
        urllib.request.urlretrieve(CLOUDFLARED_URL, EXE_PATH)
        print("Cloudflared downloaded successfully.")

def run_tunnel(port=8501):
    ensure_cloudflared()
    print(f"\nCreating secure public HTTPS link for localhost:{port}...")
    proc = subprocess.Popen(
        [EXE_PATH, "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )

    tunnel_url = None
    # Read stderr where cloudflared outputs the URL
    for _ in range(30):
        line = proc.stderr.readline()
        if not line:
            time.sleep(0.5)
            continue
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            tunnel_url = match.group(0)
            break
            
    if tunnel_url:
        print("\n" + "="*60)
        print("  🚀 YOUR DASHBOARD IS LIVE ONLINE!")
        print("="*60)
        print(f"\n  👉 Public HTTPS URL:  {tunnel_url}")
        print("\n  Share this URL with your team or open it on your phone!")
        print("  (Press Ctrl+C to stop sharing)")
        print("="*60 + "\n")
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            print("\nTunnel stopped.")
    else:
        print("Could not retrieve tunnel URL. Cloudflared process exited.")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8501
    run_tunnel(port)
