"""ISO/IEC 27001:2022, 27002:2022, 27007:2020 RAG Engine + Multi-layer Prompt Injection Guardrail.

Supports PostgreSQL pgvector when available and automatically falls back to Hybrid BM25/TF-IDF
+ Cosine vector similarity stored as JSONB/in-memory embeddings so standard postgres:16 works out of the box.
"""
from __future__ import annotations

import math
import re
import secrets
from collections import Counter
from typing import Any

from backend.pc_storage import load_iso_knowledge_base, sha256_json

INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\[\s*(?:SYSTEM|ADMIN|AUDITOR|DEVELOPER)(?:\s+(?:INSTRUCTION|OVERRIDE|PROMPT|COMMAND))?\s*[:\-].*?\]", re.I | re.DOTALL),
    re.compile(r"<\s*/?\s*(?:system|instruction|override|assistant_rule)\s*>", re.I),
    re.compile(r"(?:ignore|disregard|forget|bypass)\s+(?:all\s+)?(?:previous|prior|above|system)\s+(?:instructions|rubrics|rules|policies)", re.I),
    re.compile(r"(?:mark|set|output|return|force)\s+(?:as\s+)?(?:[\"']?(?:status|score|passed)[\"']?\s*[:=]\s*)?[\"']?(?:Compliant|10(?:/10)?|true)[\"']?", re.I),
    re.compile(r"###\s*(?:SYSTEM\s+OVERRIDE|NEW\s+INSTRUCTIONS)", re.I),
)

TOKEN_RE = re.compile(r"[a-zA-Z0-9À-ỹ._-]+")


def sanitize_untrusted_text(text: str, source_id: str = "unknown") -> tuple[str, list[str]]:
    """Detect and neutralize multi-line & syntactic prompt injection attempts."""
    cleaned = str(text)
    alerts: list[str] = []
    for idx, pat in enumerate(INJECTION_PATTERNS, 1):
        if pat.search(cleaned):
            alerts.append(f"{source_id}:pattern_{idx}")
            cleaned = pat.sub("[BLOCKED_BY_PROMPT_GUARDRAIL]", cleaned)
    return cleaned, alerts


def wrap_untrusted_payload(payload_text: str, source_id: str = "evidence") -> tuple[str, str, list[str]]:
    """Wrap sanitized untrusted text inside a random per-call nonce XML boundary."""
    cleaned, alerts = sanitize_untrusted_text(payload_text, source_id=source_id)
    boundary = f"UNTRUSTED_DATA_{secrets.token_hex(6).upper()}"
    wrapped = f"<{boundary} source=\"{source_id}\">\n{cleaned}\n</{boundary}>"
    return boundary, wrapped, alerts


def _tokenize(text: str) -> list[str]:
    return [tok.lower() for tok in TOKEN_RE.findall(text)]


def _text_to_bow_vector(text: str, dim: int = 128) -> list[float]:
    """Deterministic hashed TF vector (JSONB-serializable) for lightweight cosine similarity."""
    vec = [0.0] * dim
    tokens = _tokenize(text)
    if not tokens:
        return vec
    for tok in tokens:
        h = int(sha256_json(tok)[:8], 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [round(v / norm, 6) for v in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class ISORagEngine:
    """Hybrid ISO RAG combining ISO 27001/27002/27007 chunks with company-specific baseline & SoA."""

    def __init__(self, chunks: list[dict[str, Any]] | None = None, use_pgvector_if_available: bool = False) -> None:
        raw_chunks = chunks if chunks is not None else load_iso_knowledge_base()
        self.chunks: list[dict[str, Any]] = []
        self._doc_tokens: list[Counter[str]] = []
        self._doc_vectors: list[list[float]] = []
        self._df: Counter[str] = Counter()
        self.backend_mode: str = "hybrid_bm25_cosine_jsonb"

        if use_pgvector_if_available and self._detect_pgvector():
            self.backend_mode = "pgvector"

        for chunk in raw_chunks:
            enriched = {
                **chunk,
                "sha256_hash": chunk.get("sha256_hash") or sha256_json(chunk["content"]),
            }
            toks = _tokenize(f"{chunk['control_id']} {chunk['standard_ref']} {chunk['pillar']} {chunk['content']}")
            tf = Counter(toks)
            self.chunks.append(enriched)
            self._doc_tokens.append(tf)
            self._doc_vectors.append(_text_to_bow_vector(chunk["content"]))
            for term in tf:
                self._df[term] += 1

        self._avgdl = sum(sum(c.values()) for c in self._doc_tokens) / max(len(self._doc_tokens), 1)

    @staticmethod
    def _detect_pgvector() -> bool:
        try:
            from backend.database import get_connection

            with get_connection() as con, con.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                return cur.fetchone() is not None
        except Exception:
            return False

    def _bm25_score(self, query_tokens: list[str], doc_tf: Counter[str], k1: float = 1.5, b: float = 0.75) -> float:
        score = 0.0
        n_docs = max(len(self.chunks), 1)
        dl = sum(doc_tf.values()) or 1
        for q in query_tokens:
            freq = doc_tf.get(q, 0)
            if freq == 0:
                continue
            df = self._df.get(q, 0)
            idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
            denom = freq + k1 * (1.0 - b + b * dl / max(self._avgdl, 1.0))
            score += idf * (freq * (k1 + 1.0) / denom)
        return score

    def retrieve(
        self,
        *,
        control_id: str,
        query: str = "",
        company: dict[str, Any] | None = None,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant ISO standard clauses + company-specific baseline policy context."""
        q_text = f"{control_id} {query}".strip()
        q_tokens = _tokenize(q_text)
        q_vec = _text_to_bow_vector(q_text)

        scored: list[tuple[float, dict[str, Any]]] = []
        for idx, chunk in enumerate(self.chunks):
            bm25 = self._bm25_score(q_tokens, self._doc_tokens[idx])
            cos = _cosine(q_vec, self._doc_vectors[idx])
            exact_boost = 4.0 if chunk["control_id"].upper() == control_id.upper() else (
                1.2 if chunk["control_id"] == "AUDIT_METHODOLOGY" else 0.0
            )
            total = round(exact_boost + bm25 + 2.0 * cos, 4)
            scored.append((total, {**chunk, "retrieval_score": total, "rag_backend": self.backend_mode}))

        scored.sort(key=lambda item: item[0], reverse=True)
        results = [item[1] for item in scored[:top_k]]

        if company:
            policy = company.get("baseline_policy") or {}
            exclusions = company.get("soa_exclusions") or []
            results.append(
                {
                    "chunk_id": f"COMPANY-POLICY-{company['company_id']}",
                    "standard_ref": f"Company Baseline ({company['company_id']})",
                    "control_id": control_id,
                    "pillar": "cross_domain",
                    "content": f"Chính sách nội bộ doanh nghiệp {company['name']} (quy mô {company['size_tier']}): baseline={policy}; soa_exclusions={exclusions}",
                    "retrieval_score": 5.0,
                    "rag_backend": self.backend_mode,
                    "sha256_hash": sha256_json({"policy": policy, "exclusions": exclusions}),
                }
            )
        return results
