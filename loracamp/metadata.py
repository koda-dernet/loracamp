import hashlib
import json
import struct
from pathlib import Path
from typing import Dict, Any, Optional
from .manifests import ModelManifest

def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in 4KB chunks
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_safetensors_metadata(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Read the JSON header from a .safetensors file.
    The first 8 bytes are an unsigned little-endian 64-bit integer representing the JSON header length N.
    The next N bytes are the JSON header string.
    """
    try:
        with open(file_path, "rb") as f:
            length_bytes = f.read(8)
            if len(length_bytes) < 8:
                return None
            (header_len,) = struct.unpack("<Q", length_bytes)
            if header_len <= 0 or header_len > 100 * 1024 * 1024: # Sanity check (max 100MB header)
                return None
                
            header_bytes = f.read(header_len)
            header_str = header_bytes.decode("utf-8")
            header_data = json.loads(header_str)
            
            # The general metadata in safetensors is usually under the "__metadata__" key
            return header_data.get("__metadata__", {})
    except Exception as e:
        print(f"Error extracting safetensors metadata from {file_path.name}: {e}")
        return None

def generate_metadata_json(
    model_manifest: ModelManifest, 
    safetensor_path: Optional[Path] = None
) -> str:
    """
    Assemble metadata JSON combining manifest data and technical data (SHA256, Safetensor __metadata__).
    """
    metadata = {
        "title": model_manifest.title,
        "about": model_manifest.about,
        "trigger_word": model_manifest.trigger_word,
        "creator": model_manifest.creator,
        "release_date": model_manifest.release_date,
        "release_creators": model_manifest.release_creators,
    }
    
    if safetensor_path and safetensor_path.exists():
        metadata["technical"] = {
            "sha256": calculate_sha256(safetensor_path),
            "filename": safetensor_path.name,
            "size_bytes": safetensor_path.stat().st_size
        }
        
        # Extract Safetensor specific __metadata__ header
        st_meta = extract_safetensors_metadata(safetensor_path)
        if st_meta:
            metadata["technical"]["__metadata__"] = st_meta
            
    return json.dumps(metadata, indent=4)

def save_metadata(json_content: str, output_path: Path):
    """Save the metadata JSON to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_content)
