#!/usr/bin/env python3
"""
fetch.py — Fetch @the_enginyears follower COUNT from Instagram (public profile).

Best method: instaloader without authentication.
For a PUBLIC Instagram account the follower count is freely accessible — 
no login session required. This keeps the GitHub secret simpler and avoids 
session expiry issues.

Fallback: direct HTTP scrape of the profile page.
"""

import json, os, re, sys, time
from datetime import datetime, timezone

# ── config ────────────────────────────────────────────────────────────────────
USERNAME    = "the_enginyears"
OUTPUT_FILE = "data.json"

# ── attempt 1: instaloader (no login) ─────────────────────────────────────────
def fetch_instaloader() -> int | None:
    try:
        import instaloader
        L = instaloader.Instaloader(quiet=True,
            download_pictures=False, download_videos=False,
            download_video_thumbnails=False, download_geotags=False,
            download_comments=False, save_metadata=False)
        profile = instaloader.Profile.from_username(L.context, USERNAME)
        return profile.followers
    except Exception as e:
        print(f"  instaloader failed: {e}")
        return None

# ── attempt 2: HTTP scrape ─────────────────────────────────────────────────────
def fetch_scrape() -> int | None:
    try:
        import urllib.request
        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/124.0.0.0 Safari/537.36")
        req = urllib.request.Request(
            f"https://www.instagram.com/{USERNAME}/",
            headers={"User-Agent": ua, "Accept-Language": "en-US,en;q=0.9"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")

        # Instagram embeds JSON-LD data in the page
        patterns = [
            r'"edge_followed_by":\{"count":(\d+)\}',
            r'"follower_count":(\d+)',
            r'"followers":(\d+)',
        ]
        for pat in patterns:
            m = re.search(pat, html)
            if m:
                return int(m.group(1))
        print("  Scrape: no pattern matched")
    except Exception as e:
        print(f"  Scrape failed: {e}")
    return None

# ── load existing data ─────────────────────────────────────────────────────────
def load_existing() -> dict:
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"follower_count": 0}

# ── main ───────────────────────────────────────────────────────────────────────
def main() -> bool:
    print(f"Fetching follower count for @{USERNAME}…")

    count = None

    print("  → trying instaloader…")
    count = fetch_instaloader()

    if count is None:
        print("  → trying HTTP scrape…")
        time.sleep(2)
        count = fetch_scrape()

    if count is None:
        print("❌  All methods failed. Keeping previous count.")
        # Don't overwrite existing file with bad data
        return False

    print(f"✅  Follower count: {count:,}")

    existing = load_existing()
    prev     = existing.get("follower_count", 0)
    delta    = count - prev

    if delta > 0:
        print(f"  📈  +{delta} since last run")
    elif delta < 0:
        print(f"  📉  {delta} since last run (shooting stars incoming!)")
    else:
        print("  ↔  No change")

    data = {
        "username":       USERNAME,
        "follower_count": count,
        "prev_count":     prev,
        "delta":          delta,
        "fetched_at":     datetime.now(timezone.utc).isoformat(),
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"💾  Saved → {OUTPUT_FILE}")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
