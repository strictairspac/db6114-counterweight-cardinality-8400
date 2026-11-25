from time import time

from fastapi import HTTPException
from sqlalchemy import insert, select

from src.constants.job_state import JobState, RevisionState
from src.domain.scenario import CONFIG
from src.models.cases import cases
from src.models.revisions import revisions
from src.models.runs import runs
from . import audit, cases as case_service


def query():
    return select(runs, cases.c.title.label("case_title")).join(cases, cases.c.id == runs.c.case_id)


def get(db, run_id):
    run = db.execute(query().where(runs.c.id == run_id)).mappings().first()
    if run is None:
        raise HTTPException(404, "执行批次不存在")
    return dict(run)


def list_entries(db):
    return [dict(row) for row in db.execute(query().order_by(runs.c.id.desc()).limit(100)).mappings()]


def enqueue(db, case_id, parameter, actor):
    if parameter > CONFIG["max_parameter"]:
        raise HTTPException(422, f"参数不能超过 {CONFIG['max_parameter']}")
    entry = case_service.get(db, case_id)
    published = db.scalar(select(revisions.c.status).where(
        revisions.c.case_id == case_id, revisions.c.version == entry["current_version"]))
    if published != RevisionState.READY:
        raise HTTPException(409, "校准统计尚未就绪，请稍后提交执行")
    change = db.execute(insert(runs).values(
        case_id=case_id, case_version=entry["current_version"], status=JobState.QUEUED,
        parameter=parameter, actor=actor, created_at=int(time()),
    ))
    run_id = change.inserted_primary_key[0]
    audit.record(db, "enqueue", actor, "run", run_id)
    return get(db, run_id)
