from redis.exceptions import RedisError
from src.config.resources import cache, engine
from src.services import cases, runs, reviews


def wake_worker():
    try:
        cache.lpush("workbench:wake", "1")
        cache.ltrim("workbench:wake", 0, 99)
    except RedisError:
        # The database holds the durable queue. The worker also polls it.
        pass


def new_case(data, user):
    with engine.begin() as db:
        return cases.create(db, data, user["username"])


def new_correction(case_id, data, user):
    with engine.begin() as db:
        revision = cases.correct(db, case_id, data, user["username"])
    wake_worker()
    return revision


def new_run(case_id, data, user):
    with engine.begin() as db:
        run = runs.enqueue(db, case_id, data.parameter, user["username"])
    wake_worker()
    return run


def new_review(run_id, data, user):
    with engine.begin() as db:
        return reviews.sign(db, run_id, data, user["username"])
