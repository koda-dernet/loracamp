# LoraCamp Porting Log

This log tracks functionality from the reference `faircamp` implementation and its status in the `loracamp` port.

## Documentation & Non-Code Assets

| Item | Reference Path | Status | Notes |
| :--- | :--- | :--- | :--- |
| Manual | `manual/` | [x] Ported | All 10 topics and 4 reference pages ported and adapted. |
| CSS Assets | `src/assets/` | [x] Ported | Referenced `site.css` ported; aesthetics improvement is a future goal. |
| JS Assets | `src/assets/` | [x] Ported | JS player files (`player.js`, `browser.js`, etc.) ported into `loracamp/static/js/`. All assets consolidated under `/static/`. |
| HTML Templates | `src/render/` | [x] Ported | Jinja2 templates (`base.html`, `index.html`) renamed and updated. |
| Manifests | `N/A` | [x] Implemented | Using **TOML**; Model/Creator models and parsing logic in `manifests.py`. |
| Translations | `translations/src/` | [x] Dropped | Deferred to native browser translation (Google Translate, DeepL, etc.). `base.html` includes `lang="en"` and a footer 🌐 Translate link. |
| **All Manifests**| `manual/reference/` | [x] Implemented | Core fields ported to TOML; niche audio/commerce distribution fields intentionally dropped or marked pending. |

## Core Functionality

| Functionality | Status | Adaptation Strategy |
| :--- | :--- | :--- |
| Static Site Generation | [x] Implemented | Python engine (`engine.py`) and Jinja2. |
| Media Transcoding | [x] Implemented | Integrated `static-ffmpeg` for zero-config transcoding. |
| "Live Site" Preview | [X] Dropped | Dropped as requested. |
| Audio/Image Metadata | [x] Ported | Extract standard ID3 tags and ComfyUI prompts from MP3s, and Safetensor metadata. |
| Folder-as-Model      | [x] Implemented | `LoraCampEngine` handles model discovery and processing. |
| **CDN Splitting** (NEW) | [x] Implemented | Logic in `cdn.py` handles `/yoursite` and `/yourcdn` paths. |
| **Metadata Generation** (NEW)| [x] Implemented | `metadata.py` handles SHA256 and JSON assembly. |
| **GIF Preview** (NEW) | [x] Implemented | Engine passes `.gif` previews through without transcoding. |
| **Creator Pages** (NEW) | [x] Implemented | `creator.html` template + engine logic for per-creator pages. |
| **OpenGraph Tags** (NEW) | [x] Implemented | `base.html` includes og:title/description/image/url, Twitter card. |
| **RSS/Atom Feeds** (NEW) | [x] Implemented | `feeds.py` generates `feed.rss` and `feed.atom`. |
| Path Filtering       | [x] Implemented | `--include` / `--exclude` in `main.py`; needs wiring into engine scan. |
| Local Browsability   | [x] Implemented | Explicit `index.html` URLs are now the default. |
| Image/Audio Formats  | [x] Implemented | Python wrapper for FFmpeg and Pillow (Topic 06). |
| Granular Tagging     | [x] Dropped | Irrelevant for Lora previews. Transcoder simply injects Title and Artist attributes. Left `TODO(Tagging)` in `media.py` if we ever need to expand Opus/Vorbis tags. |
| Multi-format Stream | [x] Dropped | Opted for Opus-only output (96kbps). MP3 fallback dropped, as 98%+ of modern browsers support Opus natively and samples are meant to be small previews. |
| Creator/Model Aliases| [x] Implemented | Ported alias name matching via `creator.toml` `aliases` list. |
| External Linking     | [x] Implemented | Ported `external_page` to generate redirect links for external models/creators. |
| Download Codes       | [ ] Pending | Port `download_code(s)` and `unlock_info` (Sample Ref). |
| Embedding Widgets    | [x] Dropped | Irrelevant for LoraCamp; Lora previews are shared via URLs, not embedded in generic iframes like music players. |

## Manifest Feature Gaps (Unported from Faircamp)

| Feature Area | Missing Fields / Logic | Notes |
| :--- | :--- | :--- |
| **Catalog** | `None` | `multiplecreators_mode` (formerly label_mode) implemented, updating the index page to group by creator automatically. |
| **Creator** | `None` | Alias, external_page, and `rel="me"` now implemented. `m3u` dropped. |
| **Model**   | `extras` (release_extras) | [x] Implemented. `extras` files included. ZIP bundling was dropped entirely to save space and compute; individual downloads + JS sequential downloads are used instead. |
| **Sample**  | `sample_extras`, `preview` (per-sample) | [x] Implemented. `sample_extras` handles different epochs/files per prompt. Download logic switched to direct UI links instead of ZIPs. |
| **Player/UI** | `copy_link` | `streaming_quality`, `waveforms`, and `speed_controls` dropped as unnecessary. `copy_link` pending (must generate links matching `linking.md` specs). |
| **Low Priority**| `cache_optimization`, `rotate_download_urls`, `release_downloads`, `release_price`, `paycurtain`, `track_downloads` | Commerce, ZIP bundling, and cache rebuild ops are moved to low priority as they don't block core Lora sharing. |
| **Processing**| `None` | Audio volume normalization (`loudnorm`) is now implemented directly in the Opus transcode pipeline. |

## Items of Interest / Flags
- **[FLAG]** Safetensors-as-attachments: Port reference "attachments" logic to handle `.safetensors`.
- **[FLAG]** Jinja2 is the chosen templating engine for its ease of use and standard status.
- **[FLAG]** TOML is the chosen manifest format.
