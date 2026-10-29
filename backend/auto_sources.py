"""Opt-in, read-only local evidence source for ISO Auto-Audit.

An administrator explicitly configures ISO_AUTO_EVIDENCE_DIR in .env. The
connector never walks the disk, never fetches external URLs, and only ingests
allowlisted PDF/DOCX files listed in manifest.json within that directory.

Evidence is saved in PostgreSQL with its SHA256 and human-provided control/type
mapping, using the existing campaign evidence store. This is source discovery,
NOT an automatic compliance approval or an internet crawler.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from backend import database, teamwork
from evidence_collectors.document_parser import extract_document_text

MAX_BYTES = 15 * 1024 * 1024
MAX_ITEMS = 300
ALLOWED_SUFFIXES = {".pdf", ".docx"}


class SourceConfigurationError(ValueError):
    """Only metadata about this error is exposed in Auto-Audit logs."""


def source_directory():
    configured = os.getenv("ISO_AUTO_EVIDENCE_DIR", "").strip().strip('"')
    if not configured:
        return None
    root = Path(configured).expanduser().resolve()
    if not root.is_dir():
        raise SourceConfigurationError("Configured evidence directory does not exist.")
    return root


def get_manifest():
    """Return (root, entries); no implicit discovery of arbitrary user files."""
    root = source_directory()
    if root is None:
        return None, []
    manifest = root / "manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise SourceConfigurationError("Evidence manifest.json is missing or invalid.")
    if manifest.stat().st_size > 512 * 1024:
        raise SourceConfigurationError("Evidence manifest.json is too large.")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SourceConfigurationError("Evidence manifest.json is invalid JSON.") from exc
    entries = data.get("items") if isinstance(data, dict) else None
    if not isinstance(entries, list) or len(entries) > MAX_ITEMS:
        raise SourceConfigurationError("Evidence manifest must have up to 300 items.")
    return root, entries


def validate_item(item, root):
    if not isinstance(item, dict):
        raise SourceConfigurationError("Evidence entry must be an object.")
    control_id = item.get("control_id")
    filename = item.get("file")
    evidence_type = item.get("evidence_type")
    if not all(isinstance(v, str) and v.strip() for v in (control_id, filename, evidence_type)):
        raise SourceConfigurationError("Evidence entry needs control_id, file, evidence_type.")
    if filename in (".", "..") or Path(filename).name != filename or "\\" in filename or "/" in filename:
        raise SourceConfigurationError("Evidence file must be a basename, not a directory path.")
    if Path(filename).suffix.lower() not in ALLOWED_SUFFIXES:
        raise SourceConfigurationError("Only PDF or DOCX source documents are allowed.")
    path = root / filename
    if path.is_symlink() or not path.is_file() or path.resolve().parent != root:
        raise SourceConfigurationError("Evidence file missing, linked, or outside allowed directory.")
    size = path.stat().st_size
    if not 0 < size <= MAX_BYTES:
        raise SourceConfigurationError("Evidence file must be between 1 byte and 15 MB.")
    return control_id, filename, evidence_type, path


def import_for_control(assessment_id, control_id, user_id, emit):
    """Process only this control's opted-in files; never infer compliance.

    emit(event_type, dict) persists non-sensitive events for the current run.
    Returns the number of new evidence records imported.
    """
    try:
        root, entries = get_manifest()
    except SourceConfigurationError as exc:
        emit("SOURCE_CONFIG_ERROR", {"reason": str(exc)})
        return 0
    if root is None:
        return 0

    control = database.get_control(control_id)
    if not control:
        emit("SOURCE_CONFIG_ERROR", {"reason": "Unknown control in database.", "control_id": control_id})
        return 0
    allowed_types = set(control.get("expected_evidence_types") or [])
    imported = 0
    for item in entries:
        if not isinstance(item, dict) or item.get("control_id") != control_id or item.get("enabled") is False:
            continue
        try:
            _, filename, evidence_type, path = validate_item(item, root)
            if evidence_type not in allowed_types:
                raise SourceConfigurationError("Evidence type is not allowed for this control.")
            content = path.read_bytes()
            # Detect an edit during reading; never ingest half-written documents.
            if not content or len(content) > MAX_BYTES:
                raise SourceConfigurationError("Source document has invalid size.")
            digest = hashlib.sha256(content).hexdigest()
            source = f"authorized-folder://{filename}"
            with database.get_connection() as con:
                with con.cursor() as cur:
                    cur.execute("""
                        SELECT sha256_hash FROM evidence
                        WHERE assessment_id=%s AND control_id=%s AND source=%s
                        ORDER BY created_at DESC LIMIT 1
                    """, (assessment_id, control_id, source))
                    prior = cur.fetchone()
            if prior is not None:
                if prior[0] == digest:
                    emit("SOURCE_ALREADY_INDEXED", {"file": filename, "sha256": digest})
                else:
                    emit("SOURCE_CHANGED_REVIEW", {"file": filename, "reason": "Source file changed; version the filename and update manifest to retain immutable history."})
                continue
            extracted = extract_document_text(filename, content)
            evidence_id = str(uuid4())
            teamwork.store_campaign_evidence(
                assessment_id, control_id, user_id, evidence_id,
                evidence_type, source, extracted, digest
            )
            # Preserve source provenance separately from a manual upload.
            with database.get_connection() as con:
                with con.cursor() as cur:
                    cur.execute("""
                        UPDATE evidence SET evidence_origin='AUTHORIZED_FOLDER'
                        WHERE evidence_id=%s AND assessment_id=%s
                    """, (evidence_id, assessment_id))
            imported += 1
            emit("SOURCE_INDEXED", {"file": filename, "sha256": digest, "evidence_type": evidence_type, "characters": len(extracted), "synthetic": False})
        except (OSError, ValueError) as exc:
            # Do not write raw document contents or local filesystem paths to logs.
            emit("SOURCE_ERROR", {"file": str(item.get("file", "?"))[:100], "category": type(exc).__name__, "message": "Could not validate or parse the authorized source document."})
    return imported
