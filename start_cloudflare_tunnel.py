"""
=============================================================================
SENTINEL — Gujarat Police Command & Intelligence Platform
Option B: Cloudflare Zero-Trust Tunnel Launcher (100% Free • 0 Config)
=============================================================================
Connects your local or Google Colab FastAPI GPU backend directly to the web
using Cloudflare Tunnel without port forwarding, DNS records, or credit cards.
"""

import os
import sys
import platform
import urllib.request
import subprocess
import re
import time
import shutil

CLOUDFLARED_URLS = {
    "Windows": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe",
    "Linux": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
    "Darwin": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64"
}

def get_binary_name():
    system = platform.system()
    if system == "Windows":
        return "cloudflared.exe"
    return "./cloudflared"

def ensure_cloudflared():
    system = platform.system()
    bin_name = get_binary_name()

    # Check if already installed in system PATH
    system_bin = shutil.which("cloudflared")
    if system_bin:
        print(f"[+] Found system cloudflared: {system_bin}")
        return system_bin

    # Check local directory
    if os.path.exists(bin_name):
        print(f"[+] Found local binary: {bin_name}")
        return bin_name

    download_url = CLOUDFLARED_URLS.get(system)
    if not download_url:
        print(f"[-] Unsupported OS: {system}. Please install cloudflared manually.")
        sys.exit(1)

    print(f"[*] Downloading cloudflared binary for {system}...")
    try:
        urllib.request.urlretrieve(download_url, bin_name)
        if system != "Windows":
            os.chmod(bin_name, 0o755)
        print(f"[+] Successfully downloaded {bin_name}")
        return bin_name
    except Exception as e:
        print(f"[-] Download failed: {e}")
        print(f"[*] You can manually download from: {download_url}")
        sys.exit(1)

def run_tunnel(port=8000):
    bin_path = ensure_cloudflared()
    print("\n" + "=" * 75)
    print("  GUJARAT POLICE SENTINEL — CLOUDFLARE ZERO-TRUST TUNNEL")
    print(f"  Forwarding local backend on port {port} to public HTTPS")
    print("=" * 75 + "\n")

    cmd = [bin_path, "tunnel", "--url", f"http://127.0.0.1:{port}"]
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    tunnel_url = None
    pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    # Read stderr where cloudflared logs connection information
    try:
        for line in proc.stderr:
            sys.stdout.write(f"  [cloudflared] {line}")
            sys.stdout.flush()
            match = pattern.search(line)
            if match and not tunnel_url:
                tunnel_url = match.group(0)
                print("\n" + "#" * 75)
                print("  🚀 SENTINEL PUBLIC API & STREAM TUNNEL IS NOW ONLINE!")
                print(f"  🔗 CLOUDFLARE TUNNEL URL:  {tunnel_url}")
                print(f"  👉 VERCEL CONFIGURATION:   Open your Vercel site and enter this URL")
                print(f"                             in the 'Cloud GPU' header modal.")
                print(f"  📡 HEALTH ENDPOINT:        {tunnel_url}/health")
                print(f"  📚 API DOCUMENTATION:      {tunnel_url}/docs")
                print("#" * 75 + "\n")

        proc.wait()
    except KeyboardInterrupt:
        print("\n[*] Stopping Cloudflare tunnel...")
        proc.terminate()
        proc.wait()
        print("[+] Tunnel closed cleanly.")

if __name__ == "__main__":
    target_port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_tunnel(port=target_port)
