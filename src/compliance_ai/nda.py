"""Versioned acknowledgements for the synthetic NDA workflow."""

from hashlib import sha256
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError


class NdaDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: int
    title: str
    content: str
    sha256: str
    source: Literal["research_simulation"] = "research_simulation"


def current_document() -> NdaDocument:
    content = (
        "Đây là cam kết dùng cho diễn tập, không phải chữ ký hoặc thỏa thuận pháp lý thật.\n"
        "Trong tình huống mô phỏng, tôi chỉ sử dụng thông tin được giao đúng mục đích; "
        "không chia sẻ thông tin hoặc tài khoản cho người không được phép; "
        "báo cáo sự cố qua kênh nội bộ và thực hiện nghĩa vụ bàn giao khi chuyển công việc."
    )
    return NdaDocument(
        version=1,
        title="Cam kết bảo mật — mô phỏng nghiên cứu",
        content=content,
        sha256=sha256(content.encode("utf-8")).hexdigest(),
    )


class NdaReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    document_hash: str
    submitted_by: UUID
    submitted_at: AwareDatetime
    evidence_id: UUID
    source: Literal["synthetic_employee_acknowledgement"] = "synthetic_employee_acknowledgement"


class NdaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    company_id: UUID
    target_id: UUID
    policy_version: int
    document: NdaDocument
    requested_at: AwareDatetime
    status: Literal["ASSIGNED", "ACKNOWLEDGED"] = "ASSIGNED"
    receipt: NdaReceipt | None = None


class NdaAcknowledgement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    document_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_revision: int = Field(ge=1, strict=True)
    acknowledged: bool = Field(strict=True)


def scoped_request(
    state: dict, tenant: UUID, target: UUID, policy_version: int
) -> NdaRequest | None:
    try:
        request = NdaRequest.model_validate(state.get("nda_request"))
    except ValidationError:
        return None
    if (
        request.company_id != tenant
        or request.target_id != target
        or request.policy_version != policy_version
        or request.document != current_document()
    ):
        return None
    return request


def acknowledged(request: NdaRequest | None) -> bool:
    if request is None or request.status != "ACKNOWLEDGED" or request.receipt is None:
        return False
    receipt = request.receipt
    return (
        receipt.request_id == request.id
        and receipt.document_hash == request.document.sha256
        and receipt.submitted_at >= request.requested_at
    )
