import logging
from time import time

from sqlalchemy import select, update

from src.config.resources import engine
from src.constants.job_state import JobState, RevisionState
from src.domain import scenario
from src.models.cases import cases
from src.models.revisions import revisions
from src.models.runs import runs
from src.services.audit import record
from src.utils.serial import content_digest

logger = logging.getLogger(__name__)


def service_one():
    with engine.begin() as db:
        statement = (
            select(
                runs,
                revisions.c.payload.label("revision_payload"),
                revisions.c.stats.label("revision_stats"),
            )
            .join(revisions, (revisions.c.case_id == runs.c.case_id)
                  & (revisions.c.version == runs.c.case_version))
            .where(runs.c.status == JobState.QUEUED, revisions.c.status == RevisionState.READY)
            .order_by(runs.c.id)
            .limit(1).with_for_update(skip_locked=True)
        )
        task = db.execute(statement).mappings().first()
        if task is None:
            return False
        try:
            result = scenario.run(task["revision_payload"], task["revision_stats"], task["parameter"], db)
            output = {"status": JobState.DONE, "result": result, "digest": content_digest(result)}
        except Exception as exc:
            # Let the failed database transaction roll back before persisting the error.
            raise JobFailure(task["id"], exc) from exc
        finish(db, task["id"], output)
        return True


def recalculate_one():
    """重算最早一个待算版本的统计，就绪后与样本一次性切换发布。"""
    with engine.begin() as db:
        statement = (
            select(revisions).where(revisions.c.status == RevisionState.COMPUTING)
            .order_by(revisions.c.id).limit(1).with_for_update(skip_locked=True)
        )
        draft = db.execute(statement).mappings().first()
        if draft is None:
            return False
        try:
            stats = scenario.compute_statistics(db, draft["payload"])
        except Exception as exc:
            # Let the failed database transaction roll back before persisting the error.
            raise RecalcFailure(draft["id"], exc) from exc
        db.execute(update(revisions).where(revisions.c.id == draft["id"]).values(
            status=RevisionState.READY, stats=stats, finished_at=int(time()),
        ))
        # 发布指针只向前推进：晚算完的旧稿无法盖过已更新的版本。
        db.execute(update(cases).where(
            cases.c.id == draft["case_id"], cases.c.current_version < draft["version"],
        ).values(current_version=draft["version"]))
        record(db, "recalc_ready", "worker", "revision", draft["id"])
        return True


class JobFailure(Exception):
    def __init__(self, run_id, cause):
        super().__init__(str(cause))
        self.run_id = run_id
        self.cause = cause


class RecalcFailure(Exception):
    def __init__(self, revision_id, cause):
        super().__init__(str(cause))
        self.revision_id = revision_id
        self.cause = cause


def fail(job_failure):
    with engine.begin() as db:
        run_id = job_failure.run_id
        statement = select(runs.c.status).where(runs.c.id == run_id).with_for_update()
        if db.scalar(statement) != JobState.QUEUED:
            return
        cause = job_failure.cause
        if isinstance(cause, (ValueError, TypeError, KeyError, OverflowError)):
            reason = str(cause) or "输入资料或批次参数不符合要求"
        else:
            reason = "处理失败，请检查 worker 日志"
        finish(db, run_id, {"status": JobState.FAILED, "failure": reason[:320]})


def fail_recalc(recalc_failure):
    """重算失败只标记该版本，发布指针不动，可用的旧版本继续接单。"""
    with engine.begin() as db:
        revision_id = recalc_failure.revision_id
        statement = select(revisions.c.status).where(revisions.c.id == revision_id).with_for_update()
        if db.scalar(statement) != RevisionState.COMPUTING:
            return
        cause = recalc_failure.cause
        if isinstance(cause, (ValueError, TypeError, KeyError, OverflowError)):
            reason = str(cause) or "更正的样本资料不符合统计要求"
        else:
            reason = "统计重算失败，请检查 worker 日志"
        db.execute(update(revisions).where(revisions.c.id == revision_id).values(
            status=RevisionState.FAILED, failure=reason[:320], finished_at=int(time()),
        ))
        record(db, "recalc_failed", "worker", "revision", revision_id)


def finish(db, run_id, output):
    db.execute(update(runs).where(runs.c.id == run_id).values(**output, finished_at=int(time())))
    record(db, str(output["status"]), "worker", "run", run_id)
