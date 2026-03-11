import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader
from .manifests import CatalogManifest, ModelManifest, SampleManifest, CreatorManifest, parse_catalog, parse_model, parse_sample, parse_creator, load_toml
from .metadata import generate_metadata_json, save_metadata
from .assets import copy_static_assets
from .cdn import resolve_file_url, should_go_to_cdn
from .validators import validate_manifest
from .feeds import generate_atom_feed, generate_rss_feed

class LoraCampEngine:
    def __init__(
        self,
        catalog_dir: Path,
        output_dir: Path,
        cdn_url: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ):
        self.catalog_dir = catalog_dir
        self.output_dir = output_dir
        self.cdn_url = cdn_url
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        self.creator_aliases: Dict[str, str] = {}
        
        # Set up explicit output folders for clarity
        self.site_dir = output_dir / "yoursite"
        self.asset_dir = output_dir / "yoursite"
        
        if cdn_url:
            self.asset_dir = output_dir / "yourcdn"
        
        # Initialize Jinja2
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    def build(self):
        print(f"Building LoraCamp site in {self.site_dir}...")
        
        # 1. Setup directories
        self.site_dir.mkdir(parents=True, exist_ok=True)
        if self.cdn_url:
            self.asset_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Copy static assets
        copy_static_assets(self.site_dir)
        
        # 3. Parse Global Catalog
        catalog_manifest_path = self.catalog_dir / "catalog.toml"
        catalog = None
        if catalog_manifest_path.exists():
            data = load_toml(catalog_manifest_path)
            errors = validate_manifest("catalog.toml", data)
            if errors:
                print(f"Validation errors in {catalog_manifest_path}:")
                for key, err in errors.items():
                    print(f"  - {key}: {err}")
                return # Abort build on catalog error
            catalog = parse_catalog(catalog_manifest_path)
            
        # 4. Walk directory for Models and Creators
        models = []
        creators = []
        for root, dirs, files in os.walk(self.catalog_dir):
            root_path = Path(root)

            # Compute the relative path from the catalog root for filtering.
            # The catalog root itself (rel == ".") is always visited regardless of filters
            # so that top-level catalog.toml is parsed and all subdirs are reachable.
            try:
                rel_path = root_path.relative_to(self.catalog_dir)
            except ValueError:
                rel_path = root_path
            rel_str = str(rel_path)
            is_catalog_root = rel_str == "."

            if not is_catalog_root:
                # Exclude: prune this subtree entirely and skip processing
                if any(p in rel_str for p in self.exclude_patterns):
                    dirs[:] = []  # prevent os.walk from descending further
                    continue

                # Include: if patterns are given, skip dirs that match none of them.
                # Also prune subdirs so we don't waste time descending into excluded trees.
                if self.include_patterns and not any(p in rel_str for p in self.include_patterns):
                    dirs[:] = []
                    continue

            print(f"Scanning: {root_path}")

            # Validate TOML filenames to catch user typos
            for f in files:
                if f.endswith(".toml"):
                    is_valid = f in ["catalog.toml", "model.toml", "creator.toml", "sample.toml"]
                    if not is_valid and not f.endswith(".sample.toml"):
                        print(f"  WARNING: Ignored invalid manifest name '{f}' in {root_path}. Valid names are catalog.toml, model.toml, creator.toml, sample.toml, or *.sample.toml")

            # Look for creator.toml
            if "creator.toml" in files:
                creator_data = self.process_creator(root_path)
                if creator_data:
                    creators.append(creator_data)

            # Look for .safetensors to identify a Model
            safetensors = [f for f in files if f.endswith(".safetensors")]
            if safetensors:
                print(f"  Found Model at: {root_path}")
                model_data = self.process_model(root_path, safetensors, catalog)
                if model_data:
                    models.append(model_data)
        
        # 5. Render Index
        self.render_index(catalog, models)

        # 6. Render Creator pages
        for creator_data in creators:
            self.render_creator_page(creator_data, catalog, models)

        # 7. Generate Feeds (Atom + RSS)
        base_url: str = getattr(catalog, "base_url", None) or ""
        if base_url:
            generate_atom_feed(catalog, models, base_url, self.site_dir / "feed.atom")
            generate_rss_feed(catalog, models, base_url, self.site_dir / "feed.rss")
        else:
            print("  Skipping feed generation: no base_url set in catalog.toml")
        
        print("Build complete!")

    def process_model(self, model_dir: Path, safetensor_files: List[str], catalog: Optional[CatalogManifest]):
        manifest_path = model_dir / "model.toml"
        if manifest_path.exists():
            data = load_toml(manifest_path)
            errors = validate_manifest("model.toml", data)
            if errors:
                print(f"Validation errors in {manifest_path}:")
                for key, err in errors.items():
                    print(f"  - {key}: {err}")
                return None
            model_manifest = parse_model(manifest_path)
            # Resolve creator via aliases if present
            if model_manifest.creator and model_manifest.creator in self.creator_aliases:
                model_manifest.creator = self.creator_aliases[model_manifest.creator]
        else:
            model_manifest = ModelManifest(title=model_dir.name)
            
        model_slug = model_manifest.permalink or model_dir.name
        model_site_dir = self.site_dir / model_slug
        model_site_dir.mkdir(parents=True, exist_ok=True)

        # 1. Generate Metadata JSON
        main_model_file = model_dir / safetensor_files[0]
        meta_json = generate_metadata_json(model_manifest, main_model_file)
        save_metadata(meta_json, model_site_dir / "metadata.json")

        # 2. Handle Preview Image / Video
        preview_url = None
        video_url = None
        
        # Determine target preview format
        target_ext = model_manifest.preview_format or (catalog.preview_format if catalog else "jpg")
        target_ext = target_ext.lstrip(".").lower()
        if target_ext == "jpeg":
            target_ext = "jpg"
            
        image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        video_extensions = {".mp4"}
        gif_extensions = {".gif"}
        
        all_exts = image_extensions | video_extensions | gif_extensions
        
        target_preview = None
        
        # 1. Check if model.toml explicitly declares a preview file
        if model_manifest.preview:
            declared_file = model_dir / model_manifest.preview
            if declared_file.exists() and declared_file.suffix.lower() in all_exts:
                target_preview = declared_file
            else:
                print(f"  WARNING: Declared preview '{model_manifest.preview}' not found or invalid type.")
                
        # 2. Look for expected filenames (preview.* or cover.*)
        if not target_preview:
            for f in sorted(model_dir.iterdir()):
                if f.stem.lower() in ("cover", "preview") and f.suffix.lower() in all_exts:
                    target_preview = f
                    break
                    
        # 3. Fallback: grab the first valid image/video we find
        if not target_preview:
            for f in sorted(model_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in all_exts:
                    target_preview = f
                    break
        
        from .media import optimize_image, extract_poster_image
        import shutil
        
        if target_preview:
            f = target_preview
            ext = f.suffix.lower()
            
            if ext in video_extensions:
                # Video preview - copy and extract poster
                video_dest = model_site_dir / f"preview{ext}"
                shutil.copy2(f, video_dest)
                video_url = video_dest.name
                
                # Extract poster as JPG (fallback/preview)
                poster_dest = model_site_dir / "preview.jpg"
                if extract_poster_image(f, poster_dest):
                    preview_url = "preview.jpg"
                
            elif ext in gif_extensions:
                # Animated GIF - copy as-is, also extract a static poster for index card
                gif_dest = model_site_dir / "preview.gif"
                shutil.copy2(f, gif_dest)
                video_url = gif_dest.name  # Reuse video_url for animated display
                
                # Extract static frame for catalog card using Pillow
                poster_dest = model_site_dir / "preview.jpg"
                try:
                    from PIL import Image
                    with Image.open(f) as img:
                        img.seek(0)  # First frame
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        img.thumbnail((800, 800))
                        img.save(poster_dest, "JPEG", quality=85, optimize=True)
                    preview_url = "preview.jpg"
                except Exception as e:
                    print(f"  GIF poster extraction error: {e}")
                
            elif ext in image_extensions:
                # Image preview
                preview_dest = model_site_dir / f"preview.{target_ext}"
                if optimize_image(f, preview_dest, format=target_ext):
                    preview_url = preview_dest.name
        else:
            print(f"  WARNING: No preview images found for {model_dir.name}. Using default placeholder.")
            # Use __file__ to resolve the package directory reliably
            pkg_dir = Path(__file__).parent
            placeholder_src = pkg_dir / "static" / "placeholder.jpg"
            if placeholder_src.exists():
                preview_dest = model_site_dir / "preview.jpg"
                shutil.copy2(placeholder_src, preview_dest)
                preview_url = "preview.jpg"
            else:
                print(f"  WARNING: Default placeholder missing from {placeholder_src}")
        
        # 3. Handle Asset Placement (Local vs CDN)
        model_filename = main_model_file.name
        
        cdn_url = self.cdn_url  # local var so Pyre2 can narrow Optional[str]
        if cdn_url:
            # Split mode
            model_asset_path = Path(model_slug) / model_filename
            dest_asset = self.asset_dir / model_asset_path
            dest_asset.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(main_model_file, dest_asset)
            assert self.cdn_url is not None
            model_url = f"{cdn_url.rstrip('/')}/{model_asset_path}"
        else:
            # Combined mode
            dest_path = model_site_dir / model_filename
            import shutil
            shutil.copy2(main_model_file, dest_path)
            model_url = model_filename

        # 3. Discover Samples (MP3, WAV, FLAC)
        samples = []
        audio_extensions = {".mp3", ".wav", ".flac", ".opus"}
        model_audio_files = []
        for f in model_dir.iterdir():
            if f.suffix.lower() in audio_extensions:
                sample_data = self.process_sample(f, model_slug, model_manifest)
                if sample_data:
                    samples.append(sample_data)
                    model_audio_files.append(f)

        # 4. Discover Extras (Automatic + Manifest)
        extras = []
        ignored_extensions = {".toml", ".safetensors", ".mp3", ".wav", ".flac", ".opus", ".zip"}
        ignored_names = {"preview", "cover"}
        for f in model_dir.iterdir():
            if f.is_file():
                if f.suffix.lower() in ignored_extensions:
                    continue
                if f.stem.lower() in ignored_names:
                    continue
                if f.name.startswith("."):
                    continue
                extras.append(f)
        
        # Add explicit extras from manifest if they exist and haven't been added
        for extra_name in model_manifest.extras:
            extra_file = model_dir / extra_name
            if extra_file.exists() and extra_file not in extras:
                extras.append(extra_file)

        # 5. Prepare Download Links (Replaced ZIP bundling)
        downloads = [
            {"label": f"Download Model ({model_filename})", "url": model_url, "is_zip": False, "primary": True},
            {"label": "Download Metadata (JSON)", "url": "metadata.json", "is_zip": False, "primary": False}
        ]
        
        if preview_url:
            downloads.append({"label": "Download Preview Art", "url": preview_url, "is_zip": False, "primary": False})
        if video_url:
            downloads.append({"label": "Download Preview Video", "url": video_url, "is_zip": False, "primary": False})

        for extra_f in extras:
            # Copy extras to output for individual download
            extra_dest = model_site_dir / extra_f.name
            import shutil
            shutil.copy2(extra_f, extra_dest)
            downloads.append({"label": f"Download Extra ({extra_f.name})", "url": extra_f.name, "is_zip": False, "primary": False})

        # 6. Render Detail Page
        self.render_model_page(model_manifest, samples, model_url, preview_url, video_url, downloads, model_site_dir)

        # Build list of creators for the index
        display_creator = model_manifest.creator
        if not display_creator and model_manifest.creators:
            display_creator = ", ".join(model_manifest.creators)
        elif not display_creator and catalog:
            display_creator = getattr(catalog, "creator", None)

        return {
            "manifest": model_manifest,
            "model_url": model_url,
            "preview_url": preview_url,
            "video_url": video_url,
            "display_creator": display_creator,
            "dir": model_dir,
            "slug": model_slug
        }

    def process_sample(self, audio_file: Path, model_slug: str, model_manifest: ModelManifest):
        from .media import transcode_audio, get_audio_duration, extract_mp3_metadata
        import json
        
        # Look for sample manifest (audio_file.stem + ".toml")
        manifest_path = audio_file.with_suffix(".toml")
        sample_manifest = None
        if manifest_path.exists():
            data = load_toml(manifest_path)
            errors = validate_manifest("sample.toml", data)
            if errors:
                print(f"Validation errors in {manifest_path}:")
                for key, err in errors.items():
                    print(f"  - {key}: {err}")
                return None
            sample_manifest = parse_sample(manifest_path)
        else:
            sample_manifest = SampleManifest()
            
        # Extract MP3 metadata before transcoding
        mp3_meta = extract_mp3_metadata(audio_file)
        
        # Populate manifest with extracted data if not explicitly set
        if mp3_meta:
            # 1. Standard ID3 tags — used as gentle fallbacks
            id3_tags = mp3_meta.get("tags", {})
            if not sample_manifest.title and id3_tags.get("title"):
                sample_manifest.title = id3_tags["title"]
            if not sample_manifest.creator and id3_tags.get("artist"):
                sample_manifest.creator = id3_tags["artist"]
            if not sample_manifest.bpm and id3_tags.get("bpm"):
                sample_manifest.bpm = float(id3_tags["bpm"])
            if not sample_manifest.lyrics and id3_tags.get("lyrics"):
                sample_manifest.lyrics = id3_tags["lyrics"]

            # 2. ComfyUI TXXX:prompt — extract fields from the workflow graph
            prompt_data = mp3_meta.get("prompt", {})
            if isinstance(prompt_data, dict):
                # Try to find standard comfyui Audio/Video nodes that might contain text
                # This is highly specific to the ComfyUI workflow format, but we'll extract
                # what we can. For robust support, the user can still use sample.toml.
                # A common pattern is finding a TextEncode node.
                for node_id, node in prompt_data.items():
                    if isinstance(node, dict) and "class_type" in node:
                        ctype = node["class_type"]
                        if "inputs" in node:
                            inputs = node["inputs"]
                            # Try to extract common fields if sample_manifest lacks them
                            if not sample_manifest.prompt and "text" in inputs and isinstance(inputs["text"], str):
                                sample_manifest.prompt = inputs["text"]
                            if not sample_manifest.prompt and "tags" in inputs and isinstance(inputs["tags"], str):
                                sample_manifest.prompt = inputs["tags"]
                            if not sample_manifest.lyrics and "lyrics" in inputs and isinstance(inputs["lyrics"], str):
                                sample_manifest.lyrics = inputs["lyrics"]
                            if not sample_manifest.seed and "seed" in inputs and isinstance(inputs["seed"], (int, float)):
                                sample_manifest.seed = int(inputs["seed"])
                            if not sample_manifest.bpm and "bpm" in inputs and isinstance(inputs["bpm"], (int, float)):
                                sample_manifest.bpm = float(inputs["bpm"])
            elif isinstance(prompt_data, str) and not sample_manifest.prompt:
                 sample_manifest.prompt = prompt_data
        
        # Output to SLUG/samples/filename.opus
        if self.cdn_url:
            sample_asset_path = Path(model_slug) / "samples"
            sample_asset_path = sample_asset_path / (audio_file.stem + ".opus")
            dest_asset = self.asset_dir / sample_asset_path
            dest_asset.parent.mkdir(parents=True, exist_ok=True)
            transcode_dest = dest_asset
        else:
            sample_rel_dir = Path("samples")
            dest_dir = self.site_dir / model_slug / sample_rel_dir
            dest_dir.mkdir(parents=True, exist_ok=True)
            transcode_dest = dest_dir / (audio_file.stem + ".opus")

        print(f"  Transcoding sample: {audio_file.name} -> {transcode_dest.name}")
        
        # Use manifest metadata if available
        sample_title = audio_file.stem
        sample_creator = model_manifest.creator
        if sample_manifest:
            if sample_manifest.title:
                sample_title = sample_manifest.title
            if sample_manifest.creator:
                sample_creator = sample_manifest.creator

        transcode_audio(audio_file, transcode_dest, title=sample_title, creator=sample_creator)
        
        # Save workflow JSON next to the transcoded audio if present
        workflow_url = None
        if "workflow" in mp3_meta:
            workflow_dest = transcode_dest.with_suffix(".workflow.json")
            with open(workflow_dest, "w", encoding="utf-8") as wf:
                json.dump(mp3_meta["workflow"], wf, indent=2)
            workflow_url = workflow_dest.name
            print(f"  Extracted workflow -> {workflow_dest.name}")
        
        duration = get_audio_duration(transcode_dest)
        
        cdn_url = self.cdn_url  # local var so Pyre2 can narrow Optional[str]
        if cdn_url:
            sample_url = f"{cdn_url.rstrip('/')}/{sample_asset_path}"
            if workflow_url:
                workflow_url = f"{cdn_url.rstrip('/')}/{sample_asset_path.parent}/{workflow_url}"
        else:
            sample_url = f"samples/{transcode_dest.name}"
            if workflow_url:
                workflow_url = f"samples/{Path(workflow_url).name}"
            
        return {
            "name": audio_file.stem,
            "url": sample_url,
            "duration": duration,
            "manifest": sample_manifest,
            "workflow_url": workflow_url
        }

    def render_model_page(self, model_manifest: ModelManifest, samples: List[Dict], model_url: str, preview_url: Optional[str], video_url: Optional[str], downloads: List[Dict], output_dir: Path, catalog: Optional[CatalogManifest] = None):
        try:
            template = self.env.get_template("model.html")
        except Exception:
            return

        base_url = getattr(catalog, "base_url", None) or ""
        model_slug = output_dir.name
        og_custom = model_manifest.opengraph or {}
        og_title = og_custom.get("title") or model_manifest.title
        og_description = og_custom.get("description") or model_manifest.synopsis or (model_manifest.about or "")[:256]
        
        if og_custom.get("image") and base_url:
            og_image = f"{base_url}/{model_slug}/{og_custom['image'].lstrip('/')}"
        else:
            og_image = f"{base_url}/{model_slug}/{preview_url}" if base_url and preview_url else ""
            
        content = template.render(
            model=model_manifest,
            samples=samples,
            model_url=model_url,
            preview_url=preview_url,
            video_url=video_url,
            downloads=downloads,
            catalog=catalog,
            base_url=base_url,
            og_title=og_title,
            og_description=og_description,
            og_image=og_image,
            og_url=f"{base_url}/{model_slug}/" if base_url else "",
            og_type="article",
        )
        with open(output_dir / "index.html", "w") as f:
            f.write(content)

    def render_index(self, catalog: Optional[CatalogManifest], models: List[Dict]):
        template = self.env.get_template("index.html")
        base_url = getattr(catalog, "base_url", None) or ""
        
        og_custom = getattr(catalog, "opengraph", {}) if catalog else {}
        og_title = og_custom.get("title") or getattr(catalog, "title", None)
        og_description = og_custom.get("description") or getattr(catalog, "synopsis", None)
        
        og_image = ""
        if og_custom.get("image") and base_url:
            og_image = f"{base_url}/{og_custom['image'].lstrip('/')}"
        elif models and models[0].get("preview_url"):
            first_slug = models[0].get("slug", "")
            og_image = f"{base_url}/{first_slug}/{models[0]['preview_url']}" if base_url else ""
            
        content = template.render(
            catalog=catalog,
            models=models,
            base_url=base_url,
            og_title=og_title,
            og_description=og_description,
            og_image=og_image,
            og_url=base_url + "/" if base_url else "",
            og_type="website",
        )
        with open(self.site_dir / "index.html", "w") as f:
            f.write(content)

    def render_creator_page(self, creator_data: Dict, catalog: Optional[CatalogManifest], all_models: List[Dict]):
        """Render a creator's own page with their profile and model list."""
        if not creator_data:
            return
        manifest = creator_data.get("manifest")
        if not manifest:
            return

        creator_slug = manifest.permalink or (manifest.name or manifest.title or "creator").lower().replace(" ", "-")
        creator_site_dir = self.site_dir / creator_slug
        creator_site_dir.mkdir(parents=True, exist_ok=True)

        # Find models by this creator
        creator_name = manifest.name or manifest.title
        creator_models = [
            m for m in all_models
            if creator_name and (
                (m.get("manifest") and m["manifest"].creator == creator_name)
                or (m.get("manifest") and creator_name in (m["manifest"].creators or []))
            )
        ]

        # Handle creator image if specified
        creator_image_url = None
        if manifest.image:
            import shutil
            src = creator_data["dir"] / manifest.image
            if src.exists():
                dest = creator_site_dir / manifest.image
                shutil.copy2(src, dest)
                creator_image_url = manifest.image

        base_url = getattr(catalog, "base_url", None) or ""
        
        # Check for external_page redirect
        external_url = None
        for link in manifest.links: # Assuming manifest.links is a list of dicts
            if isinstance(link, dict) and "external_page" in link:
                external_url = link["external_page"]
                break
        
        if external_url:
            # Generate a simple redirect page instead of the full creator page
            template = self.env.from_string('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url={{ url }}">
    <title>Redirecting...</title>
</head>
<body>
    <p>Redirecting to <a href="{{ url }}">{{ url }}</a></p>
</body>
</html>''')
            content = template.render(url=external_url)
        else:
            try:
                template = self.env.get_template("creator.html")
            except Exception:
                return
            og_custom = manifest.opengraph or {}
            og_title = og_custom.get("title") or creator_name
            og_description = og_custom.get("description") or getattr(manifest, "synopsis", None)
            
            if og_custom.get("image") and base_url:
                og_image = f"{base_url}/{creator_slug}/{og_custom['image'].lstrip('/')}"
            else:
                og_image = f"{base_url}/{creator_slug}/{creator_image_url}" if base_url and creator_image_url else ""
                
            content = template.render(
                catalog=catalog,
                creator=manifest,
                models=creator_models,
                creator_image_url=creator_image_url,
                base_url=base_url,
                og_title=og_title,
                og_description=og_description,
                og_image=og_image,
                og_url=f"{base_url}/{creator_slug}/" if base_url else "",
                og_type="profile",
            )
        with open(creator_site_dir / "index.html", "w") as f:
            f.write(content)
        print(f"  Creator page: /{creator_slug}/")

    def process_creator(self, creator_dir: Path):
        manifest_path = creator_dir / "creator.toml"
        data = load_toml(manifest_path)
        errors = validate_manifest("creator.toml", data)
        if errors:
            print(f"Validation errors in {manifest_path}:")
            for key, err in errors.items():
                print(f"  - {key}: {err}")
            return None
        
        creator_manifest = parse_creator(manifest_path)
        
        # Populate alias mapping
        canonical_name = creator_manifest.name or creator_dir.name
        if creator_manifest.aliases: # Ensure aliases exist before iterating
            for alias in creator_manifest.aliases:
                self.creator_aliases[alias] = canonical_name
            
        # The permalink defaults to the directory name if not specified
        return {
            "manifest": creator_manifest,
            "dir": creator_dir
        }
