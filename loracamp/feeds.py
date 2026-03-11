"""
LoraCamp Feed Generator
Produces Atom 1.0 and RSS 2.0 feeds for a model catalog.

Each feed entry includes:
  - Title and summary (synopsis or about)
  - Link to the model page
  - Link to the model's metadata.json for easy scraping
  - Preview image (as <enclosure> in RSS or <link rel="enclosure"> in Atom)
  - Author
  - Published date
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom


def _safe_text(s: Optional[str]) -> str:
    return (s or "").strip()


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_rfc822(date_str: Optional[str]) -> str:
    """Convert a YYYY-MM-DD string to RFC 822 for RSS pubDate."""
    if not date_str:
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y 00:00:00 +0000")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return dt.strftime("%a, %d %b %Y 00:00:00 +0000")
    except ValueError:
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y 00:00:00 +0000")


def _to_rfc3339(date_str: Optional[str]) -> str:
    """Convert a YYYY-MM-DD string to RFC 3339 for Atom updated."""
    if not date_str:
        return _now_rfc3339()
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return _now_rfc3339()


def generate_atom_feed(
    catalog,
    models: List[Dict[str, Any]],
    base_url: str,
    output_path: Path
):
    """
    Generate an Atom 1.0 feed.

    Args:
        catalog: CatalogManifest (or None)
        models: list of model dicts from engine.build()
        base_url: canonical site URL (from catalog.base_url or user-supplied)
        output_path: where to write the feed.atom file
    """
    base_url = base_url.rstrip("/")

    feed = Element("feed")
    feed.set("xmlns", "http://www.w3.org/2005/Atom")

    # Feed-level metadata
    _t(feed, "id", base_url + "/")
    _t(feed, "title", _safe_text(catalog.title if catalog else "LoraCamp Catalog"))
    _t(feed, "updated", _now_rfc3339())

    link_self = SubElement(feed, "link")
    link_self.set("rel", "self")
    link_self.set("href", base_url + "/feed.atom")

    link_alt = SubElement(feed, "link")
    link_alt.set("rel", "alternate")
    link_alt.set("href", base_url + "/")

    if catalog and catalog.synopsis:
        _t(feed, "subtitle", catalog.synopsis)

    # One entry per model
    for model in models:
        manifest = model.get("manifest")
        slug = model.get("slug", "")
        preview_url = model.get("preview_url")
        model_url = f"{base_url}/{slug}/"
        metadata_url = f"{base_url}/{slug}/metadata.json"

        entry = SubElement(feed, "entry")

        _t(entry, "id", model_url)
        _t(entry, "title", _safe_text(manifest.title if manifest else slug))
        _t(entry, "updated", _to_rfc3339(manifest.release_date if manifest else None))

        link_entry = SubElement(entry, "link")
        link_entry.set("rel", "alternate")
        link_entry.set("href", model_url)

        # Link to metadata.json — the scraping hook
        link_meta = SubElement(entry, "link")
        link_meta.set("rel", "related")
        link_meta.set("title", "Metadata JSON")
        link_meta.set("href", metadata_url)

        # Preview image as enclosure-style link
        if preview_url:
            link_img = SubElement(entry, "link")
            link_img.set("rel", "enclosure")
            link_img.set("type", "image/jpeg")
            link_img.set("href", f"{base_url}/{slug}/{preview_url}")

        # Summary from synopsis or trimmed about
        summary = ""
        if manifest:
            summary = manifest.synopsis or (manifest.about or "")[:256]
        if summary:
            _t(entry, "summary", summary)

        # Author
        author_name = None
        if manifest:
            author_name = manifest.creator
            if not author_name and manifest.creators:
                author_name = ", ".join(manifest.creators)
        if not author_name and catalog:
            author_name = getattr(catalog, "creator", None)

        if author_name:
            author_elem = SubElement(entry, "author")
            _t(author_elem, "name", author_name)

        # base_model and version as categories
        if manifest and manifest.base_model:
            cat_elem = SubElement(entry, "category")
            cat_elem.set("term", manifest.base_model)

    raw_xml = b'<?xml version="1.0" encoding="utf-8"?>\n' + tostring(feed, encoding="unicode").encode("utf-8")
    dom = minidom.parseString(raw_xml)
    pretty_xml = dom.toprettyxml(indent="  ")
    # minidom's toprettyxml might add its own <?xml ... ?> if we parse it, so let's just write pretty_xml.
    # Actually, parseString on an xml snippet will create a document, and toprettyxml will prepend the declaration.
    
    # Alternatively, just build it, stringify it, parse to dom, then toprettyxml.
    raw_xml_str = tostring(feed, encoding="unicode")
    dom = minidom.parseString(raw_xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", standalone=None)
    output_path.write_bytes(pretty_xml.encode("utf-8"))
    
    print(f"  Feed written: {output_path}")


def generate_rss_feed(
    catalog,
    models: List[Dict[str, Any]],
    base_url: str,
    output_path: Path
):
    """
    Generate an RSS 2.0 feed.

    Args:
        catalog: CatalogManifest (or None)
        models: list of model dicts from engine.build()
        base_url: canonical site URL
        output_path: where to write the feed.rss file
    """
    base_url = base_url.rstrip("/")

    rss = Element("rss")
    rss.set("version", "2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

    channel = SubElement(rss, "channel")
    _t(channel, "title", _safe_text(catalog.title if catalog else "LoraCamp Catalog"))
    _t(channel, "link", base_url + "/")
    _t(channel, "description", _safe_text(catalog.synopsis if catalog else ""))
    _t(channel, "lastBuildDate", _now_rfc3339())
    _t(channel, "language", catalog.language if catalog else "en")

    # Atom self link (recommended)
    atom_link = SubElement(channel, "atom:link")
    atom_link.set("href", base_url + "/feed.rss")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    for model in models:
        manifest = model.get("manifest")
        slug = model.get("slug", "")
        preview_url = model.get("preview_url")
        model_url = f"{base_url}/{slug}/"
        metadata_url = f"{base_url}/{slug}/metadata.json"

        item = SubElement(channel, "item")
        _t(item, "title", _safe_text(manifest.title if manifest else slug))
        _t(item, "link", model_url)
        _t(item, "guid", model_url)
        _t(item, "pubDate", _to_rfc822(manifest.release_date if manifest else None))

        # Description from synopsis or about
        desc = ""
        if manifest:
            desc = manifest.synopsis or (manifest.about or "")[:512]
            # Replace placeholder explicitly during final serialization to avoid escaping the HTML
            raw_html = f'{desc}\n\n<a href="{metadata_url}">📄 Metadata JSON</a>'
            desc_elem = SubElement(item, "description")
            desc_elem.text = f"__CDATA_DESC_{slug}__"
            # We will stash this to replace later
            model["_raw_desc"] = raw_html
        else:
            _t(item, "description", "")

        # Preview enclosure
        if preview_url:
            enc = SubElement(item, "enclosure")
            enc.set("url", f"{base_url}/{slug}/{preview_url}")
            enc.set("type", "image/jpeg")
            enc.set("length", "0")  # Length unknown at build time

        # Author
        author_name = None
        if manifest:
            author_name = manifest.creator
            if not author_name and manifest.creators:
                author_name = ", ".join(manifest.creators)
        if not author_name and catalog:
            author_name = getattr(catalog, "creator", None)
        if author_name:
            _t(item, "author", author_name)

        # Categories
        if manifest and manifest.base_model:
            _t(item, "category", manifest.base_model)

    raw_xml_str = tostring(rss, encoding="unicode")
    
    # Inject the CDATA description blocks
    for model in models:
        slug = model.get("slug", "")
        if "_raw_desc" in model:
            placeholder = f"__CDATA_DESC_{slug}__"
            cdata_block = f"<![CDATA[{model['_raw_desc']}]]>"
            raw_xml_str = raw_xml_str.replace(placeholder, cdata_block)
            
    dom = minidom.parseString(raw_xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", standalone=None)
    output_path.write_bytes(pretty_xml.encode("utf-8"))
    
    print(f"  Feed written: {output_path}")


def _t(parent: Element, tag: str, text: str) -> Element:
    """Helper: create a sub-element with text."""
    el = SubElement(parent, tag)
    el.text = text
    return el
