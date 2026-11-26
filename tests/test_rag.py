from pathlib import Path
from uuid import uuid4

import pytest

from compliance_ai.rag import KnowledgeSource, embed, ingest


def test_embedding_is_reproducible_and_checks_rights_before_io() -> None:
    vector = embed("chính sách bảo mật")
    assert len(vector) == 384
    assert sum(item * item for item in vector) == pytest.approx(1)
    assert embed("chính sách bảo mật") == vector
    metadata = KnowledgeSource(
        control_id="A.6.3",
        title="Tài liệu kiểm thử",
        reference="test",
        edition="1",
        source_type="research_rubric",
        rights_reference="test-only",
    )
    with pytest.raises(ValueError, match="quyền"):
        ingest(uuid4(), Path("unavailable.txt"), metadata, permit=False)
