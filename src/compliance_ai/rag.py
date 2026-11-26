from hashlib import sha256
from math import sqrt
from pathlib import Path
from re import findall
from uuid import UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Connection

from compliance_ai.admin import privileged_connection
from compliance_ai.catalog import research_catalog
from compliance_ai.db import Database, Document


class Citation(BaseModel):
    chunk_id: UUID
    control_id: str
    source_type: str
    source_ref: str
    content_sha256: str


def assessment_citations(
    connection: Connection, tenant: UUID, controls: set[str]
) -> dict[str, list[Citation]]:
    result: dict[str, list[Citation]] = {}
    for control in research_catalog().controls:
        if control.id not in controls:
            continue
        documents = Database.nearest_documents(
            connection, tenant, control.id, embed(control.title), 3
        )
        result[control.id] = [
            Citation(
                chunk_id=doc.id,
                control_id=control.id,
                source_type=doc.source_type,
                source_ref=doc.source_ref,
                content_sha256=sha256(doc.content.encode()).hexdigest(),
            )
            for doc in documents
            if doc.control_id == control.id
            and doc.source_type in ("research_rubric", "authorized_material")
        ]
    return result


class KnowledgeSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    control_id: str
    title: str = Field(min_length=1, max_length=120)
    reference: str = Field(min_length=1, max_length=240)
    edition: str = Field(min_length=1, max_length=60)
    rights_reference: str = Field(min_length=1, max_length=240)
    source_type: str = Field(pattern=r"^(research_rubric|authorized_material)$")


def embed(value: str) -> list[float]:
    vector = [0.0] * 384
    for token in findall(r"\w+", value.casefold()):
        digest = sha256(token.encode()).digest()
        index = int.from_bytes(digest[:4], "big") % len(vector)
        vector[index] += 1 if digest[4] & 1 else -1
    length = sqrt(sum(value * value for value in vector))
    return [value / length for value in vector] if length else vector


def ingest(tenant: UUID, path: Path, metadata: KnowledgeSource, *, permit: bool) -> int:
    if not permit:
        raise ValueError("Cần xác nhận quyền nhập tài liệu.")
    if metadata.control_id not in {item.id for item in research_catalog().controls}:
        raise ValueError("Mã tham chiếu không nằm trong danh mục.")
    if path.suffix.lower() != ".txt" or path.stat().st_size > 1_000_000:
        raise ValueError("Dùng tệp UTF-8 .txt tối đa 1 MB.")
    lines = path.read_text(encoding="utf-8-sig").split()
    if not lines:
        raise ValueError("Tệp nguồn trống.")
    reference = f"{metadata.title} / {metadata.edition} / {metadata.reference}"
    rows = []
    for index in range(0, len(lines), 180):
        content = " ".join(lines[index : index + 200])
        source_ref = f"{reference} / {metadata.rights_reference} / đoạn {index // 180 + 1}"
        fingerprint = sha256(content.encode()).hexdigest()
        identifier = uuid5(tenant, f"{metadata.control_id}/{source_ref}/{fingerprint}")
        rows.append(
            (
                tenant,
                identifier,
                metadata.control_id,
                metadata.source_type,
                source_ref,
                content,
                str(embed(content)),
            )
        )
    with privileged_connection() as connection, connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO app_data.document_chunks
                (company_id,id,control_id,source_type,source_ref,content,embedding)
            VALUES (%s,%s,%s,%s,%s,%s,CAST(%s AS public.vector))
            ON CONFLICT (company_id,id) DO NOTHING
        """,
            rows,
        )
    return len(rows)


def retrieve(
    db: Database,
    connection: Connection,
    tenant: UUID,
    control: str,
    query: str,
    limit: int = 3,
) -> list[Document]:
    return db.nearest_documents(connection, tenant, control, embed(query), limit)
