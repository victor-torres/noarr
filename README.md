# noarr

Hard-link your torrent downloads into a clean media library. No automation, no database, no arr stack — just you, a YAML file, and hard links.

[![CI](https://github.com/victor-torres/noarr/actions/workflows/ci.yml/badge.svg)](https://github.com/victor-torres/noarr/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## The idea

Tools like Radarr and Sonarr are powerful but they take over your library. They monitor, rename, re-download, and manage your files automatically — which is great until they do something you didn't want.

noarr takes the opposite approach: **you decide what to download, you decide when it's ready, and you run the script.** It finds the files in your completed downloads folder and creates hard links in a clean directory structure that Plex, Jellyfin, or Emby can read.

Hard links mean the file exists in two places with zero extra disk usage. Delete either one and the data is safe — no copies, no wasted space.

---

## How it works

```
DOWNLOADS_DIR/
└── Some.Movie.2020.2160p.WEB-DL.x265/
    ├── Some.Movie.2020.2160p.WEB-DL.x265.mkv
    └── Some.Movie.2020.2160p.WEB-DL.x265.srt

          ↓  noarr  ↓

BASE_DIR/
└── Movies/
    └── Some Movie (2020)/
        ├── Some Movie (2020).mkv
        └── Some Movie (2020).srt
```

TV shows are organized by season:

```
BASE_DIR/
└── TV Shows/
    └── Some Show (2021)/
        └── Season 01/
            ├── Some Show (2021) S01E01.mkv
            └── Some Show (2021) S01E02.mkv
```

---

## Setup

```bash
git clone https://github.com/victor-torres/noarr.git
cd noarr
pip install -r requirements.txt
cp library.example.yaml library.yaml
```

Edit `library.yaml` with your own entries (see below). Your `library.yaml` is gitignored — it stays private.

---

## Usage

```bash
DOWNLOADS_DIR=/path/to/completed BASE_DIR=/path/to/media python3 create_links.py
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview what would be linked without touching anything |
| `--force` | Overwrite existing links |

---

## library.yaml

```yaml
movies:
  - title: "Some Movie (2020)"
    path: "Some.Movie.2020.2160p.WEB-DL.x265"
    magnet: "magnet:?xt=urn:btih:..."   # optional — for re-downloading if lost

tv_shows:
  - title: "Some Show (2021)"
    path: "Some.Show.S01.COMPLETE.1080p.WEB-DL"
  - title: "Some Show (2021)"
    path: "Some.Show.S02.COMPLETE.1080p.WEB-DL"
    skip_subtitles: true                # optional — skip .srt files
```

- **`title`** — the clean name used for the destination folder and filename
- **`path`** — the folder or file name inside `DOWNLOADS_DIR`
- **`magnet`** *(optional)* — stored for reference; useful if you need to re-download a corrupted file
- **`skip_subtitles`** *(optional)* — skips `.srt` files, useful when subtitles are embedded or unwanted

See [`library.example.yaml`](library.example.yaml) for a full example.

---

## Environment variables

| Variable | Description |
|----------|-------------|
| `DOWNLOADS_DIR` | Path to your completed torrent downloads |
| `BASE_DIR` | Root of your media library |

---

## Running tests

```bash
pip install -r requirements.txt
pytest
```

---

## License

MIT
