# LoraCamp Porting Progress

This file tracks the current state of the port from Faircamp (Rust) to LoraCamp (Python).

## Current Status: Phase 3 (Feeds, Creator Pages & Filters)

- [x] **Project Structure**: Renamed to LoraCamp, absolute Python-only requirement.
- [x] **Manifests**: Successfully switched from `.eno` to **TOML**. Parsing models implemented.
- [x] **Metadata**: Automatic **SHA256** hash generation and `metadata.json` bundling implemented.
- [x] **CDN Split**: Logic for `/yoursite` and `/yourcdn` separation implemented.
- [x] **i18n**: Dropped in favor of native browser translation; `base.html` includes `lang="en"` and a 🌐 Translate footer link.
- [x] **Templating**: **Jinja2** environment initialized with base layout and index.
- [x] **Assets**: CSS and JS player assets ported from reference; consolidated into a single `/static/` directory.
- [x] **CLI**: `main.py` entry point with `--build` and `--cdn-url` support.

## Feature Roadmap

### High Priority

- [x] **FFmpeg Transcoding**: Implement audio sample processing using `python-ffmpegio`.
- [x] **Model Detail Pages**: Render individual pages for each model folder.
- [ ] **Safetensor Extractions**: *(DEFERRED)* Extract technical metadata from `.safetensors` headers as a fallback (e.g., discovering `base_model` or `trigger_word` if the user omitted them from `model.toml`). Use as a safety net rather than a primary source.
- [x] **GIF Preview Support**: Engine handles `.gif` as pass-through preview (no transcoding needed).
- [x] **Individual Downloads Interface**: Replaced legacy ZIP bundling with a multi-file Javascript downloader (Download All) to save disk space and compute overhead per the LoraCamp paradigm.
- **Manifests Porting**: Fully mapped the core Faircamp `.eno` property model to TOML (`catalog.toml`, `creator.toml`, `model.toml`) in `manifests.py`. Dropped/deferred commerce and DJ-specific fields.
- [x] **Creator Pages**: `creator.html` template + engine logic for per-creator pages.
- [x] **OpenGraph Meta Tags**: Injected into `base.html` for social sharing (og:title, og:description, og:image, og:url, Twitter card).
- [x] **RSS/Atom Feeds**: `feeds.py` generates `feed.rss` and `feed.atom` with model entries, metadata.json links, and preview enclosures.
- [x] **CLI Path Filters**: `--include` / `--exclude` pattern args added to `main.py`.
- [x] **Manual Porting**: Ported all 10 topics and 4 reference pages from reference manual.
  - [x] Update `porting_log.md` with comprehensive gap list
  - [x] Update `docs/ref-catalog.md`
  - [x] Update `docs/ref-creator.md`
  - [x] Update `docs/ref-model.md`
  - [x] Update `docs/ref-sample.md`
- [x] **GenAI Metadata**: Added support for advanced sample metadata (CFG, Sampler, LLM settings, Audio params).
- [x] **TOML Validation**: Integrated `tomlval` to validate all manifests before building.

### Medium Priority

- [ ] **Vibrant Design**: Rewrite CSS to move away from minimalist look to "premium/vibrant" aesthetic.
- [ ] **Image Lora Support**: Handle image samples and galleries (currently focusing on audio).
- [x] **Catalog Feeds**: `feeds.py` generates RSS 2.0 and Atom 1.0 feeds.
- [ ] **Commerce Features**: Port `release_price`, `paycurtain`, and external purchase links.
- [x] **Distribution Features**: Port `release_downloads` (ZIP formats) and `release_extras`.
- [ ] **Anti-Hotlinking**: Port `freeze_download_urls` and randomized path logic.

### Long Term

- [ ] **Search/Filter**: Client-side search for large catalogs.
- [ ] **Theme Customization**: TOML-based theme overrides.

## Technical Decisions

- **Language**: Python 3.10+
- **Manifest Format**: TOML
- **Media Engine**: FFmpeg (`python-ffmpegio` + `static-ffmpeg`)
- **Templates**: Jinja2
- **Localization**: Babel / gettext
- **Build Output**: `/yoursite` (HTML/CSS) and `/yourcdn` (Models/Samples)

## Dropped Functionality

- **Live Preview Server**: Dropped in favor of simple filesystem browsing of `/yoursite/index.html`.
- **Server-side i18n / Multi-language builds**: Dropped; native browser translation (Google Translate, DeepL, browser extensions) provides better coverage with zero maintenance. HTML `lang` attribute and a footer Translate link are provided instead.
- **Dual-Format Audio Streams (Opus + MP3)**: Dropped in favor of Opus-only (96kbps). 98%+ of modern browsers support Opus natively, making the complex MP3 fallback logic and dual-storage requirements unnecessary for simple previews.
- **Embedding Widgets (IFrames)**: Dropped, as sharing Lora previews is generally done via direct URLs rather than embedding music players on third-party sites.
- **Granular Tagging**: Dropped (Topic 09). Lora audio previews aren't intended to be imported into DJ libraries like Faircamp's MP3s. Basic Title/Artist injection during Opus transcode is sufficient.
- **M3U Playlists**: Dropped. Lora audio previews aren't meant to be consumed as a continuous album or a site-wide radio playlist.
- **Waveforms & Speed Controls**: Dropped. Visual audio waveforms and playback speed controls are unnecessary complexity for short model preview samples.

---
*Last Updated: 2026-03-11 (Dropped i18n)*
