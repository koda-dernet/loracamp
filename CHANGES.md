# LoraCamp Code Changes

This file records significant code changes, implementations, and porting milestones.

## Phase 1: Engine Foundation & Porting (2026-03-11)

### Infrastructure & CLI
- **Entry Point**: Created `loracamp/main.py` with `argparse` for a robust CLI.
- **Build Engine**: Implemented `loracamp/engine.py` to orchestrate scanning, manifest parsing, and site generation.
- **Visible Build Paths**: Configured the engine to output to `/yoursite` and `/yourcdn` instead of hidden dot-files.
- **Dependency Management**: Initialized `pyproject.toml` and `requirements.txt` with `tomli`, `jinja2`, `babel`, and `python-ffmpeg`.

### Manifests & Logic
- **TOML Implementation**: Created `loracamp/manifests.py`. Replaced Faircamp's `.eno` format with TOML for better Python ecosystem integration.
- **Metadata Engine**: Created `loracamp/metadata.py`. Implemented SHA256 hashing for `.safetensors` files and automated `metadata.json` assembly.
- **CDN Strategy**: Created `loracamp/cdn.py`. Implemented logic to separate large binary files from static site assets.

### Frontend & Assets
- **Templates**: Set up Jinja2 environment in `loracamp/templates/`.
    - Created `base.html` for layout.
    - Created `index.html` for the catalog view.
- **CSS Port**: Migrated the reference minimalist `site.css` into `loracamp/static/css/`.
- **JS Player Assets**: Ported faircamp JS player files (`player.js`, `browser.js`, `embeds.js`, `clipboard.js`, `theming_widget.js`) into `loracamp/static/js/`.
- **Asset Consolidation**: Merged the previously split `/assets/` (JS) and `/static/` (CSS) output directories into a single `/static/` directory. Updated `assets.py`, `base.html`, and `engine.py` accordingly. The `loracamp/assets/` source directory has been removed.
- **Localization**: Created `loracamp/i18n.py` using standard Python `gettext` patterns.

## Phase 3: Feeds, Creator Pages & Filters (2026-03-11)

### Social & Discovery
- **OpenGraph Meta Tags**: Added `og:title`, `og:description`, `og:image`, `og:url`, and `twitter:card` to `base.html`. Each page injects its own values via template context.
- **RSS & Atom Feeds**: Implemented `loracamp/feeds.py`. Generates `feed.rss` (RSS 2.0) and `feed.atom` (Atom 1.0) with per-model entries including title, summary, preview image enclosure, and a `rel="related"` link to `metadata.json` for easy scraping. Feed discovery `<link>` tags added to `base.html`.
- **Creator Pages**: Created `creator.html` template and added engine logic to render a dedicated page per creator directory.

### CLI & Filtering
- **Path Filters**: Added `--include PATTERN` and `--exclude PATTERN` flags to `main.py`. Multiple flags can be stacked. Logic passed through to `LoraCampEngine`.
- **Filter Bug Fix**: The `os.walk` filter previously used `continue` which does not prune subdirectories and matched against absolute paths (incorrectly skipping the catalog root). Fixed to use `dirs[:] = []` for proper subtree pruning and to match against the *relative* path from the catalog root, so the root is always visited regardless of filter patterns.

### Media
- **GIF Preview Support**: Engine now detects `.gif` files as valid previews and passes them through without transcoding (unlike JPEG/PNG which go through Pillow optimization).

### i18n / Translations
- **Dropped Server-side i18n**: Removed `i18n.py`, `gettext` dependency, and `locales/` JSON files. Static sites can't serve per-request translations; multi-build pipelines add complexity for marginal gain.
- **Browser-native Translation**: `base.html` includes `lang="en"` so browsers auto-detect the source language, plus a 🌐 Translate footer link that opens Google Translate pre-loaded with the current page URL.

### Audio Transcoding
- **Opus-Only Output**: Changed default audio transcoding from MP3 VBR 0 to Opus at 96kbps. This significantly reduces file size and bandwidth for previews. The legacy dual-format MP3 fallback (from `faircamp`) was dropped as Opus enjoys 98%+ global browser support today.

### Organizational Features
- **Creator Aliases**: Added `aliases` array support to `creator.toml`. Models assigned to an alias are properly routed and displayed under the canonical creator name, grouping uncredited/anonymous drops effectively.
- **External Redirects**: Models or Creators can now specify `external_page = "https://..."` in their `[links]` table. Accessing their local LoraCamp URL automatically serves a lightweight HTML refresh redirect to the external site, handy for off-site portfolios or HuggingFace repos.
- **Manifests Porting Complete**: Successfully migrated the core Faircamp `.eno` property reference into standard TOML for `catalog.toml`, `creator.toml`, and `model.toml`. Dropped DJ and commerce specific fields in favor of a streamlined AI model showcase.rofile.

---

## Phase 2: Media & Metadata Enhancement (2026-03-11)

### Media Processing
- **Audio Transcoding**: Implemented `loracamp/media.py` using `python-ffmpegio` for a cleaner API, removing raw `subprocess` overhead while still leveraging `static-ffmpeg` for zero-config binaries.
- **Duration Extraction**: Added `ffprobe` integration to extract audio duration for the player.
- **Image Optimization**: Integrated `Pillow` to automatically resize and optimize Lora previews to `preview.jpg`.

### Site Structure & Features
- **Lora Detail Pages**: Implemented `lora.html` template and engine logic to generate individual model pages.
- **Slug-Based CDN**: Refined the CDN strategy to mirror the site's slug structure (`/yourcdn/SLUG/` matches `/yoursite/SLUG/`).
- **Sample Discovery**: Automated the scanning of model folders for audio assets and linking them to the site.
- **Manifest Gap Analysis**: Conducted a comprehensive audit of all Faircamp manifest types (`artist`, `catalog`, `release`, `track`) identifying over 20 unported features (distribution, commerce, social, and anti-hotlinking) and documented them in `porting_log.md` and the internal reference guides.

### Software Identity & Branding
- **LoraCamp Branding**: Reverted core engine class to `LoraCampEngine` to preserve the software's brand identity while maintaining "Model" and "Creator" as domain-specific terminology for manifests and data.
- **AGENTS.md Guidelines**: Updated project rules to prioritize `uv` and `static-ffmpeg`/`python-ffmpegio`.

### Validation & Reliability
- **TOML Validation**: Integrated `tomlval` to perform schema validation on all manifests (`catalog.toml`, `creator.toml`, `model.toml`, `sample.toml`) before the build starts.
- **Distribution Features**: Implemented ZIP bundling for models and individual file download links (safetensors, metadata, extras).
- **Automatic Discovery**: Added logic to automatically detect and include "extra" files (documentation, etc.) in model bundles.
- **Manifest Discovery**: Added support for `creator.toml` and per-sample manifest files.
- **Rules Disclosure**: Updated `AGENTS.md` with explicit guidelines on this distinction.

### Dependencies
- Added `Pillow` for image processing.
- Added `python-ffmpegio` for higher-level media control.
- Added `static-ffmpeg` for bundled binaries.
