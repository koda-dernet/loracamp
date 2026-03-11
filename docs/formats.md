# Supported Formats

This documents the audio and image formats that LoraCamp supports as *input* files within your model folders.

## Audio Formats (Samples)

LoraCamp uses FFmpeg to process audio samples. Any format supported by your FFmpeg installation should work, but we specifically test for:

- **WAV**
- **FLAC**
- **MP3**
- **OGG/Opus**

All audio samples are transcoded to **MP3 VBR 0** for optimized web streaming.

## Previews (Images & Video)

Previews are discovered automatically if named `preview.*` or `cover.*`.

### Image Formats

Previews are processed using the Pillow library. Supported formats:

- **JPG / JPEG**
- **PNG**
- **WebP**

By default, all image previews are optimized as `preview.jpg` (max 800px).

### Video Formats

LoraCamp supports **MP4** video previews. When an MP4 is detected:

- The video is copied to the site.
- A static "poster" image is automatically extracted from the video for the catalog view and as a fallback.
- The model page will display an interactive video player.

### Configuration

You can change the default output format for image previews in `catalog.toml` or `model.toml`:

```toml
preview_format = "webp"
```

---
