# 🌌 @the_enginyears · Instagram Galaxy

A live sky visualization where **every Instagram follower is a real star** — spectral colour, individual twinkle, depth parallax. The moon shows today's actual lunar phase. Lose a follower? Shooting stars streak across the sky.

**Live at:** `https://enginyears.github.io/nightsky/`

---

## What you see

| Feature | Detail |
|---|---|
| 🌙 **Real moon phase** | Mathematically accurate terminator shadow, mare regions, craters, limb darkening |
| ⭐ **Follower stars** | Exactly N stars = your follower count, seeded positions stay stable between refreshes |
| 🌈 **Spectral colours** | Stars are O/B/A/F/G/K/M class — rare hot blue stars, common yellow G-types, red dwarfs |
| 🌠 **Shooting stars** | Auto every 8–26 seconds. Lose followers? One streak per lost follower fires immediately |
| ✨ **Golden shimmer** | Warm radial glow sweeps the sky when your count increases |
| 🌌 **Milky Way band** | Diagonal star-dust smear across the canvas |
| 🌿 **Aurora borealis** | Subtle wavy green/teal/violet bands shimmer at the horizon |
| 🖱 **Parallax** | Star layers shift on mouse movement — three depth planes |
| ⏱ **Auto-refresh** | Data reloads every 30 min, countdown visible top-right |

---

## Setup (10 minutes)

### 1. Create a public GitHub repo & push all files

Push this entire folder to a new public repo on GitHub.

```
your-repo/
├── index.html
├── fetch.py
├── data.json
├── requirements.txt
├── README.md
└── .github/
    └── workflows/
        └── sync.yml
```

### 2. Enable GitHub Pages

**Settings → Pages → Source: Deploy from branch → Branch: main / (root)**

Your page will be live within ~60 seconds at:
`https://<username>.github.io/<repo>/`

### 3. Run the first sync

Go to **Actions → 🌌 Sync Galaxy → Run workflow**.

This fetches your follower count from Instagram (no login needed — public profile), writes `data.json`, and commits it back to the repo. GitHub Pages then serves it.

After this, the workflow runs every 30 minutes automatically.

---

## How it fetches follower count (no login needed)

The script (`fetch.py`) uses **instaloader** in unauthenticated mode to read the public follower count. Instagram makes this available for public profiles without requiring a session.

If instaloader is blocked, it falls back to a direct HTTP scrape of the Instagram page.

---

## Local preview

```bash
pip install instaloader
python fetch.py            # generates data.json
python -m http.server 8000 # open http://localhost:8000
```

> Note: open via a local server (not `file://`) because `fetch()` is blocked on `file://` origins.

---

## Notes

- GitHub's scheduled cron has a minimum interval of **5 minutes** and may run a few minutes late on free plans — 30 min is reliable.
- The star positions are seeded from a fixed random seed, not from follower data, so the sky looks consistent between refreshes.
- For accounts with 10,000+ followers the canvas renders all stars efficiently using Canvas2D batching.
