# 🌌 @enginyears.me · Instagram Galaxy

A live night sky where every Instagram follower is a real star. The moon shows today's actual lunar phase. Lose a follower and shooting stars streak across the sky.

**Live at:** `https://enginyears.github.io/nightsky/`

---

## What you see

| Feature | Detail |
|---|---|
| 🌙 **Real moon** | Mathematically accurate phase, mare regions, craters, limb darkening, earthshine on new moon |
| ⭐ **Follower stars** | Exactly N stars = your follower count, stable seeded positions |
| 🎨 **Spectral colours** | O/B blue-white, A white, F/G yellow, K orange, M red — weighted by real stellar frequency |
| 🖱 **Star cursor** | OS cursor hidden, replaced with a twinkling 8-spike diffraction star drawn on canvas |
| 🌊 **Mouse attraction** | Follower stars drift toward the cursor when nearby, snap back instantly when it leaves |
| 🔭 **Parallax** | Background stars shift on mouse movement across three depth layers |
| 🌌 **Milky Way** | Seeded diagonal star-dust band |
| 🌿 **Aurora** | Wavy green/teal/violet bands shimmer at the horizon |
| 🌠 **Shooting stars** | Auto every 8–26 s. Lose followers? One streak per lost follower fires immediately |
| ✨ **Gain flash** | Gold `+N ✦` floats up when your count increases |
| 🕐 **Last synced** | Top-right pill shows the exact date and time of the last successful data sync in IST |

---

## File structure

```
nightsky/
├── index.html                        # The entire webpage (self-contained, no dependencies)
├── data.json                         # Written by fetch.py, read by the webpage
├── fetch.py                          # Fetches follower count from Instagram
├── requirements.txt                  # Python dependencies (instaloader)
├── README.md
└── .github/
    └── workflows/
        └── sync.yml                  # GitHub Actions — runs fetch.py every 30 min
```

---

## How the data pipeline works

```
Your home machine (residential IP)
        │
        │  self-hosted GitHub Actions runner
        │  runs fetch.py every 30 minutes
        │
        ▼
Instagram API  ──►  data.json  ──►  git commit + push
                                          │
                                          ▼
                                   GitHub Pages serves
                                   the updated file
                                          │
                                          ▼
                              Browser fetches data.json
                              every 30 min (cache: no-store)
                              and redraws the star field
```

---

## Why a self-hosted runner?

Instagram blocks all requests from cloud datacenter IPs (AWS, Azure, Cloudflare). Your local machine has a residential IP that Instagram doesn't block. The self-hosted GitHub Actions runner is just a small background service running on your home machine that lets GitHub trigger jobs on it remotely.

---

## Setup

### 1. Push to GitHub and enable Pages

Create a public repository, push all files, then go to **Settings → Pages → Source: Deploy from branch → Branch: main / (root)**. Your page will be live within a minute.

### 2. Install the self-hosted runner

In your GitHub repo go to **Settings → Actions → Runners → New self-hosted runner → Linux**.

Follow the four commands GitHub shows you. Run them on your home machine (the same machine where `python3 fetch.py` works locally). After `./run.sh` confirms it's connected, install it as a permanent service so it survives reboots:

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

The runner will now start automatically on boot and sit idle until GitHub triggers it.

### 3. Trigger the first sync

Go to **Actions → 🌌 Sync Galaxy → Run workflow**. This runs `fetch.py` on your home machine, writes `data.json` with your real follower count, commits it, and pushes. After that it runs automatically every 30 minutes.

To confirm it worked, check that `data.json` in your repo now has a non-zero `follower_count` and a recent `fetched_at` timestamp.

---

## How the webpage works

**No framework, no build step** — `index.html` is entirely self-contained vanilla JavaScript using the browser's Canvas 2D API.

### Moon rendering
The moon is drawn once to an offscreen `<canvas>` element and cached. It is only rebuilt when the lunar phase shifts by more than 0.15% (roughly every few minutes). The terminator (day/night boundary) is approximated with a cubic bezier curve using the formula `ex = R × cos(2π × phase)` to compute the ellipse semi-axis. Phase 0 = new moon, 0.5 = full moon.

### Star positions
All positions use a seeded pseudo-random number generator (mulberry32). The same seed always produces the same sequence of positions, so the star field looks identical on every page load and every browser. Adding new followers appends new stars without shifting existing ones.

### Mouse attraction physics
Each follower star carries a displacement offset `(dx, dy)` that starts at zero. Every frame:
1. If the cursor is within `ATTRACT_RADIUS` pixels, `dx/dy` is nudged toward the cursor proportional to proximity (closer = stronger pull)
2. `dx` and `dy` are multiplied by `DECAY = 0.78` — exponential decay that pulls the star back home when the cursor leaves
3. The star is drawn at `(x + dx, y + dy)`

The cursor and attraction calculations use raw mouse coordinates (`mx, my`). The parallax effect uses smoothed coordinates (`smx, smy` — lerped 4% per frame) because that lag creates a pleasing elastic feel. Anything the user *controls* gets raw values; anything that *reacts* can be smoothed.

### Cache busting
`data.json` is fetched with `{ cache: 'no-store' }` to force a real network request on every refresh, preventing GitHub Pages' CDN from serving a stale copy.

---

## Tweaking the physics

All the interesting constants are at the top of `drawLoop` in `index.html`:

| Constant | Default | Effect |
|---|---|---|
| `ATTRACT_RADIUS` | 150 | How close the cursor must be to pull a star (px) |
| `ATTRACT_FORCE` | 0.55 | How eagerly stars accelerate toward the cursor |
| `DECAY` | 0.78 | How fast displacement fades — lower = snappier return |
| `MAX_DISPLACE` | 36 | Maximum drift from home position (px) |

---

## Local development

```bash
pip3 install instaloader
python3 fetch.py          # writes data.json locally

# Must serve over HTTP — fetch() is blocked on file:// origins
python3 -m http.server 8000
# Open http://localhost:8000
```
