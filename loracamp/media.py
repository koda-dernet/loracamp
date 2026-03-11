from static_ffmpeg import add_paths
import ffmpegio
from pathlib import Path
from typing import Optional, Any

# Add ffmpeg/ffprobe to the PATH automatically
add_paths()

def transcode_audio(
    input_path: Path, 
    output_path: Path, 
    title: Optional[str] = None,
    creator: Optional[str] = None
) -> bool:
    """
    Transcode an audio file to Opus at 96kbps.
    Adds basic metadata tags.
    """
    options = {
        "codec:a": "libopus",
        "b:a": "96k", # High quality for Opus
        "vbr": "on",
        "map_metadata": "-1", # Start clean
        "af": "loudnorm=I=-16:LRA=11:TP=-1.5" # Web standard EBU R128 normalization
    }
    
    metadata = []
    if title:
        metadata.append(f"title={title}")
    if creator:
        metadata.append(f"artist={creator}")
        
    # TODO(Tagging): If "Granular Tagging" (custom ID3/Vorbis routing) is ever needed,
    # expand the `metadata` list here. Opus/Vorbis comments support arbitrary
    # KEY=VALUE pairs (e.g., LORA_CREATOR=..., TRIGGER_WORD=...).
        
    try:
        if metadata:
            ffmpegio.transcode(str(input_path), str(output_path), overwrite=True, **options, metadata=metadata)
        else:
            ffmpegio.transcode(str(input_path), str(output_path), overwrite=True, **options)
        return True
    except Exception as e:
        print(f"Transcoding error: {e}")
        return False

def get_audio_duration(file_path: Path) -> Optional[float]:
    """Get the duration of an audio file using ffmpegio probe."""
    try:
        info = ffmpegio.probe.full_details(str(file_path))
        return float(info["format"]["duration"])
    except Exception as e:
        print(f"Probe error: {e}")
        return None

def optimize_image(input_path: Path, output_path: Path, max_size: int = 800, format: str = "JPEG"):
    """Resize and optimize an image using Pillow."""
    from PIL import Image
    # Normalize format for Pillow
    save_format = format.upper()
    if save_format == "JPG":
        save_format = "JPEG"
        
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if saving as JPEG
            if save_format == "JPEG" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            img.thumbnail((max_size, max_size))
            img.save(output_path, save_format, quality=85, optimize=True)
            return True
    except Exception as e:
        print(f"Image optimization error: {e}")
        return False

def extract_poster_image(input_video: Path, output_image: Path) -> bool:
    """Extract a representative frame from a video file as a poster image."""
    try:
        # Extract the frame at 1 second mark, or start if shorter
        ffmpegio.transcode(
            str(input_video), 
            str(output_image), 
            overwrite=True,
            ss=1.0, # Start at 1s
            vframes=1, # Single frame
            f="image2",
            vcodec="mjpeg"
        )
        return True
    except Exception as e:
        print(f"Video poster extraction error: {e}")
        # Try at 0s if 1s failed
        try:
            ffmpegio.transcode(
                str(input_video), 
                str(output_image), 
                overwrite=True,
                ss=0.0,
                vframes=1,
                f="image2",
                vcodec="mjpeg"
            )
            return True
        except:
            return False
def extract_mp3_metadata(file_path: Path) -> dict:
    """
    Extracts metadata from an MP3 file.

    Returns a dict with:
      - duration, bitrate: technical audio info
      - tags: standard ID3 fields (title, artist, album, year, genre, track, bpm, comment, lyrics)
      - prompt: ComfyUI TXXX:prompt JSON (if present)
      - workflow: ComfyUI TXXX:workflow JSON (if present)
    """
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TXXX, TIT2, TPE1, TALB, TDRC, TCON, TRCK, TBPM, COMM, USLT
    import json

    metadata = {}
    try:
        mp3 = MP3(file_path)
        if hasattr(mp3, "info") and mp3.info:
            metadata["duration"] = mp3.info.length
            metadata["bitrate"] = mp3.info.bitrate

        tags = ID3(file_path)
        standard: dict[str, Any] = {}

        def _text(frame):
            """Safely get the first text value from an ID3 frame."""
            try:
                return str(frame.text[0]).strip() if frame.text else None
            except Exception:
                return None

        # Standard ID3 text frames
        if "TIT2" in tags:
            standard["title"] = _text(tags["TIT2"])
        if "TPE1" in tags:
            standard["artist"] = _text(tags["TPE1"])
        if "TALB" in tags:
            standard["album"] = _text(tags["TALB"])
        if "TDRC" in tags:
            standard["year"] = _text(tags["TDRC"])
        if "TCON" in tags:
            standard["genre"] = _text(tags["TCON"])
        if "TRCK" in tags:
            standard["track"] = _text(tags["TRCK"])
        if "TBPM" in tags:
            raw_bpm = _text(tags["TBPM"])
            try:
                standard["bpm"] = float(raw_bpm) if raw_bpm else None
            except (ValueError, TypeError):
                standard["bpm"] = None

        # Comment frame (COMM — language-tagged, take first English or any)
        comm_frames = [v for k, v in tags.items() if k.startswith("COMM:")]
        if comm_frames:
            standard["comment"] = comm_frames[0].text[0].strip() if comm_frames[0].text else None

        # Unsynchronised lyrics (USLT)
        uslt_frames = [v for k, v in tags.items() if k.startswith("USLT:")]
        if uslt_frames:
            standard["lyrics"] = uslt_frames[0].text.strip() if uslt_frames[0].text else None

        # Filter out None values before storing
        standard = {k: v for k, v in standard.items() if v is not None}
        if standard:
            metadata["tags"] = standard

        # ComfyUI-specific TXXX frames (prompt / workflow JSON)
        for key, frame in tags.items():
            if key.startswith("TXXX:"):
                desc = frame.desc.lower()
                text_content = frame.text[0] if frame.text else ""
                if desc in ("prompt", "workflow"):
                    try:
                        metadata[desc] = json.loads(text_content)
                    except json.JSONDecodeError:
                        metadata[desc] = text_content

    except Exception as e:
        print(f"Error extracting MP3 metadata from {file_path.name}: {e}")

    return metadata
