from typing import Any, Dict, List
import tomlval
from .manifests import CatalogManifest, CreatorManifest, ModelManifest, SampleManifest

def is_string(value: Any) -> Any:
    return None if isinstance(value, str) else "expected string"

def is_int(value: Any) -> Any:
    return None if isinstance(value, int) else "expected integer"

def is_float(value: Any) -> Any:
    return None if isinstance(value, (int, float)) else "expected number"

def is_bool(value: Any) -> Any:
    return None if isinstance(value, bool) else "expected boolean"

def is_list(value: Any) -> Any:
    return None if isinstance(value, list) else "expected list"

def is_dict(value: Any) -> Any:
    return None if isinstance(value, dict) else "expected dictionary"

# Schema definitions using tomlval syntax
CATALOG_SCHEMA = tomlval.TOMLSchema({
    "title": is_string,
    "creator": is_string,
    "base_url": is_string,
    "cdn_url?": is_string,
    "language?": is_string,
    "synopsis?": is_string,
    "about?": is_string,
    "links?": is_list,
    "links?[].label": is_string,
    "links?[].url": is_string,
    "theme?": is_dict,
    "theme?.base": is_string,
    "theme?.accent_hue": is_float,
    "theme?.accent_chroma": is_float,
    "theme?.round_corners": is_bool,
    "site_assets?": is_list,
    "site_metadata?": is_string,
    "loracamp_signature?": is_bool,
    "preview_format?": is_string,
})

CREATOR_SCHEMA = tomlval.TOMLSchema({
    "name": is_string,
    "aliases?": is_list,
    "permalink?": is_string,
    "about?": is_string,
    "image?": is_string,
    "links?": is_dict,
})

MODEL_SCHEMA = tomlval.TOMLSchema({
    "title": is_string,
    "synopsis?": is_string,
    "about?": is_string,
    "trigger_word?": is_string,
    "creator?": is_string,
    "creators?": is_list,
    "release_date?": is_string,
    "permalink?": is_string,
    "preview?": is_string,
    "previews?": is_list,
    "unlisted?": is_bool,
    "base_model?": is_string,
    "version?": is_string,
    "sample_prompts?": is_list,
    "extras?": is_list,
    "preview_format?": is_string,
    "links?": is_list,
    "links?[].label": is_string,
    "links?[].url": is_string,
})

SAMPLE_SCHEMA = tomlval.TOMLSchema({
    "title": is_string,
    "creator?": is_string,
    "creators?": is_list,
    "sample_number?": is_int,
    "file?": is_string,
    "about?": is_string,
    "prompt?": is_string,
    "negative_prompt?": is_string,
    "seed?": is_int,
    "model?": is_string,
    "vae?": is_string,
    "clip?": is_string,
    "loras?": is_list,
    "loras?[].name": is_string,
    "loras?[].weight": is_float,
    "steps?": is_int,
    "cfg?": is_float,
    "sampler?": is_string,
    "scheduler?": is_string,
    "workflow?": is_string,
    "shift?": is_float,
    "lyrics?": is_string,
    "keyscale?": is_string,
    "bpm?": is_float,
    "timesignature?": is_string,
    "language?": is_string,
    "additional_seed?": is_int,
    "llm_cfg?": is_float,
    "llm_temp?": is_float,
    "llm_top_p?": is_float,
    "llm_top_k?": is_int,
    "llm_min_p?": is_float,
    "llm_rep_penalty?": is_float,
    "links?": is_list,
    "links?[].label": is_string,
    "links?[].url": is_string,
})

VALIDATORS = {
    "catalog.toml": tomlval.TOMLValidator(CATALOG_SCHEMA),
    "creator.toml": tomlval.TOMLValidator(CREATOR_SCHEMA),
    "model.toml": tomlval.TOMLValidator(MODEL_SCHEMA),
    "sample.toml": tomlval.TOMLValidator(SAMPLE_SCHEMA),
}

def validate_manifest(filename: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate TOML data against the appropriate schema.
    Returns a dictionary of errors if any, or empty dict if valid.
    """
    if filename not in VALIDATORS:
        return {}
    
    return VALIDATORS[filename].validate(data)
