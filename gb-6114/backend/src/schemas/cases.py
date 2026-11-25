from pydantic import BaseModel, Field, field_validator

from src.constants.job_state import RevisionState
from src.utils.serial import canonical_json


def check_payload_size(payload):
    if len(canonical_json(payload)) > 750_000:
        raise ValueError("样本数据不能超过 750 KB")
    return payload


class CaseInput(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=420)
    payload: dict

    @field_validator("title")
    @classmethod
    def check_title(cls, title):
        if len(title.strip()) < 2:
            raise ValueError("请输入至少两个字符的名称")
        return title.strip()

    @field_validator("payload")
    @classmethod
    def check_size(cls, payload):
        return check_payload_size(payload)


class CaseCorrection(BaseModel):
    payload: dict
    base_version: int = Field(strict=True, ge=1)

    @field_validator("payload")
    @classmethod
    def check_size(cls, payload):
        return check_payload_size(payload)


class CaseSummary(BaseModel):
    id: int
    code: str
    title: str
    description: str
    created_by: str
    current_version: int
    latest_version: int
    latest_status: RevisionState


class CaseDetail(CaseSummary):
    payload: dict
    latest_failure: str | None


class RevisionEntry(BaseModel):
    id: int
    case_id: int
    version: int
    status: RevisionState
    base_version: int | None
    actor: str
    failure: str | None
    created_at: int
    finished_at: int | None
