from time import time
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, insert, select

from src.constants.job_state import RevisionState
from src.domain import scenario
from src.models.cases import cases
from src.models.revisions import revisions
from .audit import record


def get(db, case_id):
    entry = db.execute(select(cases).where(cases.c.id == case_id)).mappings().first()
    if entry is None:
        raise HTTPException(404, "资料不存在")
    return dict(entry)


def list_entries(db):
    latest = (
        select(revisions.c.case_id, func.max(revisions.c.version).label("latest_version"))
        .group_by(revisions.c.case_id).subquery("latest_revisions")
    )
    statement = (
        select(cases, latest.c.latest_version, revisions.c.status.label("latest_status"))
        .join(latest, latest.c.case_id == cases.c.id)
        .join(revisions, (revisions.c.case_id == latest.c.case_id)
              & (revisions.c.version == latest.c.latest_version))
        .order_by(cases.c.id.desc()).limit(100)
    )
    return [dict(row) for row in db.execute(statement).mappings()]


def detail(db, case_id):
    entry = get(db, case_id)
    draft = db.execute(
        select(revisions).where(revisions.c.case_id == case_id)
        .order_by(revisions.c.version.desc()).limit(1)
    ).mappings().first()
    return {
        **entry,
        "latest_version": draft["version"],
        "latest_status": draft["status"],
        "latest_failure": draft["failure"],
        "payload": draft["payload"],
    }


def history(db, case_id):
    get(db, case_id)
    rows = db.execute(
        select(
            revisions.c.id, revisions.c.case_id, revisions.c.version, revisions.c.status,
            revisions.c.base_version, revisions.c.actor, revisions.c.failure,
            revisions.c.created_at, revisions.c.finished_at,
        ).where(revisions.c.case_id == case_id)
        .order_by(revisions.c.version.desc()).limit(50)
    ).mappings()
    return [dict(row) for row in rows]


def checked_payload(data):
    validator = getattr(scenario, "validate", None)
    if validator is not None:
        try:
            validator(data.payload)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
    return data.payload


def create(db, data, actor):
    payload = checked_payload(data)
    stats = scenario.compute_statistics(db, payload)
    now = int(time())
    change = db.execute(insert(cases).values(
        code=f"CASE-{uuid4().hex[:12].upper()}", title=data.title, description=data.description,
        created_by=actor, current_version=1,
    ))
    case_id = change.inserted_primary_key[0]
    db.execute(insert(revisions).values(
        case_id=case_id, version=1, payload=payload, stats=stats, status=RevisionState.READY,
        base_version=None, actor=actor, created_at=now, finished_at=now,
    ))
    record(db, "create_case", actor, "case", case_id)
    return detail(db, case_id)


def correct(db, case_id, data, actor):
    payload = checked_payload(data)
    entry = db.execute(select(cases).where(cases.c.id == case_id).with_for_update()).mappings().first()
    if entry is None:
        raise HTTPException(404, "资料不存在")
    latest = db.scalar(select(func.max(revisions.c.version)).where(revisions.c.case_id == case_id)) or 0
    if data.base_version != latest:
        raise HTTPException(409, f"资料已被他人更正到 v{latest}，请刷新获取最新版本后重新提交")
    version = latest + 1
    change = db.execute(insert(revisions).values(
        case_id=case_id, version=version, payload=payload, stats=None,
        status=RevisionState.COMPUTING, base_version=data.base_version, actor=actor, created_at=int(time()),
    ))
    record(db, "correct_case", actor, "case", case_id)
    return dict(db.execute(select(revisions).where(revisions.c.id == change.inserted_primary_key[0])).mappings().one())
