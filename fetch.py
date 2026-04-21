#!/usr/bin/env python3
"""
fetch.py — Get @the_enginyears follower count via Cloudflare Worker proxy.

Why the proxy? GitHub Actions runs on AWS/Azure IP ranges that Instagram
blocks. The Cloudflare Worker sits on Cloudflare edge IPs which aren't blocked.

Setup:
  1. Deploy cloudflare-worker.js (instructions inside that file, ~5 min)
  2. Add the worker URL as a GitHub Secret named WORKER_URL
     (Settings → Secrets and variables → Actions → New repository secret)
     Value: https://your-worker.your-name.workers.dev

The script tries three methods in order:
  1. Cloudflare Worker  (works on GitHub Actions — preferred)
  2. Direct Instagram API  (works locally, blocked on Actions)
  3. instaloader  (last resort)
"""
import json
import urllib.request
from datetime import datetime, timezone

url = "https://nightsky.enginyears.workers.dev/"
output_file = "data.json"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Load existing data if it exists
def load_existing():
    try:
        with open(output_file) as f:
            return json.load(f)
    except:
        return {"follower_count": 0}

# Fetch new data
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read())
    follower_count = data["follower_count"]
    print(follower_count)

# Compare with previous
existing = load_existing()
prev = existing.get("follower_count", 0)
delta = follower_count - prev

# Save
with open(output_file, "w") as f:
    json.dump({
        "follower_count": follower_count,
        "prev_count": prev,
        "delta": delta,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }, f, indent=2)

print(f"Saved → {output_file}")
