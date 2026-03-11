# model.toml Reference

Each Model directory must contain a `model.toml` file to describe it.

## Options

### `title`
The display name of the Model.
```toml
title = "Vintage Film Look"
```

### `creator` (String) | `creators` (List)
The creator(s) of the Model. If omitted, it falls back to the catalog's creator.
```toml
creator = "PhotographyExpert"
# OR
creators = ["Alpha", "Beta"]
```

### `base_model` (Optional)
The base model architecture this Model was trained on.
```toml
base_model = "SDXL 1.0"
```

### `trigger_word` (Optional)
The trigger keyword required to activate this Model.
```toml
trigger_word = "vfilm"
```

### `version` (Optional)
The version string for this specific release.
```toml
version = "1.0.2"
```

### `sample_prompts` (Optional)
A list of recommended prompts to use with this Model.
```toml
sample_prompts = [
    "vfilm style, a portraits of a robot in the rain",
    "vfilm style, cinematic landscape of a neon city"
]
```

### `preview` (Optional)
The filename of the preview image (e.g., `preview.jpg`). If omitted, LoraCamp looks for `preview.jpg` or `cover.jpg` automatically.

### `previews` (Optional)
A list of additional preview images to show in the gallery.
```toml
previews = ["sample1.png", "sample2.png"]
```

### `release_date` (Optional)
Release date in `YYYY-MM-DD` format. Used for sorting on the homepage.
```toml
release_date = "2024-03-11"
```

### `unlisted` (Optional)
If true, the Model won't appear on the homepage but its page will still be built.
```toml
unlisted = true
```

---

## Pending Implementation (Faircamp Gaps)

The following features from Faircamp's `release.eno` are not yet implemented in LoraCamp:

| Field | Description |
| :--- | :--- |
| `download_access` | Support for `code`, `paycurtain`, or `external` access modes. |
| `downloads` | Specifying multiple ZIP formats (FLAC, MP3, etc.). |
| `extras` | Automatic bundling of non-audio files into the download ZIP. |
| `price` / `payment` | Support for currencies and payment instruction display. |
| `speed_controls` | Player toggle for playback speed. |
| `streaming_quality`| bandwidth-saving `frugal` mode. |
| `track_numbering` | Templates for numbering styles (roman, etc.). |
| `copy_link` | Toggle to disable the "Copy Link" button. |

---
*Note: This is adapted from Faircamp's release options.*
