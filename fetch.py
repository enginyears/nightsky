#!/usr/bin/env python3
"""
fetch.py — Fetches @the_enginyears follower count from Instagram.

Method priority:
  1. Instagram's internal web profile JSON API  <- most reliable, no login
  2. instaloader (unauthenticated)              <- fallback #1
  3. Keep existing count + warn                 <- never write zeros

How the internal API works:
  Instagram's own website calls this endpoint to build the profile page.
  It's a public JSON endpoint — no authentication header required — but it
  does need the correct X-IG-App-ID header (the public IG web app identifier,
  visible in any browser's network tab when you visit instagram.com).
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── config ────────────────────────────────────────────────────────────────────
USERNAME    = "the_enginyears"
OUTPUT_FILE = "data.json"

# Instagram's public web app ID — baked into instagram.com's JS bundle,
# visible in any browser's network inspector on the profile page.
IG_APP_ID   = "936619743392459"

# Realistic browser headers. Instagram checks these and rejects requests
# that look obviously scripted (empty User-Agent, missing Referer, etc.)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":           "application/json, text/javascript, */*; q=0.01",
    "Accept-Language":  "en-US,en;q=0.9",
    "X-IG-App-ID":      IG_APP_ID,
    "X-Requested-With": "XMLHttpRequest",
    "Referer":          f"https://www.instagram.com/the_enginyears/",
    "Origin":           "https://www.instagram.com",
}


def get(url, headers, timeout=15):
    """Makes an HTTP GET, returns raw bytes or None on any failure."""
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if resp.info().get("Content-Encoding") == "gzip":
                import gzip
                return gzip.decompress(raw)
            return raw
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        print(f"  Connection error: {e.reason}")
    except Exception as e:
        print(f"  Unexpected: {e}")
    return None


def fetch_internal_api():
    """
    Calls Instagram's internal web_profile_info endpoint.
    This is the same endpoint instagram.com calls in your browser —
    it returns rich JSON including the follower count.
    Response shape: {"data": {"user": {"edge_followed_by": {"count": N}}}}
    """
    url = (
        f"https://www.instagram.com/api/v1/users/web_profile_info/"
        f"?username={USERNAME}"
    )
    raw = get(url, HEADERS)
    if not raw:
        return None
    try:
        data  = json.loads(raw.decode("utf-8"))
        count = data["data"]["user"]["edge_followed_by"]["count"]
        print(f"  Internal API: {count:,} followers")
        return int(count)
    except (KeyError, TypeError, ValueError) as e:
        print(f"  JSON shape unexpected: {e}")
        print(f"  Response preview: {raw[:400]}")
        return None


def fetch_instaloader():
    """Uses instaloader's public profile fetch — no login required."""
    try:
        import instaloader
        L = instaloader.Instaloader(
            quiet=True,
            download_pictures=False, download_videos=False,
            download_video_thumbnails=False, download_geotags=False,
            download_comments=False, save_metadata=False,
        )
        profile = instaloader.Profile.from_username(L.context, USERNAME)
        print(f"  instaloader: {profile.followers:,} followers")
        return profile.followers
    except Exception as e:
        print(f"  instaloader failed: {e}")
        return None


def load_existing():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"follower_count": 0}


def main():
    print(f"\n Syncing @{USERNAME}...\n")

    # Try internal API first
    print("Method 1: Instagram internal API")
    count = fetch_internal_api()

    # Fallback to instaloader
    if count is None:
        print("\nMethod 2: instaloader")
        time.sleep(3)
        count = fetch_instaloader()

    # Both failed — preserve existing file, do not write zeros
    if count is None:
        print("\nAll methods failed. Keeping existing data.json unchanged.")
        print("This is usually a temporary rate-limit on the runner IP.")
        print("The workflow will retry in 30 minutes automatically.")
        return False

    existing = load_existing()
    prev     = existing.get("follower_count", 0)
    delta    = count - prev

    if   delta > 0: print(f"\n+{delta} since last run")
    elif delta < 0: print(f"\n{delta} since last run (shooting stars!)")
    else:           print(f"\nNo change ({count:,})")

    with open(OUTPUT_FILE, "w") as f:
        json.dump({
            "username":       USERNAME,
            "follower_count": count,
            "prev_count":     prev,
            "delta":          delta,
            "fetched_at":     datetime.now(timezone.utc).isoformat(),
        }, f, indent=2)

    print(f"Saved {count:,} followers to {OUTPUT_FILE}")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
