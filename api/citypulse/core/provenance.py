"""Traceability contract (blueprint p.6): every result carries scope, window, lineage,
quality flags and an explicit evidence-vs-inference label."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

EvidenceKind = Literal["observed", "computed", "inferred", "generated"]


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Lineage(BaseModel):
    source_ids: list[str]
    batch_ids: list[str] = Field(default_factory=list)
    observation_ids: list[str] = Field(default_factory=list)
    analysis_run_id: str | None = None
    metric_version: str | None = None


class Scope(BaseModel):
    area: str | None = None
    window_start: datetime | None = None
    window_end: datetime | None = None
    data_mode: Literal["synthetic", "real"]
    filters: dict[str, str] = Field(default_factory=dict)


class Traced[T](BaseModel):
    """Wrapper: no public-facing value without scope + lineage + caveats."""

    value: T
    kind: EvidenceKind
    scope: Scope
    lineage: Lineage
    quality_flags: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
