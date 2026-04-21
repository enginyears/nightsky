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

import json, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone

USERNAME    = "the_enginyears"
OUTPUT_FILE = "data.json"
IG_APP_ID   = "936619743392459"  # Public IG web app ID

# GitHub Actions passes this from the WORKER_URL secret
WORKER_URL = os.environ.get("WORKER_URL", "").strip().rstrip("/")


def get(url, headers=None, timeout=20):
    """HTTP GET → bytes, or None on failure."""
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            if r.info().get("Content-Encoding") == "gzip":
                import gzip; return gzip.decompress(raw)
            return raw
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        print(f"  URL error: {e.reason}")
    except Exception as e:
        print(f"  Error: {e}")
    return None


def fetch_worker():
    """Call our Cloudflare Worker proxy — works from any IP."""
    if not WORKER_URL:
        print("  WORKER_URL secret not set — skipping.")
        return None
    url = f"{WORKER_URL}/?username={USERNAME}"
    print(f"  Calling: {url}")
    raw = get(url)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if data.get("ok"):
            count = data["follower_count"]
            print(f"  Worker returned: {count:,}")
            return int(count)
        print(f"  Worker error: {data.get('error')}")
    except Exception as e:
        print(f"  Worker response parse error: {e}")
    return None


def fetch_direct_api():
    """Call Instagram's internal API directly — blocked on GitHub Actions."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept":           "application/json, */*; q=0.1",
        "Accept-Language":  "en-US,en;q=0.9",
        "X-IG-App-ID":      IG_APP_ID,
        "X-Requested-With": "XMLHttpRequest",
        "Referer":          f"https://www.instagram.com/{USERNAME}/",
        "Origin":           "https://www.instagram.com",
    }
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={USERNAME}"
    raw = get(url, headers)
    if not raw:
        return None
    try:
        data  = json.loads(raw)
        count = data["data"]["user"]["edge_followed_by"]["count"]
        print(f"  Direct API returned: {count:,}")
        return int(count)
    except (KeyError, TypeError, ValueError) as e:
        print(f"  Direct API parse error: {e}")
        print(f"  Response preview: {(raw or b'')[:300]}")
    return None


def fetch_instaloader():
    """instaloader fallback — no login needed for public profile."""
    try:
        import instaloader
        L = instaloader.Instaloader(
            quiet=True,
            download_pictures=False, download_videos=False,
            download_video_thumbnails=False, download_geotags=False,
            download_comments=False, save_metadata=False,
        )
        p = instaloader.Profile.from_username(L.context, USERNAME)
        print(f"  instaloader returned: {p.followers:,}")
        return p.followers
    except Exception as e:
        print(f"  instaloader error: {e}")
    return None


def load_existing():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE) as f: return json.load(f)
        except Exception: pass
    return {"follower_count": 0}


def main():
    print(f"\nSyncing @{USERNAME}...\n")

    count = None

    print("Method 1: Cloudflare Worker")
    count = fetch_worker()

    if count is None:
        print("\nMethod 2: Direct Instagram API")
        time.sleep(2)
        count = fetch_direct_api()

    if count is None:
        print("\nMethod 3: instaloader")
        time.sleep(2)
        count = fetch_instaloader()

    if count is None:
        print("\nAll methods failed — data.json left unchanged.")
        print("→ Make sure you deployed the Cloudflare Worker and added WORKER_URL secret.")
        return False

    existing = load_existing()
    prev     = existing.get("follower_count", 0)
    delta    = count - prev

    if   delta > 0: print(f"\n+{delta} since last run ({prev} → {count})")
    elif delta < 0: print(f"\n{delta} since last run ({prev} → {count}) — shooting stars!")
    else:           print(f"\nNo change ({count:,})")

    with open(OUTPUT_FILE, "w") as f:
        json.dump({
            "username":       USERNAME,
            "follower_count": count,
            "prev_count":     prev,
            "delta":          delta,
            "fetched_at":     datetime.now(timezone.utc).isoformat(),
        }, f, indent=2)

    print(f"Saved → {OUTPUT_FILE}")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
